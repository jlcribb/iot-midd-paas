"""Create governed non-active deployment execution and staging evidence.

Revision ID: 0035
Revises: 0034
"""
from alembic import op

revision = "0035"
down_revision = "0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE public.control_governed_deployment_executions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      policy_version_candidate_id UUID NOT NULL REFERENCES public.control_controlled_policy_version_candidates(id) ON DELETE RESTRICT,
      governed_deployment_intent_id UUID NOT NULL REFERENCES public.control_governed_deployment_intents(id) ON DELETE RESTRICT,
      target_asset_id UUID NOT NULL REFERENCES public.assets(id) ON DELETE RESTRICT,
      policy_version_hash TEXT NOT NULL CHECK(policy_version_hash ~ '^[0-9a-f]{64}$'),
      intent_hash TEXT NOT NULL CHECK(intent_hash ~ '^[0-9a-f]{64}$'),
      execution_hash TEXT NOT NULL CHECK(execution_hash ~ '^[0-9a-f]{64}$'),
      execution_policy_version TEXT NOT NULL CHECK(execution_policy_version='governed-deployment-execution:v1'),
      execution_engine_version TEXT NOT NULL CHECK(execution_engine_version='governed-deployment-execution-engine:v1'),
      execution_schema_version TEXT NOT NULL CHECK(execution_schema_version='governed-deployment-execution-schema:v1'),
      delivery_channel TEXT NOT NULL CHECK(delivery_channel='DATABASE_STAGING'),
      status TEXT NOT NULL CHECK(status IN('PENDING','RUNNING','SUCCEEDED','FAILED','BLOCKED','ROLLBACK_PENDING','ROLLED_BACK','ROLLBACK_FAILED')),
      rollback_status TEXT NOT NULL CHECK(rollback_status IN('NOT_REQUIRED','PENDING','SUCCEEDED','FAILED')),
      result_hash TEXT NULL CHECK(result_hash IS NULL OR result_hash ~ '^[0-9a-f]{64}$'),
      created_by TEXT NOT NULL CHECK(btrim(created_by)<>''),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), started_at TIMESTAMPTZ NULL, completed_at TIMESTAMPTZ NULL,
      physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK(physical_effects_allowed=FALSE),
      UNIQUE(governed_deployment_intent_id), UNIQUE(project_id, execution_hash)
    )
    """)
    op.execute("""
    CREATE UNIQUE INDEX uq_governed_deployment_execution_running_slot
    ON public.control_governed_deployment_executions(project_id,target_asset_id)
    WHERE status IN ('PENDING','RUNNING','ROLLBACK_PENDING')
    """)
    op.execute("""
    CREATE TABLE public.control_governed_deployment_execution_attempts (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      execution_id UUID NOT NULL REFERENCES public.control_governed_deployment_executions(id) ON DELETE RESTRICT,
      attempt_number INTEGER NOT NULL CHECK(attempt_number>0), delivery_channel TEXT NOT NULL CHECK(delivery_channel='DATABASE_STAGING'),
      target_asset_id UUID NOT NULL REFERENCES public.assets(id) ON DELETE RESTRICT,
      request_hash TEXT NOT NULL CHECK(request_hash ~ '^[0-9a-f]{64}$'),
      result_classification TEXT NOT NULL CHECK(result_classification IN('SUCCEEDED','FAILED','PARTIALLY_STAGED','BLOCKED')),
      acknowledgement JSONB NOT NULL, error_class TEXT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(execution_id,attempt_number)
    )
    """)
    op.execute("""
    CREATE TABLE public.control_governed_deployment_staged_artifacts (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), execution_id UUID NOT NULL UNIQUE REFERENCES public.control_governed_deployment_executions(id) ON DELETE RESTRICT,
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT, target_asset_id UUID NOT NULL REFERENCES public.assets(id) ON DELETE RESTRICT,
      policy_version_hash TEXT NOT NULL CHECK(policy_version_hash ~ '^[0-9a-f]{64}$'), artifact_hash TEXT NOT NULL CHECK(artifact_hash ~ '^[0-9a-f]{64}$'),
      status TEXT NOT NULL CHECK(status IN('STAGED','ROLLED_BACK')), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), rolled_back_at TIMESTAMPTZ NULL,
      physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK(physical_effects_allowed=FALSE)
    )
    """)
    op.execute("""
    CREATE TABLE public.control_governed_deployment_execution_results (
      execution_id UUID PRIMARY KEY REFERENCES public.control_governed_deployment_executions(id) ON DELETE RESTRICT,
      result_hash TEXT NOT NULL CHECK(result_hash ~ '^[0-9a-f]{64}$'), delivery_result JSONB NOT NULL, rollback_result JSONB NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """)
    op.execute("""
    CREATE OR REPLACE FUNCTION public.enforce_governed_deployment_execution_transition() RETURNS TRIGGER AS $$
    BEGIN
      IF NEW.governed_deployment_intent_id<>OLD.governed_deployment_intent_id OR NEW.project_id<>OLD.project_id OR NEW.policy_version_candidate_id<>OLD.policy_version_candidate_id OR NEW.target_asset_id<>OLD.target_asset_id OR NEW.policy_version_hash<>OLD.policy_version_hash OR NEW.intent_hash<>OLD.intent_hash OR NEW.execution_hash<>OLD.execution_hash OR NEW.execution_policy_version<>OLD.execution_policy_version OR NEW.execution_engine_version<>OLD.execution_engine_version OR NEW.execution_schema_version<>OLD.execution_schema_version OR NEW.delivery_channel<>OLD.delivery_channel OR NEW.created_by<>OLD.created_by OR NEW.created_at<>OLD.created_at OR NEW.physical_effects_allowed<>OLD.physical_effects_allowed THEN
        RAISE EXCEPTION 'governed deployment execution identity is immutable';
      END IF;
      IF OLD.status IN ('SUCCEEDED','BLOCKED','ROLLED_BACK','ROLLBACK_FAILED') OR (OLD.status='FAILED' AND OLD.rollback_status='NOT_REQUIRED') THEN RAISE EXCEPTION 'governed deployment execution terminal evidence is immutable'; END IF;
      IF OLD.status='PENDING' AND NEW.status NOT IN ('RUNNING','BLOCKED') THEN RAISE EXCEPTION 'illegal governed deployment execution transition'; END IF;
      IF OLD.status='RUNNING' AND NEW.status NOT IN ('SUCCEEDED','FAILED','BLOCKED') THEN RAISE EXCEPTION 'illegal governed deployment execution transition'; END IF;
      IF OLD.status='FAILED' AND NEW.status NOT IN ('ROLLBACK_PENDING') THEN RAISE EXCEPTION 'illegal governed deployment execution transition'; END IF;
      IF OLD.status='ROLLBACK_PENDING' AND NEW.status NOT IN ('ROLLED_BACK','ROLLBACK_FAILED') THEN RAISE EXCEPTION 'illegal governed deployment execution transition'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""CREATE TRIGGER trg_governed_deployment_execution_transition BEFORE UPDATE ON public.control_governed_deployment_executions FOR EACH ROW EXECUTE FUNCTION public.enforce_governed_deployment_execution_transition()""")
    op.execute("""
    CREATE OR REPLACE FUNCTION public.enforce_governed_deployment_execution_history_immutable() RETURNS TRIGGER AS $$
    BEGIN RAISE EXCEPTION 'governed deployment execution historical evidence is immutable'; END; $$ LANGUAGE plpgsql
    """)
    for table in ['control_governed_deployment_execution_attempts','control_governed_deployment_execution_results']:
        op.execute(f"CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE ON public.{table} FOR EACH ROW EXECUTE FUNCTION public.enforce_governed_deployment_execution_history_immutable()")
    op.execute("""
    CREATE OR REPLACE FUNCTION public.enforce_governed_deployment_staged_artifact_transition() RETURNS TRIGGER AS $$
    BEGIN
      IF NEW.execution_id<>OLD.execution_id OR NEW.project_id<>OLD.project_id OR NEW.target_asset_id<>OLD.target_asset_id OR NEW.policy_version_hash<>OLD.policy_version_hash OR NEW.artifact_hash<>OLD.artifact_hash OR NEW.created_at<>OLD.created_at OR NEW.physical_effects_allowed<>OLD.physical_effects_allowed THEN RAISE EXCEPTION 'governed deployment staged artifact identity is immutable'; END IF;
      IF OLD.status='ROLLED_BACK' OR (OLD.status='STAGED' AND NEW.status<>'ROLLED_BACK') THEN RAISE EXCEPTION 'illegal governed deployment staged artifact transition'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("""CREATE TRIGGER trg_governed_deployment_staged_artifact_transition BEFORE UPDATE ON public.control_governed_deployment_staged_artifacts FOR EACH ROW EXECUTE FUNCTION public.enforce_governed_deployment_staged_artifact_transition()""")


def downgrade() -> None:
    for table in ['control_governed_deployment_staged_artifacts','control_governed_deployment_execution_results','control_governed_deployment_execution_attempts','control_governed_deployment_executions']:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable ON public.{table}")
    op.execute("DROP TRIGGER IF EXISTS trg_governed_deployment_execution_transition ON public.control_governed_deployment_executions")
    op.execute("DROP TRIGGER IF EXISTS trg_governed_deployment_staged_artifact_transition ON public.control_governed_deployment_staged_artifacts")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_governed_deployment_staged_artifact_transition()")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_governed_deployment_execution_history_immutable()")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_governed_deployment_execution_transition()")
    op.execute("DROP INDEX IF EXISTS public.uq_governed_deployment_execution_running_slot")
    op.execute("DROP TABLE IF EXISTS public.control_governed_deployment_execution_results")
    op.execute("DROP TABLE IF EXISTS public.control_governed_deployment_staged_artifacts")
    op.execute("DROP TABLE IF EXISTS public.control_governed_deployment_execution_attempts")
    op.execute("DROP TABLE IF EXISTS public.control_governed_deployment_executions")
