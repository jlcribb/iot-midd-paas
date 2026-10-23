"""GDSS-007C scenario evaluation and consequence evidence. Revision 0054."""

from alembic import op

revision = "0054"
down_revision = "0053"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r"""
    CREATE TABLE public.gdss_scenario_evaluation (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),project_id UUID NOT NULL,scenario_definition_id UUID NOT NULL,
      alternative_version_id UUID NOT NULL,problem_version_id UUID NOT NULL,model_version_id UUID NOT NULL,
      scenario_hash CHAR(64) NOT NULL,alternative_hash CHAR(64) NOT NULL,problem_hash CHAR(64) NOT NULL,model_hash CHAR(64) NOT NULL,
      decision_context_snapshot JSONB NOT NULL CHECK(jsonb_typeof(decision_context_snapshot)='object'),input_hash CHAR(64) NOT NULL,
      method_version TEXT NOT NULL,method_hash CHAR(64) NOT NULL CHECK(method_hash~'^[0-9a-f]{64}$'),
      resource_profile TEXT NOT NULL CHECK(resource_profile='GDSS_DECISION_LIMITS_V1'),execution_manifest JSONB NOT NULL CHECK(jsonb_typeof(execution_manifest)='object'),
      status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN('PENDING','RUNNING','COMPLETED','COMPLETED_WITH_LIMITATIONS','FAILED','INVALIDATED')),
      canonical_content TEXT NOT NULL,scenario_evaluation_hash CHAR(64) NOT NULL CHECK(scenario_evaluation_hash~'^[0-9a-f]{64}$'),
      idempotency_key TEXT NOT NULL,admitted_by TEXT NOT NULL,created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(scenario_definition_id,project_id) REFERENCES public.gdss_scenario_definition(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(alternative_version_id,project_id) REFERENCES public.gdss_decision_alternative_version(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(problem_version_id,project_id) REFERENCES public.gdss_decision_problem_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(project_id,scenario_evaluation_hash),UNIQUE(project_id,idempotency_key),UNIQUE(id,project_id));

    CREATE TABLE public.gdss_scenario_evaluation_attempt (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),project_id UUID NOT NULL,evaluation_id UUID NOT NULL,
      attempt_number INTEGER NOT NULL CHECK(attempt_number>0),status TEXT NOT NULL CHECK(status IN('RUNNING','COMPLETED','COMPLETED_WITH_LIMITATIONS','FAILED')),
      technical_metadata JSONB NOT NULL DEFAULT '{}' CHECK(jsonb_typeof(technical_metadata)='object'),diagnostics JSONB NOT NULL DEFAULT '[]' CHECK(jsonb_typeof(diagnostics)='array'),
      limitations TEXT[] NOT NULL DEFAULT '{}',missing_outputs TEXT[] NOT NULL DEFAULT '{}',idempotency_key TEXT NOT NULL,
      started_by TEXT NOT NULL,started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),ended_at TIMESTAMPTZ NULL,
      FOREIGN KEY(evaluation_id,project_id) REFERENCES public.gdss_scenario_evaluation(id,project_id) ON DELETE RESTRICT,
      UNIQUE(evaluation_id,attempt_number),UNIQUE(project_id,idempotency_key),UNIQUE(id,project_id));

    CREATE TABLE public.gdss_scenario_result_artifact (
      id UUID PRIMARY KEY,project_id UUID NOT NULL,evaluation_id UUID NOT NULL,attempt_id UUID NOT NULL,
      canonical_bytes BYTEA NOT NULL CHECK(octet_length(canonical_bytes)<=16777216),content_hash CHAR(64) NOT NULL CHECK(content_hash~'^[0-9a-f]{64}$'),
      media_type TEXT NOT NULL CHECK(media_type IN('application/json','application/vnd.midd.scenario-result+json')),
      canonical_metadata JSONB NOT NULL CHECK(jsonb_typeof(canonical_metadata)='object'),created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(evaluation_id,project_id) REFERENCES public.gdss_scenario_evaluation(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(attempt_id,project_id) REFERENCES public.gdss_scenario_evaluation_attempt(id,project_id) ON DELETE RESTRICT,
      UNIQUE(evaluation_id,attempt_id),UNIQUE(id,project_id));

    CREATE TABLE public.gdss_scenario_outcome (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),project_id UUID NOT NULL,evaluation_id UUID NOT NULL,attempt_id UUID NOT NULL,
      target_key TEXT NOT NULL,horizon_key TEXT NOT NULL,quantity_key TEXT NOT NULL,unit JSONB NOT NULL CHECK(jsonb_typeof(unit)='object'),
      value_kind TEXT NOT NULL CHECK(value_kind IN('NUMERIC','CATEGORICAL','UNKNOWN')),numeric_value DOUBLE PRECISION NULL CHECK(numeric_value IS NULL OR numeric_value NOT IN('NaN'::float8,'Infinity'::float8,'-Infinity'::float8)),
      categorical_value TEXT NULL,unknown_reason TEXT NULL,uncertainty_state TEXT NOT NULL CHECK(uncertainty_state IN('CHARACTERIZED','PARTIAL','UNKNOWN')),
      limitation_state TEXT NOT NULL CHECK(limitation_state IN('NONE','LIMITED','MISSING')),provenance TEXT NOT NULL CHECK(provenance='EXACT_METHOD_OUTPUT'),
      output_reference TEXT NOT NULL,output_hash CHAR(64) NOT NULL,canonical_content TEXT NOT NULL,outcome_hash CHAR(64) NOT NULL,created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(evaluation_id,project_id) REFERENCES public.gdss_scenario_evaluation(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(attempt_id,project_id) REFERENCES public.gdss_scenario_evaluation_attempt(id,project_id) ON DELETE RESTRICT,
      UNIQUE(evaluation_id,target_key,horizon_key,quantity_key),
      CHECK((value_kind='NUMERIC' AND numeric_value IS NOT NULL AND categorical_value IS NULL AND unknown_reason IS NULL) OR
            (value_kind='CATEGORICAL' AND numeric_value IS NULL AND categorical_value IS NOT NULL AND unknown_reason IS NULL) OR
            (value_kind='UNKNOWN' AND numeric_value IS NULL AND categorical_value IS NULL AND unknown_reason IS NOT NULL)));

    CREATE TABLE public.gdss_scenario_evaluation_event (
      id BIGSERIAL PRIMARY KEY,project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,evaluation_id UUID NOT NULL,
      sequence INTEGER NOT NULL CHECK(sequence>0),event_type TEXT NOT NULL CHECK(event_type IN('ADMIT','START','ATTEMPT_FAILED','COMPLETE','COMPLETE_WITH_LIMITATIONS','FAIL','INVALIDATE','ARTIFACT_RECONCILED','AI_AUTHORITY_DENIAL')),
      from_status TEXT NULL,to_status TEXT NULL,actor TEXT NOT NULL,actor_kind TEXT NOT NULL CHECK(actor_kind IN('HUMAN','AI')),
      reason TEXT NOT NULL,idempotency_key TEXT NOT NULL,event_hash CHAR(64) NOT NULL,metadata JSONB NOT NULL DEFAULT '{}',created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(evaluation_id,project_id) REFERENCES public.gdss_scenario_evaluation(id,project_id) ON DELETE RESTRICT,
      UNIQUE(evaluation_id,sequence),UNIQUE(project_id,idempotency_key),UNIQUE(project_id,event_hash));

    CREATE FUNCTION public.gdss007c_reject_mutation() RETURNS TRIGGER AS $$ BEGIN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE';END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss007c_reject_evidence_mutation() RETURNS TRIGGER AS $$ BEGIN RAISE EXCEPTION 'ARTIFACT_INTEGRITY_FAILURE';END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007c_guard_evaluation_insert() RETURNS TRIGGER AS $$
    DECLARE s RECORD;a RECORD;p RECORD;m RECORD;n INTEGER;
    BEGIN
      SELECT * INTO s FROM public.gdss_scenario_definition WHERE id=NEW.scenario_definition_id FOR UPDATE;
      SELECT * INTO a FROM public.gdss_decision_alternative_version WHERE id=NEW.alternative_version_id;
      SELECT * INTO p FROM public.gdss_decision_problem_version WHERE id=NEW.problem_version_id FOR UPDATE;
      SELECT v.*,i.project_id model_project INTO m FROM public.gdss_version v JOIN public.gdss_identity i ON i.id=v.identity_id WHERE v.id=NEW.model_version_id;
      IF s.id IS NULL OR a.id IS NULL OR p.id IS NULL OR m.id IS NULL OR s.project_id<>NEW.project_id OR a.project_id<>NEW.project_id OR p.project_id<>NEW.project_id OR m.model_project<>NEW.project_id OR s.alternative_version_id<>a.id OR s.problem_version_id<>p.id OR a.problem_version_id<>p.id THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE';END IF;
      IF s.status<>'ADMITTED' THEN RAISE EXCEPTION 'SCENARIO_NOT_ADMISSIBLE';END IF;
      IF s.scenario_hash<>NEW.scenario_hash OR a.alternative_hash<>NEW.alternative_hash OR p.decision_problem_hash<>NEW.problem_hash OR m.content_hash<>NEW.model_hash OR s.model_version_id<>NEW.model_version_id OR s.model_content_hash<>NEW.model_hash OR s.decision_context_snapshot<>NEW.decision_context_snapshot OR s.input_snapshot_hash<>NEW.input_hash OR s.method_version<>NEW.method_version OR s.resource_profile<>NEW.resource_profile THEN RAISE EXCEPTION 'DECISION_INPUT_NOT_CURRENT';END IF;
      IF NEW.status<>'PENDING' OR NEW.canonical_content~*'(recommended_option|best_alternative|utility_score|decision_score|causal_effect|observed_causal_result|mqtt|amqp|actuator|physical_endpoint|control_command|policy_activation|runtime_deployment)' THEN RAISE EXCEPTION 'SCENARIO_EVALUATION_INCOMPLETE';END IF;
      IF encode(digest(convert_to('midd:gdss:scenario-evaluation:v1','UTF8')||decode('00','hex')||convert_to(NEW.canonical_content,'UTF8'),'sha256'),'hex')<>NEW.scenario_evaluation_hash THEN RAISE EXCEPTION 'DECISION_INPUT_NOT_CURRENT';END IF;
      PERFORM pg_advisory_xact_lock(hashtextextended(NEW.problem_version_id::text,0));SELECT count(*) INTO n FROM public.gdss_scenario_evaluation WHERE problem_version_id=NEW.problem_version_id;
      IF n>=8192 THEN RAISE EXCEPTION 'RESOURCE_LIMIT_EXCEEDED resource=EVALUATIONS_PER_PROBLEM limit=8192 actual=%',n+1;END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007c_guard_evaluation_update() RETURNS TRIGGER AS $$
    DECLARE latest RECORD;required_count INTEGER;outcome_count INTEGER;artifact_count INTEGER;
    BEGIN
      IF TG_OP='DELETE' THEN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE';END IF;
      IF (to_jsonb(OLD)-'status'-'updated_at')<>(to_jsonb(NEW)-'status'-'updated_at') THEN RAISE EXCEPTION 'DECISION_PROBLEM_FROZEN';END IF;
      IF NOT((OLD.status='PENDING' AND NEW.status IN('RUNNING','INVALIDATED')) OR (OLD.status='RUNNING' AND NEW.status IN('COMPLETED','COMPLETED_WITH_LIMITATIONS','FAILED','INVALIDATED')) OR (OLD.status IN('COMPLETED','COMPLETED_WITH_LIMITATIONS') AND NEW.status='INVALIDATED')) THEN RAISE EXCEPTION 'INVALID_DECISION_LIFECYCLE';END IF;
      IF NEW.status IN('COMPLETED','COMPLETED_WITH_LIMITATIONS','FAILED') THEN
        SELECT * INTO latest FROM public.gdss_scenario_evaluation_attempt WHERE evaluation_id=NEW.id ORDER BY attempt_number DESC LIMIT 1;
        IF latest.id IS NULL OR latest.status<>NEW.status THEN RAISE EXCEPTION 'SCENARIO_EVALUATION_INCOMPLETE';END IF;
        IF NEW.status IN('COMPLETED','COMPLETED_WITH_LIMITATIONS') THEN SELECT count(*) INTO artifact_count FROM public.gdss_scenario_result_artifact WHERE evaluation_id=NEW.id AND attempt_id=latest.id;IF artifact_count<>1 THEN RAISE EXCEPTION 'ARTIFACT_INTEGRITY_FAILURE';END IF;END IF;
        IF NEW.status='COMPLETED' THEN SELECT jsonb_array_length(NEW.execution_manifest->'requiredOutputs') INTO required_count;SELECT count(*) INTO outcome_count FROM public.gdss_scenario_outcome WHERE evaluation_id=NEW.id AND attempt_id=latest.id;IF outcome_count<>required_count OR cardinality(latest.limitations)>0 OR cardinality(latest.missing_outputs)>0 THEN RAISE EXCEPTION 'SCENARIO_EVALUATION_INCOMPLETE';END IF;END IF;
        IF NEW.status='COMPLETED_WITH_LIMITATIONS' AND cardinality(latest.limitations)=0 AND cardinality(latest.missing_outputs)=0 THEN RAISE EXCEPTION 'SCENARIO_EVALUATION_INCOMPLETE';END IF;
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007c_guard_attempt_insert() RETURNS TRIGGER AS $$
    DECLARE e RECORD;expected INTEGER;previous RECORD;
    BEGIN SELECT * INTO e FROM public.gdss_scenario_evaluation WHERE id=NEW.evaluation_id FOR UPDATE;SELECT coalesce(max(attempt_number),0)+1 INTO expected FROM public.gdss_scenario_evaluation_attempt WHERE evaluation_id=NEW.evaluation_id;SELECT * INTO previous FROM public.gdss_scenario_evaluation_attempt WHERE evaluation_id=NEW.evaluation_id ORDER BY attempt_number DESC LIMIT 1;
      IF e.id IS NULL OR e.project_id<>NEW.project_id THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE';END IF;IF e.status<>'RUNNING' OR NEW.status<>'RUNNING' OR NEW.attempt_number<>expected THEN RAISE EXCEPTION 'INVALID_DECISION_LIFECYCLE';END IF;IF expected>1 AND previous.status<>'FAILED' THEN RAISE EXCEPTION 'INVALID_DECISION_LIFECYCLE';END IF;RETURN NEW;END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007c_guard_attempt_update() RETURNS TRIGGER AS $$
    BEGIN IF TG_OP='DELETE' THEN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE';END IF;IF (OLD.id,OLD.project_id,OLD.evaluation_id,OLD.attempt_number,OLD.technical_metadata,OLD.idempotency_key,OLD.started_by,OLD.started_at) IS DISTINCT FROM (NEW.id,NEW.project_id,NEW.evaluation_id,NEW.attempt_number,NEW.technical_metadata,NEW.idempotency_key,NEW.started_by,NEW.started_at) THEN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE';END IF;IF OLD.status<>'RUNNING' OR NEW.status NOT IN('COMPLETED','COMPLETED_WITH_LIMITATIONS','FAILED') OR NEW.ended_at IS NULL THEN RAISE EXCEPTION 'INVALID_DECISION_LIFECYCLE';END IF;RETURN NEW;END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007c_guard_artifact_insert() RETURNS TRIGGER AS $$
    DECLARE a RECORD;e RECORD;
    BEGIN SELECT * INTO a FROM public.gdss_scenario_evaluation_attempt WHERE id=NEW.attempt_id FOR UPDATE;SELECT * INTO e FROM public.gdss_scenario_evaluation WHERE id=NEW.evaluation_id;IF a.id IS NULL OR e.id IS NULL OR a.project_id<>NEW.project_id OR e.project_id<>NEW.project_id OR a.evaluation_id<>e.id OR a.status<>'RUNNING' THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE';END IF;IF encode(digest(NEW.canonical_bytes,'sha256'),'hex')<>NEW.content_hash THEN RAISE EXCEPTION 'ARTIFACT_INTEGRITY_FAILURE';END IF;RETURN NEW;END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007c_guard_outcome_insert() RETURNS TRIGGER AS $$
    DECLARE a RECORD;e RECORD;declared BOOLEAN;
    BEGIN SELECT * INTO a FROM public.gdss_scenario_evaluation_attempt WHERE id=NEW.attempt_id FOR UPDATE;SELECT * INTO e FROM public.gdss_scenario_evaluation WHERE id=NEW.evaluation_id;IF a.id IS NULL OR e.id IS NULL OR a.project_id<>NEW.project_id OR e.project_id<>NEW.project_id OR a.evaluation_id<>e.id OR a.status<>'RUNNING' OR e.status<>'RUNNING' THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE';END IF;SELECT EXISTS(SELECT 1 FROM jsonb_array_elements(e.execution_manifest->'requiredOutputs') r WHERE r->>'target'=NEW.target_key AND r->>'horizon'=NEW.horizon_key AND r->>'quantity'=NEW.quantity_key AND r->'unit'=NEW.unit) INTO declared;IF NOT declared THEN RAISE EXCEPTION 'SCENARIO_EVALUATION_INCOMPLETE';END IF;IF encode(digest(convert_to('midd:gdss:scenario-outcome:v1','UTF8')||decode('00','hex')||convert_to(NEW.canonical_content,'UTF8'),'sha256'),'hex')<>NEW.outcome_hash THEN RAISE EXCEPTION 'ARTIFACT_INTEGRITY_FAILURE';END IF;RETURN NEW;END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007c_guard_event() RETURNS TRIGGER AS $$ DECLARE expected INTEGER;BEGIN SELECT coalesce(max(sequence),0)+1 INTO expected FROM public.gdss_scenario_evaluation_event WHERE evaluation_id=NEW.evaluation_id;IF NEW.sequence<>expected THEN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE';END IF;IF NEW.actor_kind='AI' AND NEW.event_type IN('ADMIT','START','COMPLETE','COMPLETE_WITH_LIMITATIONS','FAIL','INVALIDATE','ARTIFACT_RECONCILED') THEN RAISE EXCEPTION 'AI_AUTHORITY_FORBIDDEN';END IF;RETURN NEW;END; $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_gdss007c_eval_insert BEFORE INSERT ON public.gdss_scenario_evaluation FOR EACH ROW EXECUTE FUNCTION public.gdss007c_guard_evaluation_insert();
    CREATE TRIGGER trg_gdss007c_eval_update BEFORE UPDATE OR DELETE ON public.gdss_scenario_evaluation FOR EACH ROW EXECUTE FUNCTION public.gdss007c_guard_evaluation_update();
    CREATE TRIGGER trg_gdss007c_attempt_insert BEFORE INSERT ON public.gdss_scenario_evaluation_attempt FOR EACH ROW EXECUTE FUNCTION public.gdss007c_guard_attempt_insert();
    CREATE TRIGGER trg_gdss007c_attempt_update BEFORE UPDATE OR DELETE ON public.gdss_scenario_evaluation_attempt FOR EACH ROW EXECUTE FUNCTION public.gdss007c_guard_attempt_update();
    CREATE TRIGGER trg_gdss007c_artifact_insert BEFORE INSERT ON public.gdss_scenario_result_artifact FOR EACH ROW EXECUTE FUNCTION public.gdss007c_guard_artifact_insert();
    CREATE TRIGGER trg_gdss007c_artifact_immutable BEFORE UPDATE OR DELETE ON public.gdss_scenario_result_artifact FOR EACH ROW EXECUTE FUNCTION public.gdss007c_reject_evidence_mutation();
    CREATE TRIGGER trg_gdss007c_outcome_insert BEFORE INSERT ON public.gdss_scenario_outcome FOR EACH ROW EXECUTE FUNCTION public.gdss007c_guard_outcome_insert();
    CREATE TRIGGER trg_gdss007c_outcome_immutable BEFORE UPDATE OR DELETE ON public.gdss_scenario_outcome FOR EACH ROW EXECUTE FUNCTION public.gdss007c_reject_evidence_mutation();
    CREATE TRIGGER trg_gdss007c_event_guard BEFORE INSERT ON public.gdss_scenario_evaluation_event FOR EACH ROW EXECUTE FUNCTION public.gdss007c_guard_event();
    CREATE TRIGGER trg_gdss007c_event_immutable BEFORE UPDATE OR DELETE ON public.gdss_scenario_evaluation_event FOR EACH ROW EXECUTE FUNCTION public.gdss007c_reject_mutation();
    CREATE INDEX gdss_scenario_eval_problem_status_idx ON public.gdss_scenario_evaluation(problem_version_id,status);
    CREATE INDEX gdss_scenario_outcome_eval_idx ON public.gdss_scenario_outcome(evaluation_id,attempt_id);
    """)


def downgrade():
    op.execute(r"""
    DROP TABLE IF EXISTS public.gdss_scenario_evaluation_event;DROP TABLE IF EXISTS public.gdss_scenario_outcome;DROP TABLE IF EXISTS public.gdss_scenario_result_artifact;DROP TABLE IF EXISTS public.gdss_scenario_evaluation_attempt;DROP TABLE IF EXISTS public.gdss_scenario_evaluation;
    DROP FUNCTION IF EXISTS public.gdss007c_guard_event();DROP FUNCTION IF EXISTS public.gdss007c_guard_outcome_insert();DROP FUNCTION IF EXISTS public.gdss007c_guard_artifact_insert();DROP FUNCTION IF EXISTS public.gdss007c_guard_attempt_update();DROP FUNCTION IF EXISTS public.gdss007c_guard_attempt_insert();DROP FUNCTION IF EXISTS public.gdss007c_guard_evaluation_update();DROP FUNCTION IF EXISTS public.gdss007c_guard_evaluation_insert();DROP FUNCTION IF EXISTS public.gdss007c_reject_evidence_mutation();DROP FUNCTION IF EXISTS public.gdss007c_reject_mutation();
    """)
