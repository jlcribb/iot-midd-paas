"""GDSS-007B governed alternative and scenario definition. Revision 0053."""

from alembic import op

revision = "0053"
down_revision = "0052"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r"""
    CREATE TABLE public.gdss_decision_alternative_identity (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL,
      problem_version_id UUID NOT NULL, canonical_key TEXT NOT NULL CHECK(length(btrim(canonical_key)) BETWEEN 1 AND 256),
      idempotency_key TEXT NOT NULL, created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(problem_version_id,project_id) REFERENCES public.gdss_decision_problem_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(project_id,problem_version_id,canonical_key), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_decision_alternative_version (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, alternative_identity_id UUID NOT NULL,
      problem_version_id UUID NOT NULL, version_number INTEGER NOT NULL CHECK(version_number>0), predecessor_version_id UUID NULL,
      status TEXT NOT NULL DEFAULT 'DRAFT' CHECK(status IN('DRAFT','REVIEW_REQUIRED','ADMITTED','REJECTED','SUPERSEDED')),
      semantic_version TEXT NOT NULL CHECK(semantic_version='GDSS_DECISION_ALTERNATIVE_V1'),
      problem_content_hash CHAR(64) NOT NULL, decision_context_snapshot JSONB NOT NULL CHECK(jsonb_typeof(decision_context_snapshot)='object'),
      what_changes TEXT[] NOT NULL CHECK(cardinality(what_changes)>0), what_remains_fixed TEXT[] NOT NULL CHECK(cardinality(what_remains_fixed)>0),
      parameter_deltas JSONB NOT NULL CHECK(jsonb_typeof(parameter_deltas)='array'), structural_assumptions JSONB NOT NULL CHECK(jsonb_typeof(structural_assumptions)='array'),
      decision_horizon JSONB NOT NULL CHECK(jsonb_typeof(decision_horizon)='object'), applicable_constraint_keys TEXT[] NOT NULL,
      scope JSONB NOT NULL CHECK(jsonb_typeof(scope)='object'), provenance TEXT NOT NULL CHECK(provenance IN('HUMAN_PROPOSED','DETERMINISTICALLY_GENERATED','AI_SUGGESTED','DERIVED_FROM_PRIOR_ALTERNATIVE')),
      resource_profile TEXT NOT NULL CHECK(resource_profile='GDSS_DECISION_LIMITS_V1'), canonical_content TEXT NOT NULL,
      alternative_hash CHAR(64) NOT NULL CHECK(alternative_hash~'^[0-9a-f]{64}$'), idempotency_key TEXT NOT NULL, authored_by TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(), updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(alternative_identity_id,project_id) REFERENCES public.gdss_decision_alternative_identity(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(problem_version_id,project_id) REFERENCES public.gdss_decision_problem_version(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(predecessor_version_id,project_id) REFERENCES public.gdss_decision_alternative_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(alternative_identity_id,version_number), UNIQUE(project_id,alternative_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_decision_variable (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, alternative_version_id UUID NOT NULL,
      semantic_variable_ref TEXT NOT NULL, mode TEXT NOT NULL CHECK(mode IN('FIXED','SET_TO','DELTA','RANGE','STRUCTURAL_CHANGE')),
      typed_value JSONB NOT NULL, unit JSONB NULL, baseline_value JSONB NULL, change_value JSONB NULL,
      scope JSONB NOT NULL CHECK(jsonb_typeof(scope)='object'), ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 255),
      FOREIGN KEY(alternative_version_id,project_id) REFERENCES public.gdss_decision_alternative_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(alternative_version_id,semantic_variable_ref), UNIQUE(alternative_version_id,ordinal));

    CREATE TABLE public.gdss_scenario_definition (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, problem_version_id UUID NOT NULL, alternative_version_id UUID NOT NULL,
      status TEXT NOT NULL DEFAULT 'DRAFT' CHECK(status IN('DRAFT','ADMITTED','REJECTED')), semantic_version TEXT NOT NULL CHECK(semantic_version='GDSS_DECISION_SCENARIO_V1'),
      problem_content_hash CHAR(64) NOT NULL, alternative_content_hash CHAR(64) NOT NULL, model_version_id UUID NOT NULL, model_content_hash CHAR(64) NOT NULL,
      decision_context_snapshot JSONB NOT NULL CHECK(jsonb_typeof(decision_context_snapshot)='object'), input_snapshot_hash CHAR(64) NOT NULL,
      scope JSONB NOT NULL CHECK(jsonb_typeof(scope)='object'), initial_conditions JSONB NOT NULL CHECK(jsonb_typeof(initial_conditions)='array'),
      parameter_set JSONB NOT NULL CHECK(jsonb_typeof(parameter_set)='array'), perturbations JSONB NOT NULL CHECK(jsonb_typeof(perturbations)='array'),
      uncertainty_condition JSONB NOT NULL CHECK(jsonb_typeof(uncertainty_condition)='object'),
      counterfactual_classification TEXT NOT NULL CHECK(counterfactual_classification IN('BASELINE_CONDITION','SIMULATED_COUNTERFACTUAL')),
      method_version TEXT NOT NULL, resource_profile TEXT NOT NULL CHECK(resource_profile='GDSS_DECISION_LIMITS_V1'), canonical_content TEXT NOT NULL,
      scenario_hash CHAR(64) NOT NULL CHECK(scenario_hash~'^[0-9a-f]{64}$'), idempotency_key TEXT NOT NULL, authored_by TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(), updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(problem_version_id,project_id) REFERENCES public.gdss_decision_problem_version(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(alternative_version_id,project_id) REFERENCES public.gdss_decision_alternative_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(project_id,scenario_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_scenario_assumption (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, scenario_id UUID NOT NULL,
      assumption_key TEXT NOT NULL, assumption_type TEXT NOT NULL, typed_value JSONB NOT NULL, reference TEXT NULL,
      scope JSONB NOT NULL, provenance TEXT NOT NULL CHECK(provenance IN('HUMAN_PROPOSED','DETERMINISTICALLY_GENERATED','AI_SUGGESTED','DERIVED_FROM_PRIOR_ALTERNATIVE')),
      explanation TEXT NULL, ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 255),
      FOREIGN KEY(scenario_id,project_id) REFERENCES public.gdss_scenario_definition(id,project_id) ON DELETE RESTRICT,
      UNIQUE(scenario_id,assumption_key), UNIQUE(scenario_id,ordinal));

    CREATE TABLE public.gdss_scenario_boundary_condition (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, scenario_id UUID NOT NULL,
      variable_ref TEXT NOT NULL, time_window JSONB NOT NULL, typed_value JSONB NOT NULL, unit JSONB NOT NULL,
      scope JSONB NOT NULL, method_semantics TEXT NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 255),
      FOREIGN KEY(scenario_id,project_id) REFERENCES public.gdss_scenario_definition(id,project_id) ON DELETE RESTRICT,
      UNIQUE(scenario_id,variable_ref,ordinal));

    CREATE TABLE public.gdss_decision_definition_event (
      id BIGSERIAL PRIMARY KEY, project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      entity_type TEXT NOT NULL CHECK(entity_type IN('DECISION_ALTERNATIVE','SCENARIO_DEFINITION')), entity_id UUID NOT NULL,
      sequence INTEGER NOT NULL CHECK(sequence>0), event_type TEXT NOT NULL CHECK(event_type IN('CREATE','UPDATE_DRAFT','SUBMIT_REVIEW','ADMIT','REJECT','SUPERSEDE','SOD_EXCEPTION','AI_AUTHORITY_DENIAL')),
      from_status TEXT NULL,to_status TEXT NULL,actor TEXT NOT NULL,actor_kind TEXT NOT NULL CHECK(actor_kind IN('HUMAN','AI')),
      reason TEXT NOT NULL,idempotency_key TEXT NOT NULL,event_hash CHAR(64) NOT NULL,metadata JSONB NOT NULL DEFAULT '{}',created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      UNIQUE(entity_type,entity_id,sequence),UNIQUE(project_id,idempotency_key),UNIQUE(project_id,event_hash));

    CREATE FUNCTION public.gdss007b_reject_mutation() RETURNS TRIGGER AS $$ BEGIN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE'; END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007b_guard_identity_insert() RETURNS TRIGGER AS $$
    DECLARE p RECORD; n INTEGER;
    BEGIN
      SELECT * INTO p FROM public.gdss_decision_problem_version WHERE id=NEW.problem_version_id FOR UPDATE;
      IF p.id IS NULL OR p.project_id<>NEW.project_id THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE'; END IF;
      IF p.status<>'SEALED' THEN RAISE EXCEPTION 'DECISION_PROBLEM_NOT_SEALED'; END IF;
      PERFORM pg_advisory_xact_lock(hashtextextended(NEW.problem_version_id::text,0));
      SELECT count(*) INTO n FROM public.gdss_decision_alternative_identity WHERE problem_version_id=NEW.problem_version_id;
      IF n>=64 THEN RAISE EXCEPTION 'RESOURCE_LIMIT_EXCEEDED resource=ALTERNATIVES_PER_PROBLEM limit=64 actual=%',n+1; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007b_guard_alternative_insert() RETURNS TRIGGER AS $$
    DECLARE i RECORD;p RECORD;pred RECORD;expected INTEGER;missing INTEGER;
    BEGIN
      SELECT * INTO i FROM public.gdss_decision_alternative_identity WHERE id=NEW.alternative_identity_id FOR UPDATE;
      SELECT * INTO p FROM public.gdss_decision_problem_version WHERE id=NEW.problem_version_id;
      SELECT coalesce(max(version_number),0)+1 INTO expected FROM public.gdss_decision_alternative_version WHERE alternative_identity_id=NEW.alternative_identity_id;
      IF i.id IS NULL OR p.id IS NULL OR i.project_id<>NEW.project_id OR p.project_id<>NEW.project_id OR i.problem_version_id<>NEW.problem_version_id THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE'; END IF;
      IF p.status<>'SEALED' THEN RAISE EXCEPTION 'DECISION_PROBLEM_NOT_SEALED'; END IF;
      IF NEW.canonical_content~*'(mqtt_topic|amqp_route|actuator_id|physical_endpoint|control_command|policy_activation|runtime_deployment)' THEN RAISE EXCEPTION 'OPERATIONAL_PAYLOAD_FORBIDDEN'; END IF;
      IF p.decision_problem_hash<>NEW.problem_content_hash OR p.context_snapshot<>NEW.decision_context_snapshot OR p.decision_horizon<>NEW.decision_horizon OR NOT(p.decision_scope @> NEW.scope) THEN RAISE EXCEPTION 'DECISION_INPUT_NOT_CURRENT'; END IF;
      IF NOT(NEW.provenance=ANY(p.allowed_alternative_provenance)) THEN RAISE EXCEPTION 'ALTERNATIVE_NOT_ADMISSIBLE'; END IF;
      SELECT count(*) INTO missing FROM unnest(NEW.applicable_constraint_keys) k WHERE NOT EXISTS(SELECT 1 FROM public.gdss_decision_constraint c WHERE c.problem_version_id=NEW.problem_version_id AND c.constraint_key=k);
      IF missing>0 THEN RAISE EXCEPTION 'DECISION_INPUT_NOT_CURRENT'; END IF;
      IF NEW.status<>'DRAFT' OR NEW.version_number<>expected THEN RAISE EXCEPTION 'INVALID_DECISION_LIFECYCLE'; END IF;
      IF NEW.predecessor_version_id IS NULL AND NEW.version_number<>1 THEN RAISE EXCEPTION 'DECISION_INPUT_NOT_CURRENT'; END IF;
      IF NEW.predecessor_version_id IS NOT NULL THEN SELECT * INTO pred FROM public.gdss_decision_alternative_version WHERE id=NEW.predecessor_version_id;IF pred.project_id<>NEW.project_id OR pred.alternative_identity_id<>NEW.alternative_identity_id OR pred.version_number<>NEW.version_number-1 OR pred.status<>'ADMITTED' THEN RAISE EXCEPTION 'DECISION_INPUT_NOT_CURRENT';END IF;END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007b_guard_alternative_update() RETURNS TRIGGER AS $$
    DECLARE p RECORD;missing INTEGER;
    BEGIN
      IF TG_OP='DELETE' THEN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE';END IF;
      IF (OLD.id,OLD.project_id,OLD.alternative_identity_id,OLD.problem_version_id,OLD.version_number,OLD.predecessor_version_id,OLD.created_at,OLD.authored_by) IS DISTINCT FROM (NEW.id,NEW.project_id,NEW.alternative_identity_id,NEW.problem_version_id,NEW.version_number,NEW.predecessor_version_id,NEW.created_at,NEW.authored_by) THEN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE';END IF;
      SELECT * INTO p FROM public.gdss_decision_problem_version WHERE id=NEW.problem_version_id;
      SELECT count(*) INTO missing FROM unnest(NEW.applicable_constraint_keys) k WHERE NOT EXISTS(SELECT 1 FROM public.gdss_decision_constraint c WHERE c.problem_version_id=NEW.problem_version_id AND c.constraint_key=k);
      IF p.id IS NULL OR p.project_id<>NEW.project_id THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE';END IF;
      IF p.status<>'SEALED' THEN RAISE EXCEPTION 'DECISION_PROBLEM_NOT_SEALED';END IF;
      IF p.decision_problem_hash<>NEW.problem_content_hash OR p.context_snapshot<>NEW.decision_context_snapshot OR p.decision_horizon<>NEW.decision_horizon OR NOT(p.decision_scope @> NEW.scope) OR NOT(NEW.provenance=ANY(p.allowed_alternative_provenance)) OR missing>0 THEN RAISE EXCEPTION 'DECISION_INPUT_NOT_CURRENT';END IF;
      IF NEW.canonical_content~*'(mqtt_topic|amqp_route|actuator_id|physical_endpoint|control_command|policy_activation|runtime_deployment)' THEN RAISE EXCEPTION 'OPERATIONAL_PAYLOAD_FORBIDDEN';END IF;
      IF OLD.status='DRAFT' AND NEW.status='DRAFT' THEN RETURN NEW;END IF;
      IF (to_jsonb(OLD)-'status'-'updated_at')<>(to_jsonb(NEW)-'status'-'updated_at') THEN RAISE EXCEPTION 'DECISION_PROBLEM_FROZEN';END IF;
      IF NOT((OLD.status='DRAFT' AND NEW.status IN('REVIEW_REQUIRED','REJECTED')) OR (OLD.status='REVIEW_REQUIRED' AND NEW.status IN('ADMITTED','REJECTED')) OR (OLD.status='ADMITTED' AND NEW.status='SUPERSEDED')) THEN RAISE EXCEPTION 'INVALID_DECISION_LIFECYCLE';END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007b_guard_alt_child() RETURNS TRIGGER AS $$
    DECLARE a RECORD;
    BEGIN SELECT * INTO a FROM public.gdss_decision_alternative_version WHERE id=coalesce(NEW.alternative_version_id,OLD.alternative_version_id);IF a.status<>'DRAFT' THEN RAISE EXCEPTION 'DECISION_PROBLEM_FROZEN';END IF;IF TG_OP<>'DELETE' AND (a.project_id<>NEW.project_id OR NOT(a.scope @> NEW.scope)) THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE';END IF;RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007b_guard_scenario_insert() RETURNS TRIGGER AS $$
    DECLARE p RECORD;a RECORD;m RECORD;per_alt INTEGER;global_count INTEGER;
    BEGIN
      SELECT * INTO p FROM public.gdss_decision_problem_version WHERE id=NEW.problem_version_id FOR UPDATE;
      SELECT * INTO a FROM public.gdss_decision_alternative_version WHERE id=NEW.alternative_version_id FOR UPDATE;
      SELECT v.*,i.project_id model_project INTO m FROM public.gdss_version v JOIN public.gdss_identity i ON i.id=v.identity_id WHERE v.id=NEW.model_version_id;
      IF p.id IS NULL OR a.id IS NULL OR m.id IS NULL OR p.project_id<>NEW.project_id OR a.project_id<>NEW.project_id OR m.model_project<>NEW.project_id OR a.problem_version_id<>p.id THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE';END IF;
      IF p.status<>'SEALED' OR a.status<>'ADMITTED' THEN RAISE EXCEPTION 'SCENARIO_NOT_ADMISSIBLE';END IF;
      IF NEW.canonical_content~*'(mqtt_topic|amqp_route|actuator_id|physical_endpoint|control_command|policy_activation|runtime_deployment)' OR NEW.canonical_content~*'(CAUSAL_EFFECT|OBSERVED_CAUSAL_RESULT)' THEN RAISE EXCEPTION 'SCENARIO_NOT_ADMISSIBLE';END IF;
      IF p.decision_problem_hash<>NEW.problem_content_hash OR a.alternative_hash<>NEW.alternative_content_hash OR m.content_hash<>NEW.model_content_hash OR p.context_snapshot<>NEW.decision_context_snapshot OR NOT(a.scope @> NEW.scope) THEN RAISE EXCEPTION 'DECISION_INPUT_NOT_CURRENT';END IF;
      IF NOT(NEW.method_version=ANY(p.allowed_scenario_methods)) OR NOT EXISTS(SELECT 1 FROM public.gdss_decision_problem_model_ref r WHERE r.problem_version_id=p.id AND r.model_version_id=NEW.model_version_id AND r.model_content_hash=NEW.model_content_hash) THEN RAISE EXCEPTION 'SCENARIO_NOT_ADMISSIBLE';END IF;
      PERFORM pg_advisory_xact_lock(hashtextextended(NEW.alternative_version_id::text,0));
      SELECT count(*) INTO per_alt FROM public.gdss_scenario_definition WHERE alternative_version_id=NEW.alternative_version_id;
      SELECT count(*) INTO global_count FROM public.gdss_scenario_definition WHERE problem_version_id=NEW.problem_version_id;
      IF per_alt>=128 OR global_count>=8192 THEN RAISE EXCEPTION 'RESOURCE_LIMIT_EXCEEDED resource=SCENARIOS limit=% actual=%',CASE WHEN per_alt>=128 THEN 128 ELSE 8192 END,CASE WHEN per_alt>=128 THEN per_alt+1 ELSE global_count+1 END;END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007b_guard_scenario_update() RETURNS TRIGGER AS $$
    DECLARE p RECORD;a RECORD;m RECORD;
    BEGIN
      IF TG_OP='DELETE' THEN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE';END IF;
      IF (OLD.id,OLD.project_id,OLD.problem_version_id,OLD.alternative_version_id,OLD.created_at,OLD.authored_by) IS DISTINCT FROM (NEW.id,NEW.project_id,NEW.problem_version_id,NEW.alternative_version_id,NEW.created_at,NEW.authored_by) THEN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE';END IF;
      IF OLD.status<>'DRAFT' THEN RAISE EXCEPTION 'DECISION_PROBLEM_FROZEN';END IF;
      SELECT * INTO p FROM public.gdss_decision_problem_version WHERE id=NEW.problem_version_id;SELECT * INTO a FROM public.gdss_decision_alternative_version WHERE id=NEW.alternative_version_id;SELECT v.*,i.project_id model_project INTO m FROM public.gdss_version v JOIN public.gdss_identity i ON i.id=v.identity_id WHERE v.id=NEW.model_version_id;
      IF p.id IS NULL OR a.id IS NULL OR m.id IS NULL OR p.project_id<>NEW.project_id OR a.project_id<>NEW.project_id OR m.model_project<>NEW.project_id OR a.problem_version_id<>p.id THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE';END IF;
      IF p.status<>'SEALED' OR a.status<>'ADMITTED' OR p.decision_problem_hash<>NEW.problem_content_hash OR a.alternative_hash<>NEW.alternative_content_hash OR m.content_hash<>NEW.model_content_hash OR p.context_snapshot<>NEW.decision_context_snapshot OR NOT(a.scope @> NEW.scope) OR NOT(NEW.method_version=ANY(p.allowed_scenario_methods)) OR NOT EXISTS(SELECT 1 FROM public.gdss_decision_problem_model_ref r WHERE r.problem_version_id=p.id AND r.model_version_id=NEW.model_version_id AND r.model_content_hash=NEW.model_content_hash) THEN RAISE EXCEPTION 'SCENARIO_NOT_ADMISSIBLE';END IF;
      IF NEW.canonical_content~*'(mqtt_topic|amqp_route|actuator_id|physical_endpoint|control_command|policy_activation|runtime_deployment|CAUSAL_EFFECT|OBSERVED_CAUSAL_RESULT)' THEN RAISE EXCEPTION 'SCENARIO_NOT_ADMISSIBLE';END IF;
      IF OLD.status=NEW.status THEN RETURN NEW;END IF;
      IF (to_jsonb(OLD)-'status'-'updated_at')<>(to_jsonb(NEW)-'status'-'updated_at') OR NOT(OLD.status='DRAFT' AND NEW.status IN('ADMITTED','REJECTED')) THEN RAISE EXCEPTION 'INVALID_DECISION_LIFECYCLE';END IF;RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007b_guard_scenario_child() RETURNS TRIGGER AS $$
    DECLARE s RECORD;
    BEGIN SELECT * INTO s FROM public.gdss_scenario_definition WHERE id=coalesce(NEW.scenario_id,OLD.scenario_id);IF s.status<>'DRAFT' THEN RAISE EXCEPTION 'DECISION_PROBLEM_FROZEN';END IF;IF TG_OP<>'DELETE' AND (s.project_id<>NEW.project_id OR NOT(s.scope @> NEW.scope)) THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE';END IF;RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007b_guard_event() RETURNS TRIGGER AS $$ DECLARE expected INTEGER;author_value TEXT;BEGIN SELECT coalesce(max(sequence),0)+1 INTO expected FROM public.gdss_decision_definition_event WHERE entity_type=NEW.entity_type AND entity_id=NEW.entity_id;IF NEW.sequence<>expected THEN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE';END IF;IF NEW.actor_kind='AI' AND NEW.event_type IN('SUBMIT_REVIEW','ADMIT','SOD_EXCEPTION') THEN RAISE EXCEPTION 'AI_AUTHORITY_FORBIDDEN';END IF;IF NEW.entity_type='DECISION_ALTERNATIVE' THEN SELECT authored_by INTO author_value FROM public.gdss_decision_alternative_version WHERE id=NEW.entity_id;ELSE SELECT authored_by INTO author_value FROM public.gdss_scenario_definition WHERE id=NEW.entity_id;END IF;IF NEW.event_type='ADMIT' AND author_value=NEW.actor AND coalesce((NEW.metadata->>'sod_exception')::boolean,false)=false THEN RAISE EXCEPTION 'SOD_VIOLATION';END IF;RETURN NEW;END; $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_gdss007b_identity_insert BEFORE INSERT ON public.gdss_decision_alternative_identity FOR EACH ROW EXECUTE FUNCTION public.gdss007b_guard_identity_insert();
    CREATE TRIGGER trg_gdss007b_identity_immutable BEFORE UPDATE OR DELETE ON public.gdss_decision_alternative_identity FOR EACH ROW EXECUTE FUNCTION public.gdss007b_reject_mutation();
    CREATE TRIGGER trg_gdss007b_alt_insert BEFORE INSERT ON public.gdss_decision_alternative_version FOR EACH ROW EXECUTE FUNCTION public.gdss007b_guard_alternative_insert();
    CREATE TRIGGER trg_gdss007b_alt_update BEFORE UPDATE OR DELETE ON public.gdss_decision_alternative_version FOR EACH ROW EXECUTE FUNCTION public.gdss007b_guard_alternative_update();
    CREATE TRIGGER trg_gdss007b_variable_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_decision_variable FOR EACH ROW EXECUTE FUNCTION public.gdss007b_guard_alt_child();
    CREATE TRIGGER trg_gdss007b_scenario_insert BEFORE INSERT ON public.gdss_scenario_definition FOR EACH ROW EXECUTE FUNCTION public.gdss007b_guard_scenario_insert();
    CREATE TRIGGER trg_gdss007b_scenario_update BEFORE UPDATE OR DELETE ON public.gdss_scenario_definition FOR EACH ROW EXECUTE FUNCTION public.gdss007b_guard_scenario_update();
    CREATE TRIGGER trg_gdss007b_assumption_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_scenario_assumption FOR EACH ROW EXECUTE FUNCTION public.gdss007b_guard_scenario_child();
    CREATE TRIGGER trg_gdss007b_boundary_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_scenario_boundary_condition FOR EACH ROW EXECUTE FUNCTION public.gdss007b_guard_scenario_child();
    CREATE TRIGGER trg_gdss007b_event_guard BEFORE INSERT ON public.gdss_decision_definition_event FOR EACH ROW EXECUTE FUNCTION public.gdss007b_guard_event();
    CREATE TRIGGER trg_gdss007b_event_immutable BEFORE UPDATE OR DELETE ON public.gdss_decision_definition_event FOR EACH ROW EXECUTE FUNCTION public.gdss007b_reject_mutation();
    CREATE INDEX gdss_alt_problem_status_idx ON public.gdss_decision_alternative_version(problem_version_id,status);
    CREATE INDEX gdss_scenario_alt_status_idx ON public.gdss_scenario_definition(alternative_version_id,status);
    """)


def downgrade():
    op.execute(r"""
    DROP TABLE IF EXISTS public.gdss_decision_definition_event;
    DROP TABLE IF EXISTS public.gdss_scenario_boundary_condition;
    DROP TABLE IF EXISTS public.gdss_scenario_assumption;
    DROP TABLE IF EXISTS public.gdss_scenario_definition;
    DROP TABLE IF EXISTS public.gdss_decision_variable;
    DROP TABLE IF EXISTS public.gdss_decision_alternative_version;
    DROP TABLE IF EXISTS public.gdss_decision_alternative_identity;
    DROP FUNCTION IF EXISTS public.gdss007b_guard_event();DROP FUNCTION IF EXISTS public.gdss007b_guard_scenario_child();
    DROP FUNCTION IF EXISTS public.gdss007b_guard_scenario_update();DROP FUNCTION IF EXISTS public.gdss007b_guard_scenario_insert();
    DROP FUNCTION IF EXISTS public.gdss007b_guard_alt_child();DROP FUNCTION IF EXISTS public.gdss007b_guard_alternative_update();
    DROP FUNCTION IF EXISTS public.gdss007b_guard_alternative_insert();DROP FUNCTION IF EXISTS public.gdss007b_guard_identity_insert();DROP FUNCTION IF EXISTS public.gdss007b_reject_mutation();
    """)
