"""Create governed physical-actuation readiness and non-executable intent evidence.

Revision ID: 0038
Revises: 0037
"""

from alembic import op


revision = "0038"
down_revision = "0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE public.control_physical_actuation_readiness_assessments (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      binding_id UUID NOT NULL REFERENCES public.control_runtime_policy_bindings(id) ON DELETE RESTRICT,
      policy_version_candidate_id UUID NOT NULL REFERENCES public.control_controlled_policy_version_candidates(id) ON DELETE RESTRICT,
      runtime_target_asset_id UUID NOT NULL REFERENCES public.assets(id) ON DELETE RESTRICT,
      actuator_target_asset_id UUID NULL REFERENCES public.assets(id) ON DELETE RESTRICT,
      policy_version_hash TEXT NOT NULL CHECK(policy_version_hash ~ '^[0-9a-f]{64}$'),
      binding_snapshot_hash TEXT NOT NULL CHECK(binding_snapshot_hash ~ '^[0-9a-f]{64}$'),
      shadow_evidence_hash TEXT NOT NULL CHECK(shadow_evidence_hash ~ '^[0-9a-f]{64}$'),
      readiness_hash TEXT NOT NULL CHECK(readiness_hash ~ '^[0-9a-f]{64}$'),
      readiness_policy_version TEXT NOT NULL CHECK(readiness_policy_version = 'physical-actuation-readiness:v1'),
      readiness_engine_version TEXT NOT NULL CHECK(readiness_engine_version = 'physical-actuation-readiness-engine:v1'),
      readiness_schema_version TEXT NOT NULL CHECK(readiness_schema_version = 'physical-actuation-readiness-schema:v1'),
      status TEXT NOT NULL CHECK(status IN ('PENDING','PASSED','FAILED','BLOCKED')),
      created_by TEXT NOT NULL CHECK(btrim(created_by) <> ''),
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      physical_effects BOOLEAN NOT NULL DEFAULT FALSE CHECK(physical_effects = FALSE),
      actuation_enabled BOOLEAN NOT NULL DEFAULT FALSE CHECK(actuation_enabled = FALSE),
      UNIQUE(project_id, readiness_hash)
    )
    """)
    op.execute("""
    CREATE TABLE public.control_physical_actuation_readiness_gates (
      assessment_id UUID NOT NULL REFERENCES public.control_physical_actuation_readiness_assessments(id) ON DELETE RESTRICT,
      gate_code TEXT NOT NULL,
      position INTEGER NOT NULL CHECK(position > 0),
      status TEXT NOT NULL CHECK(status IN ('PASS','FAIL','ERROR')),
      reason_code TEXT NOT NULL,
      details JSONB NOT NULL CHECK(jsonb_typeof(details) = 'object'),
      PRIMARY KEY(assessment_id, gate_code),
      UNIQUE(assessment_id, position)
    )
    """)
    op.execute("""
    CREATE TABLE public.control_governed_physical_actuation_authorizations (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      readiness_id UUID NOT NULL UNIQUE REFERENCES public.control_physical_actuation_readiness_assessments(id) ON DELETE RESTRICT,
      binding_id UUID NOT NULL REFERENCES public.control_runtime_policy_bindings(id) ON DELETE RESTRICT,
      policy_version_hash TEXT NOT NULL CHECK(policy_version_hash ~ '^[0-9a-f]{64}$'),
      readiness_hash TEXT NOT NULL CHECK(readiness_hash ~ '^[0-9a-f]{64}$'),
      decision TEXT NOT NULL CHECK(decision IN ('AUTHORIZE_PHYSICAL_ACTUATION_INTENT','REJECT_PHYSICAL_ACTUATION','REQUEST_ACTUATION_REASSESSMENT')),
      rationale TEXT NOT NULL CHECK(btrim(rationale) <> '' AND length(btrim(rationale)) <= 2000),
      authorizer_id TEXT NOT NULL CHECK(btrim(authorizer_id) <> ''),
      authorization_hash TEXT NOT NULL CHECK(authorization_hash ~ '^[0-9a-f]{64}$'),
      authorization_policy_version TEXT NOT NULL CHECK(authorization_policy_version = 'governed-physical-actuation-authorization:v1'),
      authorization_schema_version TEXT NOT NULL CHECK(authorization_schema_version = 'governed-physical-actuation-authorization-schema:v1'),
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      physical_effects BOOLEAN NOT NULL DEFAULT FALSE CHECK(physical_effects = FALSE),
      actuation_enabled BOOLEAN NOT NULL DEFAULT FALSE CHECK(actuation_enabled = FALSE),
      UNIQUE(project_id, authorization_hash)
    )
    """)
    op.execute("""
    CREATE TABLE public.control_governed_actuation_intents (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      authorization_id UUID NOT NULL UNIQUE REFERENCES public.control_governed_physical_actuation_authorizations(id) ON DELETE RESTRICT,
      readiness_id UUID NOT NULL REFERENCES public.control_physical_actuation_readiness_assessments(id) ON DELETE RESTRICT,
      binding_id UUID NOT NULL REFERENCES public.control_runtime_policy_bindings(id) ON DELETE RESTRICT,
      policy_version_candidate_id UUID NOT NULL REFERENCES public.control_controlled_policy_version_candidates(id) ON DELETE RESTRICT,
      runtime_target_asset_id UUID NOT NULL REFERENCES public.assets(id) ON DELETE RESTRICT,
      actuator_target_asset_id UUID NOT NULL REFERENCES public.assets(id) ON DELETE RESTRICT,
      policy_version_hash TEXT NOT NULL CHECK(policy_version_hash ~ '^[0-9a-f]{64}$'),
      capability_identity TEXT NOT NULL CHECK(btrim(capability_identity) <> ''),
      control_output_schema TEXT NOT NULL CHECK(btrim(control_output_schema) <> ''),
      safety_limit_contract JSONB NOT NULL CHECK(jsonb_typeof(safety_limit_contract) = 'object'),
      interlock_contract JSONB NOT NULL CHECK(jsonb_typeof(interlock_contract) = 'object'),
      safe_state_contract JSONB NOT NULL CHECK(jsonb_typeof(safe_state_contract) = 'object'),
      intent_policy_version TEXT NOT NULL CHECK(intent_policy_version = 'governed-actuation-intent:v1'),
      intent_schema_version TEXT NOT NULL CHECK(intent_schema_version = 'governed-actuation-intent-schema:v1'),
      intent_type TEXT NOT NULL CHECK(intent_type = 'GOVERNED_PHYSICAL_ACTUATION_INTENT'),
      execution_mode TEXT NOT NULL CHECK(execution_mode = 'PROPOSED_ONLY'),
      non_executable BOOLEAN NOT NULL DEFAULT TRUE CHECK(non_executable = TRUE),
      intent_hash TEXT NOT NULL CHECK(intent_hash ~ '^[0-9a-f]{64}$'),
      created_by TEXT NOT NULL CHECK(btrim(created_by) <> ''),
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      physical_effects BOOLEAN NOT NULL DEFAULT FALSE CHECK(physical_effects = FALSE),
      actuation_enabled BOOLEAN NOT NULL DEFAULT FALSE CHECK(actuation_enabled = FALSE),
      UNIQUE(project_id, intent_hash)
    )
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION public.enforce_m79_project_integrity() RETURNS TRIGGER AS $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM public.control_runtime_policy_bindings b WHERE b.id = NEW.binding_id AND b.project_id = NEW.project_id)
        OR NOT EXISTS (SELECT 1 FROM public.assets a WHERE a.id = NEW.runtime_target_asset_id AND a.project_id = NEW.project_id)
        OR (NEW.actuator_target_asset_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public.assets a WHERE a.id = NEW.actuator_target_asset_id AND a.project_id = NEW.project_id)) THEN
        RAISE EXCEPTION 'M7.9 project/target integrity violation';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_m79_readiness_project_integrity BEFORE INSERT OR UPDATE ON public.control_physical_actuation_readiness_assessments FOR EACH ROW EXECUTE FUNCTION public.enforce_m79_project_integrity()")
    op.execute("""
    CREATE OR REPLACE FUNCTION public.enforce_m79_authorization_project_integrity() RETURNS TRIGGER AS $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM public.control_physical_actuation_readiness_assessments r WHERE r.id = NEW.readiness_id AND r.project_id = NEW.project_id AND r.binding_id = NEW.binding_id AND r.policy_version_hash = NEW.policy_version_hash AND r.readiness_hash = NEW.readiness_hash) THEN
        RAISE EXCEPTION 'M7.9 authorization project/provenance integrity violation';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_m79_authorization_project_integrity BEFORE INSERT OR UPDATE ON public.control_governed_physical_actuation_authorizations FOR EACH ROW EXECUTE FUNCTION public.enforce_m79_authorization_project_integrity()")
    op.execute("""
    CREATE OR REPLACE FUNCTION public.enforce_m79_intent_project_integrity() RETURNS TRIGGER AS $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM public.control_governed_physical_actuation_authorizations a WHERE a.id = NEW.authorization_id AND a.project_id = NEW.project_id)
        OR NOT EXISTS (SELECT 1 FROM public.control_physical_actuation_readiness_assessments r WHERE r.id = NEW.readiness_id AND r.project_id = NEW.project_id)
        OR NOT EXISTS (SELECT 1 FROM public.control_runtime_policy_bindings b WHERE b.id = NEW.binding_id AND b.project_id = NEW.project_id)
        OR NOT EXISTS (SELECT 1 FROM public.control_controlled_policy_version_candidates c WHERE c.id = NEW.policy_version_candidate_id AND c.project_id = NEW.project_id)
        OR NOT EXISTS (SELECT 1 FROM public.assets a WHERE a.id = NEW.runtime_target_asset_id AND a.project_id = NEW.project_id)
        OR NOT EXISTS (SELECT 1 FROM public.assets a WHERE a.id = NEW.actuator_target_asset_id AND a.project_id = NEW.project_id) THEN
        RAISE EXCEPTION 'M7.9 intent project/target integrity violation';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_m79_intent_project_integrity BEFORE INSERT OR UPDATE ON public.control_governed_actuation_intents FOR EACH ROW EXECUTE FUNCTION public.enforce_m79_intent_project_integrity()")
    op.execute("""
    CREATE OR REPLACE FUNCTION public.enforce_m79_immutable() RETURNS TRIGGER AS $$
    BEGIN RAISE EXCEPTION 'M7.9 historical evidence is immutable'; END; $$ LANGUAGE plpgsql
    """)
    for table in [
        'control_physical_actuation_readiness_assessments',
        'control_physical_actuation_readiness_gates',
        'control_governed_physical_actuation_authorizations',
        'control_governed_actuation_intents',
    ]:
        op.execute(f"CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE ON public.{table} FOR EACH ROW EXECUTE FUNCTION public.enforce_m79_immutable()")


def downgrade() -> None:
    for table in [
        'control_governed_actuation_intents',
        'control_governed_physical_actuation_authorizations',
        'control_physical_actuation_readiness_gates',
        'control_physical_actuation_readiness_assessments',
    ]:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable ON public.{table}")
    op.execute("DROP TRIGGER IF EXISTS trg_m79_intent_project_integrity ON public.control_governed_actuation_intents")
    op.execute("DROP TRIGGER IF EXISTS trg_m79_authorization_project_integrity ON public.control_governed_physical_actuation_authorizations")
    op.execute("DROP TRIGGER IF EXISTS trg_m79_readiness_project_integrity ON public.control_physical_actuation_readiness_assessments")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_m79_immutable()")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_m79_intent_project_integrity()")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_m79_authorization_project_integrity()")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_m79_project_integrity()")
    for table in [
        'control_governed_actuation_intents',
        'control_governed_physical_actuation_authorizations',
        'control_physical_actuation_readiness_gates',
        'control_physical_actuation_readiness_assessments',
    ]:
        op.execute(f"DROP TABLE IF EXISTS public.{table}")
