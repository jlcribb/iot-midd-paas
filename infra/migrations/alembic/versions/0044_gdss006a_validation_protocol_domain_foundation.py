"""GDSS-006A validation protocol and validity-domain foundation. Revision 0044."""
from alembic import op

revision = "0044"
down_revision = "0043"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r"""
    CREATE TABLE public.gdss_validity_domain_identity (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      logical_key TEXT NOT NULL CHECK(length(btrim(logical_key)) BETWEEN 1 AND 128), created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(project_id,logical_key), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_validity_domain_version (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), domain_identity_id UUID NOT NULL REFERENCES public.gdss_validity_domain_identity(id) ON DELETE RESTRICT,
      version_number INTEGER NOT NULL CHECK(version_number>0), predecessor_version_id UUID NULL REFERENCES public.gdss_validity_domain_version(id) ON DELETE RESTRICT,
      status TEXT NOT NULL DEFAULT 'DRAFT' CHECK(status IN ('DRAFT','APPROVED','SEALED','SUPERSEDED','INVALIDATED')),
      semantic_version TEXT NOT NULL CHECK(semantic_version='GDSS_VALIDITY_DOMAIN_V1'), content JSONB NOT NULL CHECK(jsonb_typeof(content)='object'),
      canonical_content TEXT NOT NULL, content_hash CHAR(64) NULL CHECK(content_hash IS NULL OR content_hash ~ '^[0-9a-f]{64}$'),
      created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), approved_by TEXT NULL, approved_at TIMESTAMPTZ NULL,
      sealed_by TEXT NULL, sealed_at TIMESTAMPTZ NULL, superseded_by TEXT NULL, superseded_at TIMESTAMPTZ NULL,
      invalidated_by TEXT NULL, invalidated_at TIMESTAMPTZ NULL,
      UNIQUE(domain_identity_id,version_number), UNIQUE(domain_identity_id,id),
      CHECK((status IN ('DRAFT','APPROVED') AND content_hash IS NULL) OR (status IN ('SEALED','SUPERSEDED','INVALIDATED') AND content_hash IS NOT NULL)));
    CREATE UNIQUE INDEX gdss_validity_domain_hash_uq ON public.gdss_validity_domain_version(domain_identity_id,content_hash) WHERE content_hash IS NOT NULL;
    CREATE TABLE public.gdss_domain_predicate (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), domain_version_id UUID NOT NULL REFERENCES public.gdss_validity_domain_version(id) ON DELETE RESTRICT,
      ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 63), predicate_key TEXT NOT NULL, predicate_type TEXT NOT NULL CHECK(predicate_type IN ('NUMERIC_RANGE','CATEGORICAL_MEMBERSHIP','BOOLEAN_CONDITION','TEMPORAL_RANGE','PARAMETER_RANGE')),
      variable_key TEXT NOT NULL, operator TEXT NOT NULL, lower_bound DOUBLE PRECISION NULL CHECK(lower_bound IS NULL OR lower_bound NOT IN ('NaN'::float8,'Infinity'::float8,'-Infinity'::float8)), upper_bound DOUBLE PRECISION NULL CHECK(upper_bound IS NULL OR upper_bound NOT IN ('NaN'::float8,'Infinity'::float8,'-Infinity'::float8)),
      lower_inclusive BOOLEAN NULL, upper_inclusive BOOLEAN NULL, allowed_values JSONB NULL, expected_boolean BOOLEAN NULL,
      start_epoch_micros BIGINT NULL, end_epoch_micros BIGINT NULL, unit_identity JSONB NULL, rationale TEXT NOT NULL,
      UNIQUE(domain_version_id,ordinal), UNIQUE(domain_version_id,predicate_key),
      CHECK((predicate_type IN ('NUMERIC_RANGE','PARAMETER_RANGE') AND lower_bound IS NOT NULL AND upper_bound IS NOT NULL AND lower_bound<=upper_bound AND lower_inclusive IS NOT NULL AND upper_inclusive IS NOT NULL AND allowed_values IS NULL AND expected_boolean IS NULL AND start_epoch_micros IS NULL)
         OR (predicate_type='CATEGORICAL_MEMBERSHIP' AND lower_bound IS NULL AND upper_bound IS NULL AND allowed_values IS NOT NULL AND jsonb_typeof(allowed_values)='array' AND jsonb_array_length(allowed_values)>0 AND expected_boolean IS NULL AND unit_identity IS NULL)
         OR (predicate_type='BOOLEAN_CONDITION' AND lower_bound IS NULL AND upper_bound IS NULL AND allowed_values IS NULL AND expected_boolean IS NOT NULL AND unit_identity IS NULL)
         OR (predicate_type='TEMPORAL_RANGE' AND start_epoch_micros IS NOT NULL AND end_epoch_micros IS NOT NULL AND start_epoch_micros<=end_epoch_micros AND lower_bound IS NULL AND upper_bound IS NULL AND allowed_values IS NULL AND expected_boolean IS NULL)));
    CREATE TABLE public.gdss_domain_boundary (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), domain_version_id UUID NOT NULL REFERENCES public.gdss_validity_domain_version(id) ON DELETE RESTRICT,
      ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 63), boundary_key TEXT NOT NULL, boundary_kind TEXT NOT NULL CHECK(boundary_kind IN ('HARD','DECLARED_OPERATIONAL','UNKNOWN')),
      predicate_keys JSONB NOT NULL CHECK(jsonb_typeof(predicate_keys)='array' AND jsonb_array_length(predicate_keys)>0), description TEXT NOT NULL,
      UNIQUE(domain_version_id,ordinal), UNIQUE(domain_version_id,boundary_key));
    CREATE TABLE public.gdss_validity_domain_lifecycle_event (
      id BIGSERIAL PRIMARY KEY, domain_version_id UUID NOT NULL REFERENCES public.gdss_validity_domain_version(id) ON DELETE RESTRICT,
      sequence INTEGER NOT NULL CHECK(sequence BETWEEN 1 AND 5), from_status TEXT NULL, to_status TEXT NOT NULL CHECK(to_status IN ('DRAFT','APPROVED','SEALED','SUPERSEDED','INVALIDATED')),
      actor TEXT NOT NULL, reason TEXT NOT NULL, resulting_content_hash CHAR(64) NULL, idempotency_key TEXT NOT NULL, sod_exception BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(domain_version_id,sequence), UNIQUE(domain_version_id,idempotency_key));

    CREATE TABLE public.gdss_validation_protocol_identity (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      logical_key TEXT NOT NULL CHECK(length(btrim(logical_key)) BETWEEN 1 AND 128), created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(project_id,logical_key), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_validation_protocol_version (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), protocol_identity_id UUID NOT NULL REFERENCES public.gdss_validation_protocol_identity(id) ON DELETE RESTRICT,
      version_number INTEGER NOT NULL CHECK(version_number>0), predecessor_version_id UUID NULL REFERENCES public.gdss_validation_protocol_version(id) ON DELETE RESTRICT,
      status TEXT NOT NULL DEFAULT 'DRAFT' CHECK(status IN ('DRAFT','REVIEW_REQUIRED','APPROVED','SEALED','SUPERSEDED','INVALIDATED')),
      semantic_version TEXT NOT NULL CHECK(semantic_version='GDSS_VALIDATION_PROTOCOL_V1'),
      model_identity_id UUID NOT NULL REFERENCES public.gdss_identity(id) ON DELETE RESTRICT, model_version_id UUID NOT NULL, model_version_number INTEGER NOT NULL CHECK(model_version_number>0), model_content_hash CHAR(64) NOT NULL CHECK(model_content_hash ~ '^[0-9a-f]{64}$'),
      validity_domain_version_id UUID NOT NULL REFERENCES public.gdss_validity_domain_version(id) ON DELETE RESTRICT, validity_domain_hash CHAR(64) NOT NULL CHECK(validity_domain_hash ~ '^[0-9a-f]{64}$'),
      content JSONB NOT NULL CHECK(jsonb_typeof(content)='object'), canonical_content TEXT NOT NULL, content_hash CHAR(64) NULL CHECK(content_hash IS NULL OR content_hash ~ '^[0-9a-f]{64}$'),
      created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), approved_by TEXT NULL, approved_at TIMESTAMPTZ NULL,
      sealed_by TEXT NULL, sealed_at TIMESTAMPTZ NULL, superseded_by TEXT NULL, superseded_at TIMESTAMPTZ NULL,
      invalidated_by TEXT NULL, invalidated_at TIMESTAMPTZ NULL,
      FOREIGN KEY(model_identity_id,model_version_id) REFERENCES public.gdss_version(identity_id,id) ON DELETE RESTRICT,
      UNIQUE(protocol_identity_id,version_number), UNIQUE(protocol_identity_id,id),
      CHECK((status IN ('DRAFT','REVIEW_REQUIRED','APPROVED') AND content_hash IS NULL) OR (status IN ('SEALED','SUPERSEDED','INVALIDATED') AND content_hash IS NOT NULL)));
    CREATE UNIQUE INDEX gdss_validation_protocol_hash_uq ON public.gdss_validation_protocol_version(protocol_identity_id,content_hash) WHERE content_hash IS NOT NULL;
    CREATE TABLE public.gdss_validation_target (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), protocol_version_id UUID NOT NULL REFERENCES public.gdss_validation_protocol_version(id) ON DELETE RESTRICT,
      ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 15), target_key TEXT NOT NULL, variable_reference TEXT NOT NULL, unit_reference JSONB NOT NULL,
      aggregation TEXT NOT NULL CHECK(aggregation IN ('NONE','MEAN','SUM','MIN','MAX')), transformation TEXT NOT NULL CHECK(transformation IN ('IDENTITY','DECLARED_REFERENCE')),
      transformation_reference TEXT NULL, semantic_role TEXT NOT NULL CHECK(semantic_role IN ('OBSERVED_TARGET','DERIVED_TARGET')),
      UNIQUE(protocol_version_id,ordinal), UNIQUE(protocol_version_id,target_key), CHECK((transformation='IDENTITY' AND transformation_reference IS NULL) OR (transformation='DECLARED_REFERENCE' AND length(btrim(transformation_reference))>0)));
    CREATE TABLE public.gdss_validation_horizon (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), protocol_version_id UUID NOT NULL REFERENCES public.gdss_validation_protocol_version(id) ON DELETE RESTRICT,
      ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 15), horizon_key TEXT NOT NULL, duration DOUBLE PRECISION NOT NULL CHECK(duration NOT IN ('NaN'::float8,'Infinity'::float8,'-Infinity'::float8) AND duration>0), unit_identity JSONB NOT NULL,
      forecast_origin_semantics TEXT NOT NULL CHECK(forecast_origin_semantics IN ('RUN_START','EXPLICIT_ORIGIN','ROLLING_ORIGIN')),
      UNIQUE(protocol_version_id,ordinal), UNIQUE(protocol_version_id,horizon_key));
    CREATE TABLE public.gdss_validation_acceptance_criterion (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), protocol_version_id UUID NOT NULL REFERENCES public.gdss_validation_protocol_version(id) ON DELETE RESTRICT,
      ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 63), criterion_key TEXT NOT NULL, metric_key TEXT NOT NULL, metric_version TEXT NOT NULL,
      operator TEXT NOT NULL CHECK(operator IN ('LT','LTE','GT','GTE','EQ')), threshold DOUBLE PRECISION NOT NULL CHECK(threshold NOT IN ('NaN'::float8,'Infinity'::float8,'-Infinity'::float8)), unit_identity JSONB NULL,
      scope TEXT NOT NULL CHECK(scope IN ('GLOBAL','TARGET','HORIZON','TARGET_HORIZON','SUBGROUP')), scope_reference TEXT NULL, required BOOLEAN NOT NULL,
      UNIQUE(protocol_version_id,ordinal), UNIQUE(protocol_version_id,criterion_key), CHECK((scope='GLOBAL' AND scope_reference IS NULL) OR (scope<>'GLOBAL' AND length(btrim(scope_reference))>0)));
    CREATE TABLE public.gdss_validation_policy (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), protocol_version_id UUID NOT NULL REFERENCES public.gdss_validation_protocol_version(id) ON DELETE RESTRICT,
      policy_type TEXT NOT NULL CHECK(policy_type IN ('EXCLUSION','MISSINGNESS','OUTLIER','MULTIPLICITY')), policy_version TEXT NOT NULL, policy_content JSONB NOT NULL CHECK(jsonb_typeof(policy_content)='object'),
      UNIQUE(protocol_version_id,policy_type));
    CREATE TABLE public.gdss_validation_revalidation_trigger (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), protocol_version_id UUID NOT NULL REFERENCES public.gdss_validation_protocol_version(id) ON DELETE RESTRICT,
      ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 11), trigger_type TEXT NOT NULL CHECK(trigger_type IN ('MODEL_STRUCTURE_CHANGED','FORMULA_CHANGED','PARAMETER_REGIME_CHANGED','NUMERICAL_METHOD_CHANGED','INPUT_DOMAIN_CHANGED','SENSOR_CHANGED','VALIDITY_DOMAIN_CHANGED','HORIZON_CHANGED','DRIFT_DETECTED','CONTRADICTORY_EVIDENCE','BASELINE_CHANGED','METRIC_CHANGED')),
      UNIQUE(protocol_version_id,ordinal), UNIQUE(protocol_version_id,trigger_type));
    CREATE TABLE public.gdss_validation_protocol_lifecycle_event (
      id BIGSERIAL PRIMARY KEY, protocol_version_id UUID NOT NULL REFERENCES public.gdss_validation_protocol_version(id) ON DELETE RESTRICT,
      sequence INTEGER NOT NULL CHECK(sequence BETWEEN 1 AND 7), from_status TEXT NULL, to_status TEXT NOT NULL CHECK(to_status IN ('DRAFT','REVIEW_REQUIRED','APPROVED','SEALED','SUPERSEDED','INVALIDATED')),
      actor TEXT NOT NULL, reason TEXT NOT NULL, resulting_content_hash CHAR(64) NULL, idempotency_key TEXT NOT NULL, sod_exception BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(protocol_version_id,sequence), UNIQUE(protocol_version_id,idempotency_key));

    CREATE FUNCTION public.gdss006a_reject_mutation() RETURNS TRIGGER AS $$ BEGIN RAISE EXCEPTION 'GDSS-006A immutable history'; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006a_guard_domain_content() RETURNS TRIGGER AS $$
    DECLARE version_id UUID; current_status TEXT;
    BEGIN
      IF pg_trigger_depth()>1 THEN RETURN NEW; END IF;
      IF TG_TABLE_NAME='gdss_validity_domain_version' THEN version_id:=COALESCE(NEW.id,OLD.id); ELSE version_id:=COALESCE(NEW.domain_version_id,OLD.domain_version_id); END IF;
      SELECT status INTO current_status FROM public.gdss_validity_domain_version WHERE id=version_id FOR SHARE;
      IF TG_OP='DELETE' OR current_status<>'DRAFT' THEN RAISE EXCEPTION 'VALIDITY_DOMAIN_IMMUTABLE'; END IF;
      IF TG_TABLE_NAME='gdss_validity_domain_version' THEN IF NEW.status IS DISTINCT FROM OLD.status THEN RAISE EXCEPTION 'Lifecycle event required'; END IF; END IF;
      RETURN COALESCE(NEW,OLD);
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006a_guard_protocol_content() RETURNS TRIGGER AS $$
    DECLARE version_id UUID; current_status TEXT;
    BEGIN
      IF pg_trigger_depth()>1 THEN RETURN NEW; END IF;
      IF TG_TABLE_NAME='gdss_validation_protocol_version' THEN version_id:=COALESCE(NEW.id,OLD.id); ELSE version_id:=COALESCE(NEW.protocol_version_id,OLD.protocol_version_id); END IF;
      SELECT status INTO current_status FROM public.gdss_validation_protocol_version WHERE id=version_id FOR SHARE;
      IF TG_OP='DELETE' OR current_status<>'DRAFT' THEN RAISE EXCEPTION 'VALIDATION_PROTOCOL_IMMUTABLE'; END IF;
      IF TG_TABLE_NAME='gdss_validation_protocol_version' THEN IF NEW.status IS DISTINCT FROM OLD.status THEN RAISE EXCEPTION 'Lifecycle event required'; END IF; END IF;
      RETURN COALESCE(NEW,OLD);
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006a_guard_domain_event() RETURNS TRIGGER AS $$
    DECLARE prior_sequence INTEGER; prior_status TEXT; expected_hash TEXT;
    BEGIN
      SELECT sequence,to_status INTO prior_sequence,prior_status FROM public.gdss_validity_domain_lifecycle_event WHERE domain_version_id=NEW.domain_version_id ORDER BY sequence DESC LIMIT 1 FOR UPDATE;
      IF prior_sequence IS NULL THEN IF NEW.sequence<>1 OR NEW.from_status IS NOT NULL OR NEW.to_status<>'DRAFT' THEN RAISE EXCEPTION 'Invalid domain initial lifecycle'; END IF;
      ELSIF NEW.sequence<>prior_sequence+1 OR NEW.from_status IS DISTINCT FROM prior_status OR NOT((prior_status='DRAFT' AND NEW.to_status='APPROVED') OR (prior_status='APPROVED' AND NEW.to_status='SEALED') OR (prior_status='SEALED' AND NEW.to_status IN ('SUPERSEDED','INVALIDATED'))) THEN RAISE EXCEPTION 'Illegal validity domain transition'; END IF;
      IF NEW.to_status='SEALED' THEN
        SELECT encode(digest(convert_to('gdss006:validity-domain:v1','UTF8')||decode('00','hex')||convert_to(canonical_content,'UTF8'),'sha256'),'hex') INTO expected_hash FROM public.gdss_validity_domain_version WHERE id=NEW.domain_version_id;
        IF NEW.resulting_content_hash IS NULL OR NEW.resulting_content_hash<>expected_hash THEN RAISE EXCEPTION 'Validity domain hash mismatch'; END IF;
      END IF;
      UPDATE public.gdss_validity_domain_version SET status=NEW.to_status,content_hash=CASE WHEN NEW.to_status='SEALED' THEN NEW.resulting_content_hash ELSE content_hash END,
        approved_by=CASE WHEN NEW.to_status='APPROVED' THEN NEW.actor ELSE approved_by END,approved_at=CASE WHEN NEW.to_status='APPROVED' THEN clock_timestamp() ELSE approved_at END,
        sealed_by=CASE WHEN NEW.to_status='SEALED' THEN NEW.actor ELSE sealed_by END,sealed_at=CASE WHEN NEW.to_status='SEALED' THEN clock_timestamp() ELSE sealed_at END,
        superseded_by=CASE WHEN NEW.to_status='SUPERSEDED' THEN NEW.actor ELSE superseded_by END,superseded_at=CASE WHEN NEW.to_status='SUPERSEDED' THEN clock_timestamp() ELSE superseded_at END,
        invalidated_by=CASE WHEN NEW.to_status='INVALIDATED' THEN NEW.actor ELSE invalidated_by END,invalidated_at=CASE WHEN NEW.to_status='INVALIDATED' THEN clock_timestamp() ELSE invalidated_at END WHERE id=NEW.domain_version_id;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006a_guard_protocol_binding() RETURNS TRIGGER AS $$
    DECLARE protocol_project UUID; model_project UUID; domain_project UUID; actual_model_hash TEXT; actual_domain_hash TEXT; domain_status TEXT;
    BEGIN
      SELECT project_id INTO protocol_project FROM public.gdss_validation_protocol_identity WHERE id=NEW.protocol_identity_id;
      SELECT i.project_id,v.content_hash INTO model_project,actual_model_hash FROM public.gdss_version v JOIN public.gdss_identity i ON i.id=v.identity_id WHERE v.id=NEW.model_version_id AND v.identity_id=NEW.model_identity_id AND v.version_number=NEW.model_version_number;
      SELECT i.project_id,v.content_hash,v.status INTO domain_project,actual_domain_hash,domain_status FROM public.gdss_validity_domain_version v JOIN public.gdss_validity_domain_identity i ON i.id=v.domain_identity_id WHERE v.id=NEW.validity_domain_version_id;
      IF model_project IS NULL THEN RAISE EXCEPTION 'MODEL_VERSION_NOT_FOUND'; END IF;
      IF protocol_project IS DISTINCT FROM model_project OR protocol_project IS DISTINCT FROM domain_project THEN RAISE EXCEPTION 'PROJECT_SCOPE_MISMATCH'; END IF;
      IF actual_model_hash IS DISTINCT FROM NEW.model_content_hash OR actual_domain_hash IS DISTINCT FROM NEW.validity_domain_hash OR domain_status<>'SEALED' THEN RAISE EXCEPTION 'VALIDITY_DOMAIN_VERSION_MISMATCH'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006a_guard_domain_predecessor() RETURNS TRIGGER AS $$
    BEGIN IF NEW.predecessor_version_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM public.gdss_validity_domain_version p WHERE p.id=NEW.predecessor_version_id AND p.domain_identity_id=NEW.domain_identity_id AND p.version_number<NEW.version_number) THEN RAISE EXCEPTION 'Validity domain predecessor mismatch'; END IF; RETURN NEW; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006a_guard_protocol_predecessor() RETURNS TRIGGER AS $$
    BEGIN IF NEW.predecessor_version_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM public.gdss_validation_protocol_version p WHERE p.id=NEW.predecessor_version_id AND p.protocol_identity_id=NEW.protocol_identity_id AND p.version_number<NEW.version_number) THEN RAISE EXCEPTION 'Validation protocol predecessor mismatch'; END IF; RETURN NEW; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006a_guard_protocol_event() RETURNS TRIGGER AS $$
    DECLARE prior_sequence INTEGER; prior_status TEXT; expected_hash TEXT;
    BEGIN
      SELECT sequence,to_status INTO prior_sequence,prior_status FROM public.gdss_validation_protocol_lifecycle_event WHERE protocol_version_id=NEW.protocol_version_id ORDER BY sequence DESC LIMIT 1 FOR UPDATE;
      IF prior_sequence IS NULL THEN IF NEW.sequence<>1 OR NEW.from_status IS NOT NULL OR NEW.to_status<>'DRAFT' THEN RAISE EXCEPTION 'Invalid protocol initial lifecycle'; END IF;
      ELSIF NEW.sequence<>prior_sequence+1 OR NEW.from_status IS DISTINCT FROM prior_status OR NOT((prior_status='DRAFT' AND NEW.to_status='REVIEW_REQUIRED') OR (prior_status='REVIEW_REQUIRED' AND NEW.to_status IN ('DRAFT','APPROVED')) OR (prior_status='APPROVED' AND NEW.to_status='SEALED') OR (prior_status='SEALED' AND NEW.to_status IN ('SUPERSEDED','INVALIDATED'))) THEN RAISE EXCEPTION 'Illegal validation protocol transition'; END IF;
      IF NEW.to_status='SEALED' THEN
        SELECT encode(digest(convert_to('gdss006:validation-protocol:v1','UTF8')||decode('00','hex')||convert_to(canonical_content,'UTF8'),'sha256'),'hex') INTO expected_hash FROM public.gdss_validation_protocol_version WHERE id=NEW.protocol_version_id;
        IF NEW.resulting_content_hash IS NULL OR NEW.resulting_content_hash<>expected_hash THEN RAISE EXCEPTION 'Validation protocol hash mismatch'; END IF;
      END IF;
      UPDATE public.gdss_validation_protocol_version SET status=NEW.to_status,content_hash=CASE WHEN NEW.to_status='SEALED' THEN NEW.resulting_content_hash ELSE content_hash END,
        approved_by=CASE WHEN NEW.to_status='APPROVED' THEN NEW.actor ELSE approved_by END,approved_at=CASE WHEN NEW.to_status='APPROVED' THEN clock_timestamp() ELSE approved_at END,
        sealed_by=CASE WHEN NEW.to_status='SEALED' THEN NEW.actor ELSE sealed_by END,sealed_at=CASE WHEN NEW.to_status='SEALED' THEN clock_timestamp() ELSE sealed_at END,
        superseded_by=CASE WHEN NEW.to_status='SUPERSEDED' THEN NEW.actor ELSE superseded_by END,superseded_at=CASE WHEN NEW.to_status='SUPERSEDED' THEN clock_timestamp() ELSE superseded_at END,
        invalidated_by=CASE WHEN NEW.to_status='INVALIDATED' THEN NEW.actor ELSE invalidated_by END,invalidated_at=CASE WHEN NEW.to_status='INVALIDATED' THEN clock_timestamp() ELSE invalidated_at END WHERE id=NEW.protocol_version_id;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_gdss006a_domain_event BEFORE INSERT ON public.gdss_validity_domain_lifecycle_event FOR EACH ROW EXECUTE FUNCTION public.gdss006a_guard_domain_event();
    CREATE TRIGGER trg_gdss006a_domain_predecessor BEFORE INSERT OR UPDATE ON public.gdss_validity_domain_version FOR EACH ROW EXECUTE FUNCTION public.gdss006a_guard_domain_predecessor();
    CREATE TRIGGER trg_gdss006a_protocol_binding BEFORE INSERT OR UPDATE ON public.gdss_validation_protocol_version FOR EACH ROW EXECUTE FUNCTION public.gdss006a_guard_protocol_binding();
    CREATE TRIGGER trg_gdss006a_protocol_predecessor BEFORE INSERT OR UPDATE ON public.gdss_validation_protocol_version FOR EACH ROW EXECUTE FUNCTION public.gdss006a_guard_protocol_predecessor();
    CREATE TRIGGER trg_gdss006a_protocol_event BEFORE INSERT ON public.gdss_validation_protocol_lifecycle_event FOR EACH ROW EXECUTE FUNCTION public.gdss006a_guard_protocol_event();
    CREATE TRIGGER trg_gdss006a_domain_version_guard BEFORE UPDATE OR DELETE ON public.gdss_validity_domain_version FOR EACH ROW EXECUTE FUNCTION public.gdss006a_guard_domain_content();
    CREATE TRIGGER trg_gdss006a_predicate_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_domain_predicate FOR EACH ROW EXECUTE FUNCTION public.gdss006a_guard_domain_content();
    CREATE TRIGGER trg_gdss006a_boundary_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_domain_boundary FOR EACH ROW EXECUTE FUNCTION public.gdss006a_guard_domain_content();
    CREATE TRIGGER trg_gdss006a_protocol_version_guard BEFORE UPDATE OR DELETE ON public.gdss_validation_protocol_version FOR EACH ROW EXECUTE FUNCTION public.gdss006a_guard_protocol_content();
    CREATE TRIGGER trg_gdss006a_target_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_validation_target FOR EACH ROW EXECUTE FUNCTION public.gdss006a_guard_protocol_content();
    CREATE TRIGGER trg_gdss006a_horizon_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_validation_horizon FOR EACH ROW EXECUTE FUNCTION public.gdss006a_guard_protocol_content();
    CREATE TRIGGER trg_gdss006a_criterion_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_validation_acceptance_criterion FOR EACH ROW EXECUTE FUNCTION public.gdss006a_guard_protocol_content();
    CREATE TRIGGER trg_gdss006a_policy_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_validation_policy FOR EACH ROW EXECUTE FUNCTION public.gdss006a_guard_protocol_content();
    CREATE TRIGGER trg_gdss006a_trigger_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_validation_revalidation_trigger FOR EACH ROW EXECUTE FUNCTION public.gdss006a_guard_protocol_content();
    CREATE TRIGGER trg_gdss006a_domain_identity_guard BEFORE UPDATE OR DELETE ON public.gdss_validity_domain_identity FOR EACH ROW EXECUTE FUNCTION public.gdss006a_reject_mutation();
    CREATE TRIGGER trg_gdss006a_protocol_identity_guard BEFORE UPDATE OR DELETE ON public.gdss_validation_protocol_identity FOR EACH ROW EXECUTE FUNCTION public.gdss006a_reject_mutation();
    CREATE TRIGGER trg_gdss006a_domain_history_guard BEFORE UPDATE OR DELETE ON public.gdss_validity_domain_lifecycle_event FOR EACH ROW EXECUTE FUNCTION public.gdss006a_reject_mutation();
    CREATE TRIGGER trg_gdss006a_protocol_history_guard BEFORE UPDATE OR DELETE ON public.gdss_validation_protocol_lifecycle_event FOR EACH ROW EXECUTE FUNCTION public.gdss006a_reject_mutation();
    CREATE INDEX gdss_validity_domain_state_idx ON public.gdss_validity_domain_version(domain_identity_id,status);
    CREATE INDEX gdss_validation_protocol_state_idx ON public.gdss_validation_protocol_version(protocol_identity_id,status);
    CREATE INDEX gdss_validation_protocol_model_idx ON public.gdss_validation_protocol_version(model_version_id);
    CREATE INDEX gdss_validation_protocol_domain_idx ON public.gdss_validation_protocol_version(validity_domain_version_id);
    """)


def downgrade():
    op.execute(r"""
    DROP TABLE public.gdss_validation_protocol_lifecycle_event;
    DROP TABLE public.gdss_validation_revalidation_trigger;
    DROP TABLE public.gdss_validation_policy;
    DROP TABLE public.gdss_validation_acceptance_criterion;
    DROP TABLE public.gdss_validation_horizon;
    DROP TABLE public.gdss_validation_target;
    DROP TABLE public.gdss_validation_protocol_version;
    DROP TABLE public.gdss_validation_protocol_identity;
    DROP TABLE public.gdss_validity_domain_lifecycle_event;
    DROP TABLE public.gdss_domain_boundary;
    DROP TABLE public.gdss_domain_predicate;
    DROP TABLE public.gdss_validity_domain_version;
    DROP TABLE public.gdss_validity_domain_identity;
    DROP FUNCTION IF EXISTS public.gdss006a_guard_protocol_event();
    DROP FUNCTION IF EXISTS public.gdss006a_guard_protocol_predecessor();
    DROP FUNCTION IF EXISTS public.gdss006a_guard_protocol_binding();
    DROP FUNCTION IF EXISTS public.gdss006a_guard_domain_predecessor();
    DROP FUNCTION IF EXISTS public.gdss006a_guard_domain_event();
    DROP FUNCTION IF EXISTS public.gdss006a_guard_protocol_content();
    DROP FUNCTION IF EXISTS public.gdss006a_guard_domain_content();
    DROP FUNCTION IF EXISTS public.gdss006a_reject_mutation();
    """)
