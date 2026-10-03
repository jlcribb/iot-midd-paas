"""Governed dynamic simulation runtime foundation. Revision 0041."""
from alembic import op

revision = "0041"
down_revision = "0040"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r"""
    CREATE TABLE public.gdss_dynamic_binding (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      canonical_name TEXT NOT NULL,
      description TEXT NOT NULL DEFAULT '',
      created_by TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(project_id, canonical_name)
    );
    CREATE TABLE public.gdss_dynamic_binding_version (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      binding_id UUID NOT NULL REFERENCES public.gdss_dynamic_binding(id) ON DELETE RESTRICT,
      version_number INTEGER NOT NULL CHECK(version_number > 0),
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT,
      predecessor_version_id UUID NULL REFERENCES public.gdss_dynamic_binding_version(id) ON DELETE RESTRICT,
      dynamic_semantic_version TEXT NOT NULL CHECK(dynamic_semantic_version = 'DETERMINISTIC_CONTINUOUS_TIME_V1'),
      content JSONB NOT NULL,
      canonical_content TEXT NOT NULL,
      dynamic_binding_hash CHAR(64) NOT NULL CHECK(dynamic_binding_hash ~ '^[0-9a-f]{64}$'),
      created_by TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(binding_id, version_number), UNIQUE(binding_id, dynamic_binding_hash), UNIQUE(id, model_version_id)
    );
    CREATE TABLE public.gdss_dynamic_binding_lifecycle_event (
      id BIGSERIAL PRIMARY KEY,
      binding_version_id UUID NOT NULL REFERENCES public.gdss_dynamic_binding_version(id) ON DELETE RESTRICT,
      sequence INTEGER NOT NULL CHECK(sequence > 0),
      from_status TEXT NULL CHECK(from_status IS NULL OR from_status IN ('DRAFT','PUBLISHED','DEPRECATED')),
      to_status TEXT NOT NULL CHECK(to_status IN ('DRAFT','PUBLISHED','DEPRECATED')),
      actor TEXT NOT NULL, reason TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(binding_version_id, sequence)
    );
    CREATE TABLE public.gdss_simulation_attempt (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT,
      binding_version_id UUID NOT NULL REFERENCES public.gdss_dynamic_binding_version(id) ON DELETE RESTRICT,
      simulation_input_manifest JSONB NOT NULL,
      simulation_input_hash CHAR(64) NOT NULL CHECK(simulation_input_hash ~ '^[0-9a-f]{64}$'),
      requested_by TEXT NOT NULL,
      idempotency_key TEXT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE UNIQUE INDEX gdss_simulation_attempt_idempotency_uq ON public.gdss_simulation_attempt(project_id,idempotency_key) WHERE idempotency_key IS NOT NULL;
    CREATE TABLE public.gdss_simulation_artifact (
      hash CHAR(64) PRIMARY KEY CHECK(hash ~ '^[0-9a-f]{64}$'),
      media_type TEXT NOT NULL CHECK(media_type = 'application/vnd.midd.gdss-trajectory+ndjson;version=1'),
      format_version TEXT NOT NULL CHECK(format_version = 'GDSS_TRAJECTORY_NDJSON_V1'),
      byte_length INTEGER NOT NULL CHECK(byte_length BETWEEN 1 AND 16777216),
      payload BYTEA NOT NULL,
      point_count INTEGER NOT NULL CHECK(point_count BETWEEN 1 AND 10001),
      completeness TEXT NOT NULL CHECK(completeness IN ('COMPLETE','PARTIAL')),
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      CHECK(octet_length(payload) = byte_length)
    );
    CREATE TABLE public.gdss_simulation_execution_event (
      id BIGSERIAL PRIMARY KEY,
      attempt_id UUID NOT NULL REFERENCES public.gdss_simulation_attempt(id) ON DELETE RESTRICT,
      sequence INTEGER NOT NULL CHECK(sequence > 0),
      status TEXT NOT NULL CHECK(status IN ('RUNNING','COMPLETED','FAILED','ABORTED')),
      termination_reason TEXT NULL,
      simulation_result_hash CHAR(64) NULL CHECK(simulation_result_hash IS NULL OR simulation_result_hash ~ '^[0-9a-f]{64}$'),
      trajectory_hash CHAR(64) NULL REFERENCES public.gdss_simulation_artifact(hash) ON DELETE RESTRICT,
      trajectory_completeness TEXT NULL CHECK(trajectory_completeness IS NULL OR trajectory_completeness IN ('COMPLETE','PARTIAL')),
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(attempt_id, sequence)
    );
    CREATE TABLE public.gdss_simulation_diagnostic (
      id BIGSERIAL PRIMARY KEY,
      attempt_id UUID NOT NULL REFERENCES public.gdss_simulation_attempt(id) ON DELETE RESTRICT,
      sequence INTEGER NOT NULL CHECK(sequence > 0 AND sequence <= 256),
      code TEXT NOT NULL,
      severity TEXT NOT NULL CHECK(severity IN ('ERROR','WARNING','INFO')),
      stage TEXT NOT NULL,
      step_index INTEGER NULL CHECK(step_index IS NULL OR step_index >= 0),
      state_ref TEXT NULL, rate_ref TEXT NULL, formula_ref TEXT NULL,
      details JSONB NOT NULL DEFAULT '{}', message TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(attempt_id, sequence)
    );

    CREATE FUNCTION public.gdss_simulation_reject_mutation() RETURNS TRIGGER AS $$
    BEGIN RAISE EXCEPTION 'GDSS-003 evidence is append-only'; END; $$ LANGUAGE plpgsql;
    CREATE TRIGGER gdss_dynamic_binding_append_only BEFORE UPDATE OR DELETE ON public.gdss_dynamic_binding FOR EACH ROW EXECUTE FUNCTION public.gdss_simulation_reject_mutation();
    CREATE TRIGGER gdss_dynamic_binding_version_append_only BEFORE UPDATE OR DELETE ON public.gdss_dynamic_binding_version FOR EACH ROW EXECUTE FUNCTION public.gdss_simulation_reject_mutation();
    CREATE TRIGGER gdss_dynamic_binding_lifecycle_append_only BEFORE UPDATE OR DELETE ON public.gdss_dynamic_binding_lifecycle_event FOR EACH ROW EXECUTE FUNCTION public.gdss_simulation_reject_mutation();
    CREATE TRIGGER gdss_simulation_attempt_append_only BEFORE UPDATE OR DELETE ON public.gdss_simulation_attempt FOR EACH ROW EXECUTE FUNCTION public.gdss_simulation_reject_mutation();
    CREATE TRIGGER gdss_simulation_artifact_append_only BEFORE UPDATE OR DELETE ON public.gdss_simulation_artifact FOR EACH ROW EXECUTE FUNCTION public.gdss_simulation_reject_mutation();
    CREATE TRIGGER gdss_simulation_execution_event_append_only BEFORE UPDATE OR DELETE ON public.gdss_simulation_execution_event FOR EACH ROW EXECUTE FUNCTION public.gdss_simulation_reject_mutation();
    CREATE TRIGGER gdss_simulation_diagnostic_append_only BEFORE UPDATE OR DELETE ON public.gdss_simulation_diagnostic FOR EACH ROW EXECUTE FUNCTION public.gdss_simulation_reject_mutation();

    CREATE FUNCTION public.gdss_dynamic_binding_version_guard() RETURNS TRIGGER AS $$
    DECLARE binding_project UUID; model_project UUID; predecessor_binding UUID;
    BEGIN
      SELECT project_id INTO binding_project FROM public.gdss_dynamic_binding WHERE id=NEW.binding_id;
      SELECT i.project_id INTO model_project FROM public.gdss_version v JOIN public.gdss_identity i ON i.id=v.identity_id WHERE v.id=NEW.model_version_id;
      IF binding_project IS DISTINCT FROM model_project THEN RAISE EXCEPTION 'GDSS binding/model project mismatch'; END IF;
      IF NEW.predecessor_version_id IS NOT NULL THEN
        SELECT binding_id INTO predecessor_binding FROM public.gdss_dynamic_binding_version WHERE id=NEW.predecessor_version_id;
        IF predecessor_binding IS DISTINCT FROM NEW.binding_id THEN RAISE EXCEPTION 'GDSS predecessor binding mismatch'; END IF;
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE TRIGGER gdss_dynamic_binding_version_validate BEFORE INSERT ON public.gdss_dynamic_binding_version FOR EACH ROW EXECUTE FUNCTION public.gdss_dynamic_binding_version_guard();

    CREATE FUNCTION public.gdss_binding_lifecycle_guard() RETURNS TRIGGER AS $$
    DECLARE last_sequence INTEGER; last_status TEXT;
    BEGIN
      SELECT sequence,to_status INTO last_sequence,last_status FROM public.gdss_dynamic_binding_lifecycle_event WHERE binding_version_id=NEW.binding_version_id ORDER BY sequence DESC LIMIT 1 FOR UPDATE;
      IF last_sequence IS NULL THEN
        IF NEW.sequence<>1 OR NEW.from_status IS NOT NULL OR NEW.to_status<>'DRAFT' THEN RAISE EXCEPTION 'GDSS lifecycle must begin NULL to DRAFT'; END IF;
      ELSE
        IF NEW.sequence<>last_sequence+1 OR NEW.from_status IS DISTINCT FROM last_status OR NOT ((last_status='DRAFT' AND NEW.to_status='PUBLISHED') OR (last_status='PUBLISHED' AND NEW.to_status='DEPRECATED')) THEN RAISE EXCEPTION 'GDSS illegal binding lifecycle transition'; END IF;
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE TRIGGER gdss_binding_lifecycle_validate BEFORE INSERT ON public.gdss_dynamic_binding_lifecycle_event FOR EACH ROW EXECUTE FUNCTION public.gdss_binding_lifecycle_guard();

    CREATE FUNCTION public.gdss_simulation_attempt_guard() RETURNS TRIGGER AS $$
    DECLARE binding_project UUID; binding_model UUID; binding_status TEXT;
    BEGIN
      SELECT b.project_id,v.model_version_id INTO binding_project,binding_model FROM public.gdss_dynamic_binding_version v JOIN public.gdss_dynamic_binding b ON b.id=v.binding_id WHERE v.id=NEW.binding_version_id;
      SELECT to_status INTO binding_status FROM public.gdss_dynamic_binding_lifecycle_event WHERE binding_version_id=NEW.binding_version_id ORDER BY sequence DESC LIMIT 1;
      IF binding_project IS DISTINCT FROM NEW.project_id OR binding_model IS DISTINCT FROM NEW.model_version_id OR binding_status IS DISTINCT FROM 'PUBLISHED' THEN RAISE EXCEPTION 'GDSS attempt ownership or publication mismatch'; END IF;
      IF NEW.simulation_input_manifest->>'unitConversionCatalogVersion' IS DISTINCT FROM 'GDSS_UNIT_CONVERSION_V2' THEN RAISE EXCEPTION 'GDSS-003 requires unit catalog V2'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE TRIGGER gdss_simulation_attempt_validate BEFORE INSERT ON public.gdss_simulation_attempt FOR EACH ROW EXECUTE FUNCTION public.gdss_simulation_attempt_guard();

    CREATE FUNCTION public.gdss_simulation_event_guard() RETURNS TRIGGER AS $$
    DECLARE previous_status TEXT; previous_sequence INTEGER; artifact_kind TEXT;
    BEGIN
      SELECT sequence,status INTO previous_sequence,previous_status FROM public.gdss_simulation_execution_event WHERE attempt_id=NEW.attempt_id ORDER BY sequence DESC LIMIT 1 FOR UPDATE;
      IF previous_sequence IS NULL THEN
        IF NEW.sequence<>1 OR NEW.status<>'RUNNING' OR NEW.termination_reason IS NOT NULL OR NEW.simulation_result_hash IS NOT NULL OR NEW.trajectory_hash IS NOT NULL THEN RAISE EXCEPTION 'GDSS first execution event must be RUNNING'; END IF;
      ELSE
        IF previous_sequence<>1 OR previous_status<>'RUNNING' OR NEW.sequence<>2 OR NEW.status NOT IN ('COMPLETED','FAILED','ABORTED') OR NEW.simulation_result_hash IS NULL THEN RAISE EXCEPTION 'GDSS exactly one terminal event required'; END IF;
        IF NEW.trajectory_hash IS NOT NULL THEN SELECT completeness INTO artifact_kind FROM public.gdss_simulation_artifact WHERE hash=NEW.trajectory_hash; IF artifact_kind IS DISTINCT FROM NEW.trajectory_completeness THEN RAISE EXCEPTION 'GDSS artifact completeness mismatch'; END IF; END IF;
        IF NEW.status='COMPLETED' AND (NEW.termination_reason IS DISTINCT FROM 'END_TIME_REACHED' OR NEW.trajectory_hash IS NULL OR NEW.trajectory_completeness IS DISTINCT FROM 'COMPLETE') THEN RAISE EXCEPTION 'GDSS completed event requires complete end-time artifact'; END IF;
        IF NEW.status='FAILED' AND NEW.trajectory_hash IS NOT NULL AND NEW.trajectory_completeness IS DISTINCT FROM 'PARTIAL' THEN RAISE EXCEPTION 'GDSS failed artifact must be partial'; END IF;
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE TRIGGER gdss_simulation_execution_event_validate BEFORE INSERT ON public.gdss_simulation_execution_event FOR EACH ROW EXECUTE FUNCTION public.gdss_simulation_event_guard();

    CREATE INDEX gdss_dynamic_binding_project_idx ON public.gdss_dynamic_binding(project_id,canonical_name);
    CREATE INDEX gdss_dynamic_binding_version_order_idx ON public.gdss_dynamic_binding_version(binding_id,version_number);
    CREATE INDEX gdss_simulation_attempt_project_created_idx ON public.gdss_simulation_attempt(project_id,created_at);
    CREATE INDEX gdss_simulation_attempt_input_hash_idx ON public.gdss_simulation_attempt(simulation_input_hash);
    CREATE INDEX gdss_simulation_event_attempt_idx ON public.gdss_simulation_execution_event(attempt_id,sequence);
    CREATE INDEX gdss_simulation_diagnostic_attempt_idx ON public.gdss_simulation_diagnostic(attempt_id,sequence);
    """)

def downgrade():
    op.execute(r"""
    DROP TABLE public.gdss_simulation_diagnostic;
    DROP TABLE public.gdss_simulation_execution_event;
    DROP TABLE public.gdss_simulation_artifact;
    DROP TABLE public.gdss_simulation_attempt;
    DROP TABLE public.gdss_dynamic_binding_lifecycle_event;
    DROP TABLE public.gdss_dynamic_binding_version;
    DROP TABLE public.gdss_dynamic_binding;
    DROP FUNCTION public.gdss_simulation_event_guard();
    DROP FUNCTION public.gdss_simulation_attempt_guard();
    DROP FUNCTION public.gdss_binding_lifecycle_guard();
    DROP FUNCTION public.gdss_dynamic_binding_version_guard();
    DROP FUNCTION public.gdss_simulation_reject_mutation();
    """)
