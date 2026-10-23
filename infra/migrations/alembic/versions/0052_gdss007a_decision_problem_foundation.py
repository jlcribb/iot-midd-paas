"""GDSS-007A governed decision problem foundation. Revision 0052."""

from alembic import op

revision = "0052"
down_revision = "0051"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r"""
    CREATE TABLE public.gdss_decision_preference_identity (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      canonical_key TEXT NOT NULL CHECK(length(btrim(canonical_key)) BETWEEN 1 AND 256),
      idempotency_key TEXT NOT NULL, created_by TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      UNIQUE(project_id,canonical_key), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_decision_preference_version (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL,
      preference_identity_id UUID NOT NULL, version_number INTEGER NOT NULL CHECK(version_number>0),
      predecessor_version_id UUID NULL, status TEXT NOT NULL DEFAULT 'DRAFT'
        CHECK(status IN('DRAFT','REVIEW_REQUIRED','SEALED','INVALIDATED','SUPERSEDED')),
      semantic_version TEXT NOT NULL CHECK(semantic_version='GDSS_DECISION_PREFERENCE_V1'),
      mode TEXT NOT NULL CHECK(mode IN('UNWEIGHTED_PARETO','ORDINAL_PRIORITY','EXPLICIT_NORMALIZED_WEIGHTS')),
      scope JSONB NOT NULL CHECK(jsonb_typeof(scope)='object'), canonical_content TEXT NOT NULL,
      content_hash CHAR(64) NOT NULL CHECK(content_hash~'^[0-9a-f]{64}$'),
      idempotency_key TEXT NOT NULL, authored_by TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(), updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(preference_identity_id,project_id) REFERENCES public.gdss_decision_preference_identity(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(predecessor_version_id,project_id) REFERENCES public.gdss_decision_preference_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(preference_identity_id,version_number), UNIQUE(project_id,content_hash),
      UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_decision_preference_item (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL,
      preference_version_id UUID NOT NULL, objective_key TEXT NOT NULL,
      ordinal_priority INTEGER NULL CHECK(ordinal_priority IS NULL OR ordinal_priority>0),
      weight DOUBLE PRECISION NULL CHECK(weight IS NULL OR (weight NOT IN ('NaN'::float8,'Infinity'::float8,'-Infinity'::float8) AND weight>=0)),
      FOREIGN KEY(preference_version_id,project_id) REFERENCES public.gdss_decision_preference_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(preference_version_id,objective_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_decision_risk_identity (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      canonical_key TEXT NOT NULL CHECK(length(btrim(canonical_key)) BETWEEN 1 AND 256),
      idempotency_key TEXT NOT NULL, created_by TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      UNIQUE(project_id,canonical_key), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_decision_risk_version (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL,
      risk_identity_id UUID NOT NULL, version_number INTEGER NOT NULL CHECK(version_number>0),
      predecessor_version_id UUID NULL, status TEXT NOT NULL DEFAULT 'DRAFT'
        CHECK(status IN('DRAFT','REVIEW_REQUIRED','SEALED','INVALIDATED','SUPERSEDED')),
      semantic_version TEXT NOT NULL CHECK(semantic_version='GDSS_DECISION_RISK_V1'),
      scope JSONB NOT NULL CHECK(jsonb_typeof(scope)='object'), canonical_content TEXT NOT NULL,
      content_hash CHAR(64) NOT NULL CHECK(content_hash~'^[0-9a-f]{64}$'),
      idempotency_key TEXT NOT NULL, authored_by TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(), updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(risk_identity_id,project_id) REFERENCES public.gdss_decision_risk_identity(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(predecessor_version_id,project_id) REFERENCES public.gdss_decision_risk_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(risk_identity_id,version_number), UNIQUE(project_id,content_hash),
      UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_decision_risk_dimension (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL,
      risk_version_id UUID NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 255),
      dimension_key TEXT NOT NULL, source JSONB NOT NULL CHECK(jsonb_typeof(source)='object'),
      severity TEXT NOT NULL CHECK(severity IN('LOW','MODERATE','HIGH','CRITICAL')),
      likelihood_knowledge_state TEXT NOT NULL CHECK(likelihood_knowledge_state IN('KNOWN','BOUNDED','UNKNOWN')),
      reversibility TEXT NOT NULL CHECK(reversibility IN('REVERSIBLE','PARTIALLY_REVERSIBLE','IRREVERSIBLE','UNKNOWN')),
      recoverability TEXT NOT NULL CHECK(recoverability IN('RECOVERABLE','CONDITIONALLY_RECOVERABLE','NOT_RECOVERABLE','UNKNOWN')),
      uncertainty TEXT NOT NULL CHECK(uncertainty IN('CHARACTERIZED','PARTIAL','UNKNOWN')),
      state TEXT NOT NULL CHECK(state IN('ACCEPTABLE','CONDITIONALLY_ACCEPTABLE','UNACCEPTABLE','UNKNOWN')),
      unknown_handling TEXT NOT NULL CHECK(unknown_handling IN('REVIEW_REQUIRED','FAIL_CLOSED')),
      acceptance_rule TEXT NOT NULL, scope JSONB NOT NULL CHECK(jsonb_typeof(scope)='object'),
      FOREIGN KEY(risk_version_id,project_id) REFERENCES public.gdss_decision_risk_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(risk_version_id,ordinal), UNIQUE(risk_version_id,dimension_key), UNIQUE(id,project_id),
      CHECK((likelihood_knowledge_state<>'UNKNOWN' AND uncertainty<>'UNKNOWN') OR state='UNKNOWN'));

    CREATE TABLE public.gdss_decision_problem_identity (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      canonical_key TEXT NOT NULL CHECK(length(btrim(canonical_key)) BETWEEN 1 AND 256),
      idempotency_key TEXT NOT NULL, created_by TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      UNIQUE(project_id,canonical_key), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_decision_problem_version (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL,
      problem_identity_id UUID NOT NULL, version_number INTEGER NOT NULL CHECK(version_number>0),
      predecessor_version_id UUID NULL, status TEXT NOT NULL DEFAULT 'DRAFT'
        CHECK(status IN('DRAFT','REVIEW_REQUIRED','SEALED','EVALUATING','EVALUATED','INVALIDATED','SUPERSEDED')),
      semantic_version TEXT NOT NULL CHECK(semantic_version='GDSS_DECISION_PROBLEM_V1'),
      context_snapshot JSONB NOT NULL CHECK(jsonb_typeof(context_snapshot)='object'),
      decision_scope JSONB NOT NULL CHECK(jsonb_typeof(decision_scope)='object'),
      decision_horizon JSONB NOT NULL CHECK(jsonb_typeof(decision_horizon)='object'),
      target_variables TEXT[] NOT NULL CHECK(cardinality(target_variables) BETWEEN 1 AND 16),
      preference_profile_version_id UUID NOT NULL, preference_profile_hash CHAR(64) NOT NULL,
      risk_profile_version_id UUID NOT NULL, risk_profile_hash CHAR(64) NOT NULL,
      resource_profile TEXT NOT NULL CHECK(resource_profile='GDSS_DECISION_LIMITS_V1'),
      allowed_alternative_provenance TEXT[] NOT NULL CHECK(cardinality(allowed_alternative_provenance)>0),
      allowed_scenario_methods TEXT[] NOT NULL CHECK(cardinality(allowed_scenario_methods) BETWEEN 1 AND 32),
      recommendation_eligibility TEXT NOT NULL CHECK(recommendation_eligibility IN('AUTHORIZED_RECOMMENDATION_V1_ELIGIBLE','CANNOT_SUPPORT_AUTHORIZED_RECOMMENDATION_V1')),
      decision_support_review_required BOOLEAN NOT NULL,
      canonical_content TEXT NOT NULL, decision_problem_hash CHAR(64) NOT NULL CHECK(decision_problem_hash~'^[0-9a-f]{64}$'),
      idempotency_key TEXT NOT NULL, authored_by TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(), updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(problem_identity_id,project_id) REFERENCES public.gdss_decision_problem_identity(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(predecessor_version_id,project_id) REFERENCES public.gdss_decision_problem_version(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(preference_profile_version_id,project_id) REFERENCES public.gdss_decision_preference_version(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(risk_profile_version_id,project_id) REFERENCES public.gdss_decision_risk_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(problem_identity_id,version_number), UNIQUE(project_id,decision_problem_hash),
      UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_decision_problem_model_ref (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL,
      problem_version_id UUID NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 15),
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT,
      model_content_hash CHAR(64) NOT NULL, binding_version_id UUID NOT NULL,
      binding_content_hash CHAR(64) NOT NULL,
      FOREIGN KEY(problem_version_id,project_id) REFERENCES public.gdss_decision_problem_version(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(binding_version_id,model_version_id) REFERENCES public.gdss_dynamic_binding_version(id,model_version_id) ON DELETE RESTRICT,
      UNIQUE(problem_version_id,ordinal), UNIQUE(problem_version_id,model_version_id,binding_version_id));

    CREATE TABLE public.gdss_decision_problem_evidence_ref (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL,
      problem_version_id UUID NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 63),
      evidence_set_id UUID NOT NULL, evidence_set_hash CHAR(64) NOT NULL,
      capability_assessment_id UUID NOT NULL, capability_assessment_hash CHAR(64) NOT NULL,
      predictive_claim_id UUID NOT NULL, predictive_claim_hash CHAR(64) NOT NULL,
      validity_domain_version_id UUID NOT NULL REFERENCES public.gdss_validity_domain_version(id) ON DELETE RESTRICT,
      validity_domain_hash CHAR(64) NOT NULL,
      FOREIGN KEY(problem_version_id,project_id) REFERENCES public.gdss_decision_problem_version(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(evidence_set_id,project_id) REFERENCES public.gdss_predictive_evidence_set(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(capability_assessment_id,project_id) REFERENCES public.gdss_capability_assessment(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(predictive_claim_id,project_id) REFERENCES public.gdss_predictive_claim_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(problem_version_id,ordinal), UNIQUE(problem_version_id,evidence_set_id,capability_assessment_id,predictive_claim_id));

    CREATE TABLE public.gdss_decision_objective (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL,
      problem_version_id UUID NOT NULL, objective_key TEXT NOT NULL, direction TEXT NOT NULL
        CHECK(direction IN('MINIMIZE','MAXIMIZE','TARGET_RANGE','MAINTAIN_WITHIN')),
      quantity_key TEXT NOT NULL, unit JSONB NOT NULL, target JSONB NOT NULL,
      horizon_key TEXT NOT NULL, criterion_version_id UUID NOT NULL,
      criterion_content_hash CHAR(64) NOT NULL, aspiration_bounds JSONB NOT NULL,
      acceptance_bounds JSONB NOT NULL, required BOOLEAN NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 15),
      FOREIGN KEY(problem_version_id,project_id) REFERENCES public.gdss_decision_problem_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(problem_version_id,objective_key), UNIQUE(problem_version_id,ordinal));

    CREATE TABLE public.gdss_decision_constraint (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL,
      problem_version_id UUID NOT NULL, constraint_key TEXT NOT NULL,
      constraint_type TEXT NOT NULL CHECK(constraint_type IN('HARD_CONSTRAINT','SOFT_CONSTRAINT','ADVISORY_CONSTRAINT')),
      scope JSONB NOT NULL, predicate_method TEXT NOT NULL, unit JSONB NULL,
      threshold JSONB NOT NULL, required_inputs JSONB NOT NULL CHECK(jsonb_typeof(required_inputs)='array' AND jsonb_array_length(required_inputs)>0),
      missing_semantics TEXT NOT NULL CHECK(missing_semantics IN('FAIL_CLOSED','REVIEW_REQUIRED','INCOMPLETE')),
      provenance JSONB NOT NULL, explanation TEXT NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 63),
      FOREIGN KEY(problem_version_id,project_id) REFERENCES public.gdss_decision_problem_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(problem_version_id,constraint_key), UNIQUE(problem_version_id,ordinal),
      CHECK(constraint_type<>'HARD_CONSTRAINT' OR missing_semantics='FAIL_CLOSED'));

    CREATE TABLE public.gdss_decision_audit_event (
      id BIGSERIAL PRIMARY KEY, project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      entity_type TEXT NOT NULL CHECK(entity_type IN('DECISION_PROBLEM','PREFERENCE_PROFILE','RISK_PROFILE')),
      entity_id UUID NOT NULL, sequence INTEGER NOT NULL CHECK(sequence>0),
      event_type TEXT NOT NULL CHECK(event_type IN('CREATE','UPDATE_DRAFT','SUBMIT_REVIEW','SEAL','INVALIDATE','SUPERSEDE','SOD_EXCEPTION','AI_AUTHORITY_DENIAL')),
      from_status TEXT NULL, to_status TEXT NULL, actor TEXT NOT NULL, actor_kind TEXT NOT NULL CHECK(actor_kind IN('HUMAN','AI')),
      reason TEXT NOT NULL, idempotency_key TEXT NOT NULL, event_hash CHAR(64) NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}', created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      UNIQUE(entity_type,entity_id,sequence), UNIQUE(project_id,idempotency_key), UNIQUE(project_id,event_hash));

    CREATE FUNCTION public.gdss007a_reject_mutation() RETURNS TRIGGER AS $$
    BEGIN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE'; END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007a_guard_version_insert() RETURNS TRIGGER AS $$
    DECLARE identity_project UUID; expected INTEGER; predecessor RECORD;
    BEGIN
      IF TG_TABLE_NAME='gdss_decision_problem_version' THEN
        SELECT project_id INTO identity_project FROM public.gdss_decision_problem_identity WHERE id=NEW.problem_identity_id;
        SELECT coalesce(max(version_number),0)+1 INTO expected FROM public.gdss_decision_problem_version WHERE problem_identity_id=NEW.problem_identity_id;
      ELSIF TG_TABLE_NAME='gdss_decision_preference_version' THEN
        SELECT project_id INTO identity_project FROM public.gdss_decision_preference_identity WHERE id=NEW.preference_identity_id;
        SELECT coalesce(max(version_number),0)+1 INTO expected FROM public.gdss_decision_preference_version WHERE preference_identity_id=NEW.preference_identity_id;
      ELSE
        SELECT project_id INTO identity_project FROM public.gdss_decision_risk_identity WHERE id=NEW.risk_identity_id;
        SELECT coalesce(max(version_number),0)+1 INTO expected FROM public.gdss_decision_risk_version WHERE risk_identity_id=NEW.risk_identity_id;
      END IF;
      IF identity_project IS DISTINCT FROM NEW.project_id THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE'; END IF;
      IF NEW.status<>'DRAFT' OR NEW.version_number<>expected THEN RAISE EXCEPTION 'INVALID_DECISION_LIFECYCLE'; END IF;
      IF NEW.predecessor_version_id IS NULL AND NEW.version_number<>1 THEN RAISE EXCEPTION 'DECISION_INPUT_NOT_CURRENT'; END IF;
      IF NEW.predecessor_version_id IS NOT NULL THEN
        EXECUTE format('SELECT * FROM public.%I WHERE id=$1',TG_TABLE_NAME) INTO predecessor USING NEW.predecessor_version_id;
        IF predecessor.project_id IS DISTINCT FROM NEW.project_id OR predecessor.version_number<>NEW.version_number-1 THEN RAISE EXCEPTION 'DECISION_INPUT_NOT_CURRENT'; END IF;
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007a_guard_version_update() RETURNS TRIGGER AS $$
    BEGIN
      IF TG_OP='DELETE' THEN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE'; END IF;
      IF (OLD.id,OLD.project_id,OLD.version_number,OLD.created_at,OLD.authored_by) IS DISTINCT FROM
         (NEW.id,NEW.project_id,NEW.version_number,NEW.created_at,NEW.authored_by) THEN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE'; END IF;
      IF TG_TABLE_NAME='gdss_decision_problem_version' THEN
        IF (OLD.problem_identity_id,OLD.predecessor_version_id) IS DISTINCT FROM (NEW.problem_identity_id,NEW.predecessor_version_id) THEN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE'; END IF;
      ELSIF TG_TABLE_NAME='gdss_decision_preference_version' THEN
        IF (OLD.preference_identity_id,OLD.predecessor_version_id) IS DISTINCT FROM (NEW.preference_identity_id,NEW.predecessor_version_id) THEN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE'; END IF;
      ELSE
        IF (OLD.risk_identity_id,OLD.predecessor_version_id) IS DISTINCT FROM (NEW.risk_identity_id,NEW.predecessor_version_id) THEN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE'; END IF;
      END IF;
      IF OLD.status<>'DRAFT' AND ROW(OLD.*) IS DISTINCT FROM ROW(NEW.*) AND OLD.status=NEW.status THEN RAISE EXCEPTION 'DECISION_PROBLEM_FROZEN'; END IF;
      IF OLD.status='DRAFT' AND NEW.status='DRAFT' THEN RETURN NEW; END IF;
      IF (to_jsonb(OLD)-'status'-'updated_at') IS DISTINCT FROM (to_jsonb(NEW)-'status'-'updated_at') THEN RAISE EXCEPTION 'DECISION_PROBLEM_FROZEN'; END IF;
      IF NOT ((OLD.status='DRAFT' AND NEW.status IN('REVIEW_REQUIRED','INVALIDATED')) OR
              (OLD.status='REVIEW_REQUIRED' AND NEW.status IN('SEALED','INVALIDATED')) OR
              (OLD.status='SEALED' AND NEW.status IN('INVALIDATED','SUPERSEDED','EVALUATING')) OR
              (OLD.status='EVALUATING' AND NEW.status='EVALUATED') OR
              (OLD.status='EVALUATED' AND NEW.status='SUPERSEDED')) THEN
        RAISE EXCEPTION 'INVALID_DECISION_LIFECYCLE';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007a_guard_problem_child() RETURNS TRIGGER AS $$
    DECLARE parent RECORD; actual INTEGER; limit_value INTEGER;
    BEGIN
      IF TG_OP='DELETE' THEN SELECT * INTO parent FROM public.gdss_decision_problem_version WHERE id=OLD.problem_version_id; ELSE SELECT * INTO parent FROM public.gdss_decision_problem_version WHERE id=NEW.problem_version_id; END IF;
      IF parent.status<>'DRAFT' THEN RAISE EXCEPTION 'DECISION_PROBLEM_FROZEN'; END IF;
      IF TG_OP='DELETE' THEN RETURN OLD; END IF;
      IF parent.project_id IS DISTINCT FROM NEW.project_id THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE'; END IF;
      IF TG_OP='INSERT' AND TG_TABLE_NAME IN('gdss_decision_objective','gdss_decision_constraint') THEN
        PERFORM pg_advisory_xact_lock(hashtextextended(NEW.problem_version_id::text,0));
        limit_value:=CASE WHEN TG_TABLE_NAME='gdss_decision_objective' THEN 16 ELSE 64 END;
        EXECUTE format('SELECT count(*) FROM public.%I WHERE problem_version_id=$1',TG_TABLE_NAME) INTO actual USING NEW.problem_version_id;
        IF actual>=limit_value THEN RAISE EXCEPTION 'RESOURCE_LIMIT_EXCEEDED resource=% limit=% actual=%',upper(TG_TABLE_NAME),limit_value,actual+1; END IF;
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007a_guard_profile_item() RETURNS TRIGGER AS $$
    DECLARE parent RECORD;
    BEGIN
      IF TG_TABLE_NAME='gdss_decision_preference_item' THEN
        SELECT * INTO parent FROM public.gdss_decision_preference_version WHERE id=COALESCE(NEW.preference_version_id,OLD.preference_version_id);
      ELSE SELECT * INTO parent FROM public.gdss_decision_risk_version WHERE id=COALESCE(NEW.risk_version_id,OLD.risk_version_id); END IF;
      IF parent.status<>'DRAFT' THEN RAISE EXCEPTION 'DECISION_PROBLEM_FROZEN'; END IF;
      IF TG_OP='DELETE' THEN RETURN OLD; END IF;
      IF parent.project_id IS DISTINCT FROM NEW.project_id THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE'; END IF;
      IF TG_TABLE_NAME='gdss_decision_preference_item' THEN
        IF parent.mode='EXPLICIT_NORMALIZED_WEIGHTS' AND NEW.weight IS NULL THEN RAISE EXCEPTION 'PREFERENCE_REQUIRED'; END IF;
        IF parent.mode<>'EXPLICIT_NORMALIZED_WEIGHTS' AND NEW.weight IS NOT NULL THEN RAISE EXCEPTION 'PREFERENCE_PROFILE_MISMATCH'; END IF;
        IF parent.mode='ORDINAL_PRIORITY' AND NEW.ordinal_priority IS NULL THEN RAISE EXCEPTION 'PREFERENCE_REQUIRED'; END IF;
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007a_guard_model_ref() RETURNS TRIGGER AS $$
    DECLARE parent RECORD; mp UUID; mh TEXT; bp UUID; bm UUID; bh TEXT;
    BEGIN
      SELECT * INTO parent FROM public.gdss_decision_problem_version WHERE id=NEW.problem_version_id;
      SELECT i.project_id,v.content_hash INTO mp,mh FROM public.gdss_version v JOIN public.gdss_identity i ON i.id=v.identity_id WHERE v.id=NEW.model_version_id;
      SELECT b.project_id,v.model_version_id,v.dynamic_binding_hash INTO bp,bm,bh FROM public.gdss_dynamic_binding_version v JOIN public.gdss_dynamic_binding b ON b.id=v.binding_id WHERE v.id=NEW.binding_version_id;
      IF parent.project_id IS DISTINCT FROM NEW.project_id OR mp IS DISTINCT FROM NEW.project_id OR bp IS DISTINCT FROM NEW.project_id OR
         bm IS DISTINCT FROM NEW.model_version_id OR mh IS DISTINCT FROM NEW.model_content_hash OR bh IS DISTINCT FROM NEW.binding_content_hash
      THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007a_guard_evidence_ref() RETURNS TRIGGER AS $$
    DECLARE parent RECORD; es RECORD; ca RECORD; cl RECORD; dh TEXT; dp UUID;
    BEGIN
      SELECT * INTO parent FROM public.gdss_decision_problem_version WHERE id=NEW.problem_version_id;
      SELECT * INTO es FROM public.gdss_predictive_evidence_set WHERE id=NEW.evidence_set_id;
      SELECT * INTO ca FROM public.gdss_capability_assessment WHERE id=NEW.capability_assessment_id;
      SELECT * INTO cl FROM public.gdss_predictive_claim_version WHERE id=NEW.predictive_claim_id;
      SELECT v.content_hash,i.project_id INTO dh,dp FROM public.gdss_validity_domain_version v JOIN public.gdss_validity_domain_identity i ON i.id=v.domain_identity_id WHERE v.id=NEW.validity_domain_version_id;
      IF parent.project_id IS DISTINCT FROM NEW.project_id OR es.project_id IS DISTINCT FROM NEW.project_id OR ca.project_id IS DISTINCT FROM NEW.project_id OR cl.project_id IS DISTINCT FROM NEW.project_id OR dp IS DISTINCT FROM NEW.project_id OR
         es.content_hash IS DISTINCT FROM NEW.evidence_set_hash OR ca.content_hash IS DISTINCT FROM NEW.capability_assessment_hash OR cl.content_hash IS DISTINCT FROM NEW.predictive_claim_hash OR dh IS DISTINCT FROM NEW.validity_domain_hash OR
         ca.evidence_set_id IS DISTINCT FROM es.id OR cl.capability_assessment_id IS DISTINCT FROM ca.id OR cl.evidence_set_id IS DISTINCT FROM es.id OR es.validity_domain_version_id IS DISTINCT FROM NEW.validity_domain_version_id
      THEN RAISE EXCEPTION 'CROSS_PROJECT_DECISION_REFERENCE'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007a_validate_profile(profile_kind TEXT, profile_id UUID) RETURNS VOID AS $$
    DECLARE profile RECORD; item_count INTEGER; weight_count INTEGER; weight_sum NUMERIC; unknown_count INTEGER;
    BEGIN
      IF profile_kind='PREFERENCE_PROFILE' THEN
        SELECT * INTO profile FROM public.gdss_decision_preference_version WHERE id=profile_id;
        SELECT count(*),count(weight),coalesce(sum(weight::numeric),0) INTO item_count,weight_count,weight_sum FROM public.gdss_decision_preference_item WHERE preference_version_id=profile_id;
        IF item_count=0 THEN RAISE EXCEPTION 'PREFERENCE_REQUIRED'; END IF;
        IF profile.mode='EXPLICIT_NORMALIZED_WEIGHTS' AND (weight_count<>item_count OR abs(weight_sum-1)>0.000000000001) THEN RAISE EXCEPTION 'PREFERENCE_PROFILE_MISMATCH'; END IF;
      ELSE
        SELECT * INTO profile FROM public.gdss_decision_risk_version WHERE id=profile_id;
        SELECT count(*),count(*) FILTER(WHERE (likelihood_knowledge_state='UNKNOWN' OR uncertainty='UNKNOWN') AND state<>'UNKNOWN') INTO item_count,unknown_count FROM public.gdss_decision_risk_dimension WHERE risk_version_id=profile_id;
        IF item_count=0 OR unknown_count>0 THEN RAISE EXCEPTION 'RISK_UNACCEPTABLE'; END IF;
      END IF;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007a_validate_problem_seal(problem_id UUID) RETURNS VOID AS $$
    DECLARE p RECORD; pref RECORD; risk RECORD; oc INTEGER; cc INTEGER; mc INTEGER; ec INTEGER; missing_pref INTEGER; invalid_ref INTEGER;
    BEGIN
      SELECT * INTO p FROM public.gdss_decision_problem_version WHERE id=problem_id;
      SELECT * INTO pref FROM public.gdss_decision_preference_version WHERE id=p.preference_profile_version_id;
      SELECT * INTO risk FROM public.gdss_decision_risk_version WHERE id=p.risk_profile_version_id;
      SELECT count(*) INTO oc FROM public.gdss_decision_objective WHERE problem_version_id=problem_id;
      SELECT count(*) INTO cc FROM public.gdss_decision_constraint WHERE problem_version_id=problem_id;
      SELECT count(*) INTO mc FROM public.gdss_decision_problem_model_ref WHERE problem_version_id=problem_id;
      SELECT count(*) INTO ec FROM public.gdss_decision_problem_evidence_ref WHERE problem_version_id=problem_id;
      IF oc<1 OR oc>16 OR cc>64 THEN RAISE EXCEPTION 'RESOURCE_LIMIT_EXCEEDED'; END IF;
      IF mc<1 OR ec<1 THEN RAISE EXCEPTION 'DECISION_INPUT_NOT_CURRENT'; END IF;
      IF pref.status<>'SEALED' OR pref.content_hash<>p.preference_profile_hash OR risk.status<>'SEALED' OR risk.content_hash<>p.risk_profile_hash THEN RAISE EXCEPTION 'PREFERENCE_PROFILE_MISMATCH'; END IF;
      SELECT count(*) INTO missing_pref FROM public.gdss_decision_objective o WHERE o.problem_version_id=problem_id AND NOT EXISTS(SELECT 1 FROM public.gdss_decision_preference_item i WHERE i.preference_version_id=p.preference_profile_version_id AND i.objective_key=o.objective_key);
      IF missing_pref>0 THEN RAISE EXCEPTION 'PREFERENCE_REQUIRED'; END IF;
      SELECT count(*) INTO invalid_ref FROM public.gdss_decision_problem_evidence_ref r
        LEFT JOIN public.gdss_capability_assessment c ON c.id=r.capability_assessment_id
        LEFT JOIN public.gdss_predictive_claim_version q ON q.id=r.predictive_claim_id
        WHERE r.problem_version_id=problem_id AND (
          c.id IS NULL OR q.id IS NULL OR c.state NOT IN('EVIDENCE_OF_CAPABILITY','EVIDENCE_OF_LIMITED_CAPABILITY') OR q.status<>'AUTHORIZED' OR
          (q.valid_through_epoch_micros IS NOT NULL AND q.valid_through_epoch_micros < floor(extract(epoch FROM clock_timestamp())*1000000)::bigint) OR
          EXISTS(SELECT 1 FROM public.gdss_predictive_claim_revocation x WHERE x.claim_id=q.id) OR
          EXISTS(SELECT 1 FROM public.gdss_revalidation_trigger_assessment t WHERE t.claim_id=q.id AND t.state IN('DETECTED','REVIEW_REQUIRED','REVALIDATION_REQUIRED') AND NOT EXISTS(SELECT 1 FROM public.gdss_revalidation_trigger_assessment s WHERE s.predecessor_trigger_id=t.id)));
      IF invalid_ref>0 THEN RAISE EXCEPTION 'CLAIM_NOT_CURRENT'; END IF;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss007a_guard_audit_event() RETURNS TRIGGER AS $$
    DECLARE expected INTEGER; current_status_value TEXT; author_value TEXT;
    BEGIN
      SELECT coalesce(max(sequence),0)+1 INTO expected FROM public.gdss_decision_audit_event WHERE entity_type=NEW.entity_type AND entity_id=NEW.entity_id;
      IF NEW.sequence<>expected THEN RAISE EXCEPTION 'DECISION_HISTORY_IMMUTABLE'; END IF;
      IF NEW.actor_kind='AI' AND NEW.event_type IN('SUBMIT_REVIEW','SEAL','SOD_EXCEPTION') THEN RAISE EXCEPTION 'AI_AUTHORITY_FORBIDDEN'; END IF;
      IF NEW.entity_type='DECISION_PROBLEM' THEN SELECT status,authored_by INTO current_status_value,author_value FROM public.gdss_decision_problem_version WHERE id=NEW.entity_id FOR UPDATE;
      ELSIF NEW.entity_type='PREFERENCE_PROFILE' THEN SELECT status,authored_by INTO current_status_value,author_value FROM public.gdss_decision_preference_version WHERE id=NEW.entity_id FOR UPDATE;
      ELSE SELECT status,authored_by INTO current_status_value,author_value FROM public.gdss_decision_risk_version WHERE id=NEW.entity_id FOR UPDATE; END IF;
      IF NEW.event_type='SEAL' THEN
        IF current_status_value<>'REVIEW_REQUIRED' OR NEW.from_status<>'REVIEW_REQUIRED' OR NEW.to_status<>'SEALED' THEN RAISE EXCEPTION 'INVALID_DECISION_LIFECYCLE'; END IF;
        IF author_value=NEW.actor AND coalesce((NEW.metadata->>'sod_exception')::boolean,false)=false THEN RAISE EXCEPTION 'SOD_VIOLATION'; END IF;
        IF NEW.entity_type='DECISION_PROBLEM' THEN PERFORM public.gdss007a_validate_problem_seal(NEW.entity_id);
        ELSE PERFORM public.gdss007a_validate_profile(NEW.entity_type,NEW.entity_id); END IF;
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_gdss007a_preference_identity_immutable BEFORE UPDATE OR DELETE ON public.gdss_decision_preference_identity FOR EACH ROW EXECUTE FUNCTION public.gdss007a_reject_mutation();
    CREATE TRIGGER trg_gdss007a_risk_identity_immutable BEFORE UPDATE OR DELETE ON public.gdss_decision_risk_identity FOR EACH ROW EXECUTE FUNCTION public.gdss007a_reject_mutation();
    CREATE TRIGGER trg_gdss007a_problem_identity_immutable BEFORE UPDATE OR DELETE ON public.gdss_decision_problem_identity FOR EACH ROW EXECUTE FUNCTION public.gdss007a_reject_mutation();
    CREATE TRIGGER trg_gdss007a_preference_insert BEFORE INSERT ON public.gdss_decision_preference_version FOR EACH ROW EXECUTE FUNCTION public.gdss007a_guard_version_insert();
    CREATE TRIGGER trg_gdss007a_risk_insert BEFORE INSERT ON public.gdss_decision_risk_version FOR EACH ROW EXECUTE FUNCTION public.gdss007a_guard_version_insert();
    CREATE TRIGGER trg_gdss007a_problem_insert BEFORE INSERT ON public.gdss_decision_problem_version FOR EACH ROW EXECUTE FUNCTION public.gdss007a_guard_version_insert();
    CREATE TRIGGER trg_gdss007a_preference_update BEFORE UPDATE OR DELETE ON public.gdss_decision_preference_version FOR EACH ROW EXECUTE FUNCTION public.gdss007a_guard_version_update();
    CREATE TRIGGER trg_gdss007a_risk_update BEFORE UPDATE OR DELETE ON public.gdss_decision_risk_version FOR EACH ROW EXECUTE FUNCTION public.gdss007a_guard_version_update();
    CREATE TRIGGER trg_gdss007a_problem_update BEFORE UPDATE OR DELETE ON public.gdss_decision_problem_version FOR EACH ROW EXECUTE FUNCTION public.gdss007a_guard_version_update();
    CREATE TRIGGER trg_gdss007a_preference_item_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_decision_preference_item FOR EACH ROW EXECUTE FUNCTION public.gdss007a_guard_profile_item();
    CREATE TRIGGER trg_gdss007a_risk_dimension_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_decision_risk_dimension FOR EACH ROW EXECUTE FUNCTION public.gdss007a_guard_profile_item();
    CREATE TRIGGER trg_gdss007a_model_ref_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_decision_problem_model_ref FOR EACH ROW EXECUTE FUNCTION public.gdss007a_guard_problem_child();
    CREATE TRIGGER trg_gdss007a_model_ref_exact BEFORE INSERT OR UPDATE ON public.gdss_decision_problem_model_ref FOR EACH ROW EXECUTE FUNCTION public.gdss007a_guard_model_ref();
    CREATE TRIGGER trg_gdss007a_evidence_ref_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_decision_problem_evidence_ref FOR EACH ROW EXECUTE FUNCTION public.gdss007a_guard_problem_child();
    CREATE TRIGGER trg_gdss007a_evidence_ref_exact BEFORE INSERT OR UPDATE ON public.gdss_decision_problem_evidence_ref FOR EACH ROW EXECUTE FUNCTION public.gdss007a_guard_evidence_ref();
    CREATE TRIGGER trg_gdss007a_objective_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_decision_objective FOR EACH ROW EXECUTE FUNCTION public.gdss007a_guard_problem_child();
    CREATE TRIGGER trg_gdss007a_constraint_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_decision_constraint FOR EACH ROW EXECUTE FUNCTION public.gdss007a_guard_problem_child();
    CREATE TRIGGER trg_gdss007a_audit_guard BEFORE INSERT ON public.gdss_decision_audit_event FOR EACH ROW EXECUTE FUNCTION public.gdss007a_guard_audit_event();
    CREATE TRIGGER trg_gdss007a_audit_immutable BEFORE UPDATE OR DELETE ON public.gdss_decision_audit_event FOR EACH ROW EXECUTE FUNCTION public.gdss007a_reject_mutation();

    CREATE INDEX gdss_decision_problem_project_status_idx ON public.gdss_decision_problem_version(project_id,status);
    CREATE INDEX gdss_decision_problem_evidence_idx ON public.gdss_decision_problem_evidence_ref(evidence_set_id,capability_assessment_id,predictive_claim_id);
    """)


def downgrade():
    op.execute(r"""
    DROP TABLE IF EXISTS public.gdss_decision_audit_event;
    DROP TABLE IF EXISTS public.gdss_decision_constraint;
    DROP TABLE IF EXISTS public.gdss_decision_objective;
    DROP TABLE IF EXISTS public.gdss_decision_problem_evidence_ref;
    DROP TABLE IF EXISTS public.gdss_decision_problem_model_ref;
    DROP TABLE IF EXISTS public.gdss_decision_problem_version;
    DROP TABLE IF EXISTS public.gdss_decision_problem_identity;
    DROP TABLE IF EXISTS public.gdss_decision_risk_dimension;
    DROP TABLE IF EXISTS public.gdss_decision_risk_version;
    DROP TABLE IF EXISTS public.gdss_decision_risk_identity;
    DROP TABLE IF EXISTS public.gdss_decision_preference_item;
    DROP TABLE IF EXISTS public.gdss_decision_preference_version;
    DROP TABLE IF EXISTS public.gdss_decision_preference_identity;
    DROP FUNCTION IF EXISTS public.gdss007a_guard_audit_event();
    DROP FUNCTION IF EXISTS public.gdss007a_validate_problem_seal(UUID);
    DROP FUNCTION IF EXISTS public.gdss007a_validate_profile(TEXT,UUID);
    DROP FUNCTION IF EXISTS public.gdss007a_guard_evidence_ref();
    DROP FUNCTION IF EXISTS public.gdss007a_guard_model_ref();
    DROP FUNCTION IF EXISTS public.gdss007a_guard_profile_item();
    DROP FUNCTION IF EXISTS public.gdss007a_guard_problem_child();
    DROP FUNCTION IF EXISTS public.gdss007a_guard_version_update();
    DROP FUNCTION IF EXISTS public.gdss007a_guard_version_insert();
    DROP FUNCTION IF EXISTS public.gdss007a_reject_mutation();
    """)
