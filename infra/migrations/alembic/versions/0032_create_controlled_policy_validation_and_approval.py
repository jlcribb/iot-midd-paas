"""Create immutable controlled policy validation and approval evidence.

Revision ID: 0032
Revises: 0031
"""
from alembic import op

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE public.control_controlled_policy_validations (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      policy_version_candidate_id UUID NOT NULL REFERENCES public.control_controlled_policy_version_candidates(id) ON DELETE RESTRICT,
      policy_version_hash TEXT NOT NULL CHECK(policy_version_hash ~ '^[0-9a-f]{64}$'), validation_hash TEXT NOT NULL CHECK(validation_hash ~ '^[0-9a-f]{64}$'),
      validation_policy_version TEXT NOT NULL CHECK(validation_policy_version='controlled-policy-validation:v1'), validation_engine_version TEXT NOT NULL CHECK(validation_engine_version='controlled-policy-validation-engine:v1'),
      status TEXT NOT NULL CHECK(status IN('PENDING','PASSED','FAILED','BLOCKED')), blocking_pass_count INTEGER NOT NULL CHECK(blocking_pass_count >= 0), blocking_fail_count INTEGER NOT NULL CHECK(blocking_fail_count >= 0), warning_count INTEGER NOT NULL DEFAULT 0 CHECK(warning_count >= 0),
      schema_version INTEGER NOT NULL CHECK(schema_version=1), created_by TEXT NOT NULL CHECK(btrim(created_by)<>''), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK(physical_effects_allowed=FALSE),
      UNIQUE(project_id,policy_version_candidate_id,validation_policy_version))""")
    op.execute("""CREATE TABLE public.control_controlled_policy_validation_gate_results (
      validation_id UUID NOT NULL REFERENCES public.control_controlled_policy_validations(id) ON DELETE RESTRICT,
      gate_code TEXT NOT NULL CHECK(gate_code IN ('GATE_POLICY_CANDIDATE_IMMUTABLE','GATE_PROMOTION_ASSESSMENT_PASSED','GATE_CONFIGURATION_SCHEMA_VALID','GATE_CONFIGURATION_HASH_VALID','GATE_PROVENANCE_COMPLETE','GATE_VERSION_IDENTITY_VALID','GATE_PROJECT_SCOPE_VALID','GATE_NO_OPERATIONAL_BINDING')),
      gate_version TEXT NOT NULL CHECK(gate_version='v1'), status TEXT NOT NULL CHECK(status IN('PASS','FAIL','ERROR')), severity TEXT NOT NULL CHECK(severity='BLOCKING'), reason_code TEXT NOT NULL, details JSONB NOT NULL, evidence_reference JSONB NOT NULL,
      PRIMARY KEY(validation_id,gate_code))""")
    op.execute("""CREATE TABLE public.control_controlled_policy_approvals (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT, policy_version_candidate_id UUID NOT NULL REFERENCES public.control_controlled_policy_version_candidates(id) ON DELETE RESTRICT, validation_id UUID NOT NULL REFERENCES public.control_controlled_policy_validations(id) ON DELETE RESTRICT,
      validation_hash TEXT NOT NULL CHECK(validation_hash ~ '^[0-9a-f]{64}$'), decision TEXT NOT NULL CHECK(decision IN('APPROVE_FOR_CONTROLLED_DEPLOYMENT_PREPARATION','REJECT','REQUEST_REVALIDATION')), rationale TEXT NOT NULL CHECK(btrim(rationale)<>''), reviewer_id TEXT NOT NULL CHECK(btrim(reviewer_id)<>''),
      approval_hash TEXT NOT NULL CHECK(approval_hash ~ '^[0-9a-f]{64}$'), approval_policy_version TEXT NOT NULL CHECK(approval_policy_version='controlled-policy-approval:v1'), schema_version INTEGER NOT NULL CHECK(schema_version=1), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK(physical_effects_allowed=FALSE),
      UNIQUE(validation_id), UNIQUE(project_id,approval_hash))""")
    op.execute("""CREATE OR REPLACE FUNCTION public.enforce_controlled_policy_validation_immutable() RETURNS TRIGGER AS $$ BEGIN RAISE EXCEPTION 'controlled policy validation and approval evidence is immutable'; END; $$ LANGUAGE plpgsql""")
    for table in ['control_controlled_policy_validations','control_controlled_policy_validation_gate_results','control_controlled_policy_approvals']:
        op.execute(f"CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE ON public.{table} FOR EACH ROW EXECUTE FUNCTION public.enforce_controlled_policy_validation_immutable()")


def downgrade() -> None:
    for table in ['control_controlled_policy_approvals','control_controlled_policy_validation_gate_results','control_controlled_policy_validations']:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable ON public.{table}")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_controlled_policy_validation_immutable()")
    op.execute("DROP TABLE IF EXISTS public.control_controlled_policy_approvals")
    op.execute("DROP TABLE IF EXISTS public.control_controlled_policy_validation_gate_results")
    op.execute("DROP TABLE IF EXISTS public.control_controlled_policy_validations")
