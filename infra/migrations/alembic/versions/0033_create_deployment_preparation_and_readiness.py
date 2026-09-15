"""Create immutable deployment preparation and operational readiness evidence.

Revision ID: 0033
Revises: 0032
"""
from alembic import op

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE public.control_controlled_deployment_preparations (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      policy_version_candidate_id UUID NOT NULL REFERENCES public.control_controlled_policy_version_candidates(id) ON DELETE RESTRICT,
      target_asset_id UUID NOT NULL REFERENCES public.assets(id) ON DELETE RESTRICT, target_scope_kind TEXT NOT NULL CHECK(target_scope_kind='asset'),
      policy_version_hash TEXT NOT NULL CHECK(policy_version_hash ~ '^[0-9a-f]{64}$'), validation_id UUID NOT NULL REFERENCES public.control_controlled_policy_validations(id) ON DELETE RESTRICT, validation_hash TEXT NOT NULL CHECK(validation_hash ~ '^[0-9a-f]{64}$'),
      approval_id UUID NOT NULL REFERENCES public.control_controlled_policy_approvals(id) ON DELETE RESTRICT, approval_hash TEXT NOT NULL CHECK(approval_hash ~ '^[0-9a-f]{64}$'),
      strategy_type TEXT NOT NULL CHECK(strategy_type IN ('proportional','threshold')), strategy_schema_version INTEGER NOT NULL CHECK(strategy_schema_version>0), version_number INTEGER NOT NULL CHECK(version_number>0),
      preparation_hash TEXT NOT NULL CHECK(preparation_hash ~ '^[0-9a-f]{64}$'), preparation_policy_version TEXT NOT NULL CHECK(preparation_policy_version='controlled-deployment-preparation:v1'), preparation_schema_version TEXT NOT NULL CHECK(preparation_schema_version='controlled-deployment-preparation-schema:v1'),
      status TEXT NOT NULL CHECK(status='CREATED'), created_by TEXT NOT NULL CHECK(btrim(created_by)<>''), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK(physical_effects_allowed=FALSE),
      UNIQUE(project_id,policy_version_candidate_id,target_asset_id,preparation_policy_version), UNIQUE(project_id,preparation_hash))""")
    op.execute("""CREATE TABLE public.control_operational_readiness_assessments (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      deployment_preparation_id UUID NOT NULL REFERENCES public.control_controlled_deployment_preparations(id) ON DELETE RESTRICT,
      preparation_hash TEXT NOT NULL CHECK(preparation_hash ~ '^[0-9a-f]{64}$'), readiness_hash TEXT NOT NULL CHECK(readiness_hash ~ '^[0-9a-f]{64}$'),
      readiness_policy_version TEXT NOT NULL CHECK(readiness_policy_version='operational-readiness:v1'), readiness_engine_version TEXT NOT NULL CHECK(readiness_engine_version='operational-readiness-engine:v1'),
      status TEXT NOT NULL CHECK(status IN('PENDING','PASSED','FAILED','BLOCKED')), blocking_pass_count INTEGER NOT NULL CHECK(blocking_pass_count>=0), blocking_fail_count INTEGER NOT NULL CHECK(blocking_fail_count>=0), warning_count INTEGER NOT NULL DEFAULT 0 CHECK(warning_count>=0),
      schema_version INTEGER NOT NULL CHECK(schema_version=1), created_by TEXT NOT NULL CHECK(btrim(created_by)<>''), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK(physical_effects_allowed=FALSE),
      UNIQUE(project_id,deployment_preparation_id,readiness_policy_version), UNIQUE(project_id,readiness_hash))""")
    op.execute("""CREATE TABLE public.control_operational_readiness_gate_results (
      assessment_id UUID NOT NULL REFERENCES public.control_operational_readiness_assessments(id) ON DELETE RESTRICT,
      gate_code TEXT NOT NULL CHECK(gate_code IN ('GATE_M7_3_APPROVAL_VALID','GATE_POLICY_VERSION_IDENTITY_VALID','GATE_PREPARATION_PROVENANCE_COMPLETE','GATE_TARGET_SCOPE_VALID','GATE_TARGET_TOPOLOGY_EXISTS','GATE_TARGET_COMPATIBILITY_VALID','GATE_REQUIRED_RUNTIME_CAPABILITIES_DECLARED','GATE_SECURITY_BOUNDARY_VALID','GATE_NO_CONFLICTING_ACTIVE_BINDING','GATE_ROLLBACK_PRECONDITIONS_DEFINED','GATE_OBSERVABILITY_PRECONDITIONS_DEFINED','GATE_NO_DEPLOYMENT_EXECUTED')),
      gate_version TEXT NOT NULL CHECK(gate_version='v1'), status TEXT NOT NULL CHECK(status IN('PASS','FAIL','ERROR')), severity TEXT NOT NULL CHECK(severity='BLOCKING'), reason_code TEXT NOT NULL, details JSONB NOT NULL, evidence_reference JSONB NOT NULL,
      PRIMARY KEY(assessment_id,gate_code))""")
    op.execute("""CREATE OR REPLACE FUNCTION public.enforce_controlled_deployment_readiness_immutable() RETURNS TRIGGER AS $$ BEGIN RAISE EXCEPTION 'controlled deployment preparation and readiness evidence is immutable'; END; $$ LANGUAGE plpgsql""")
    for table in ['control_controlled_deployment_preparations','control_operational_readiness_assessments','control_operational_readiness_gate_results']:
        op.execute(f"CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE ON public.{table} FOR EACH ROW EXECUTE FUNCTION public.enforce_controlled_deployment_readiness_immutable()")


def downgrade() -> None:
    for table in ['control_operational_readiness_gate_results','control_operational_readiness_assessments','control_controlled_deployment_preparations']:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable ON public.{table}")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_controlled_deployment_readiness_immutable()")
    op.execute("DROP TABLE IF EXISTS public.control_operational_readiness_gate_results")
    op.execute("DROP TABLE IF EXISTS public.control_operational_readiness_assessments")
    op.execute("DROP TABLE IF EXISTS public.control_controlled_deployment_preparations")
