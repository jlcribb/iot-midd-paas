"""Create immutable governed deployment authorization and intent evidence.

Revision ID: 0034
Revises: 0033
"""
from alembic import op
revision="0034"
down_revision="0033"
branch_labels=None
depends_on=None

def upgrade() -> None:
    op.execute("""CREATE TABLE public.control_governed_deployment_authorizations (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      policy_version_candidate_id UUID NOT NULL REFERENCES public.control_controlled_policy_version_candidates(id) ON DELETE RESTRICT,
      deployment_preparation_id UUID NOT NULL REFERENCES public.control_controlled_deployment_preparations(id) ON DELETE RESTRICT,
      readiness_assessment_id UUID NOT NULL REFERENCES public.control_operational_readiness_assessments(id) ON DELETE RESTRICT,
      policy_version_hash TEXT NOT NULL CHECK(policy_version_hash ~ '^[0-9a-f]{64}$'), validation_hash TEXT NOT NULL CHECK(validation_hash ~ '^[0-9a-f]{64}$'), approval_hash TEXT NOT NULL CHECK(approval_hash ~ '^[0-9a-f]{64}$'), preparation_hash TEXT NOT NULL CHECK(preparation_hash ~ '^[0-9a-f]{64}$'), readiness_hash TEXT NOT NULL CHECK(readiness_hash ~ '^[0-9a-f]{64}$'),
      decision TEXT NOT NULL CHECK(decision IN('AUTHORIZE_CONTROLLED_DEPLOYMENT_INTENT','REJECT_DEPLOYMENT','REQUEST_READINESS_REASSESSMENT')),
      rationale TEXT NOT NULL CHECK(btrim(rationale)<>''), authorizer_id TEXT NOT NULL CHECK(btrim(authorizer_id)<>''), authorization_hash TEXT NOT NULL CHECK(authorization_hash ~ '^[0-9a-f]{64}$'), authorization_policy_version TEXT NOT NULL CHECK(authorization_policy_version='governed-deployment-authorization:v1'), authorization_schema_version TEXT NOT NULL CHECK(authorization_schema_version='governed-deployment-authorization-schema:v1'), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK(physical_effects_allowed=FALSE),
      UNIQUE(readiness_assessment_id), UNIQUE(project_id,authorization_hash))""")
    op.execute("""CREATE TABLE public.control_governed_deployment_intents (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      policy_version_candidate_id UUID NOT NULL REFERENCES public.control_controlled_policy_version_candidates(id) ON DELETE RESTRICT,
      deployment_preparation_id UUID NOT NULL REFERENCES public.control_controlled_deployment_preparations(id) ON DELETE RESTRICT,
      readiness_assessment_id UUID NOT NULL REFERENCES public.control_operational_readiness_assessments(id) ON DELETE RESTRICT,
      authorization_id UUID NOT NULL REFERENCES public.control_governed_deployment_authorizations(id) ON DELETE RESTRICT, target_asset_id UUID NOT NULL REFERENCES public.assets(id) ON DELETE RESTRICT,
      policy_version_hash TEXT NOT NULL CHECK(policy_version_hash ~ '^[0-9a-f]{64}$'), preparation_hash TEXT NOT NULL CHECK(preparation_hash ~ '^[0-9a-f]{64}$'), readiness_hash TEXT NOT NULL CHECK(readiness_hash ~ '^[0-9a-f]{64}$'), authorization_hash TEXT NOT NULL CHECK(authorization_hash ~ '^[0-9a-f]{64}$'), strategy_type TEXT NOT NULL CHECK(strategy_type IN('proportional','threshold')), version_number INTEGER NOT NULL CHECK(version_number>0),
      intent_hash TEXT NOT NULL CHECK(intent_hash ~ '^[0-9a-f]{64}$'), intent_policy_version TEXT NOT NULL CHECK(intent_policy_version='governed-deployment-intent:v1'), intent_schema_version TEXT NOT NULL CHECK(intent_schema_version='governed-deployment-intent-schema:v1'), status TEXT NOT NULL CHECK(status='CREATED'), created_by TEXT NOT NULL CHECK(btrim(created_by)<>''), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK(physical_effects_allowed=FALSE),
      UNIQUE(authorization_id), UNIQUE(project_id,intent_hash))""")
    op.execute("""CREATE OR REPLACE FUNCTION public.enforce_governed_deployment_authorization_immutable() RETURNS TRIGGER AS $$ BEGIN RAISE EXCEPTION 'governed deployment authorization and intent evidence is immutable'; END; $$ LANGUAGE plpgsql""")
    for table in ['control_governed_deployment_authorizations','control_governed_deployment_intents']:
      op.execute(f"CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE ON public.{table} FOR EACH ROW EXECUTE FUNCTION public.enforce_governed_deployment_authorization_immutable()")

def downgrade() -> None:
    for table in ['control_governed_deployment_intents','control_governed_deployment_authorizations']:
      op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable ON public.{table}")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_governed_deployment_authorization_immutable()")
    op.execute("DROP TABLE IF EXISTS public.control_governed_deployment_intents")
    op.execute("DROP TABLE IF EXISTS public.control_governed_deployment_authorizations")
