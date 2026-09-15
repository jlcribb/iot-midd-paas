"""Create immutable controlled policy version candidates.

Revision ID: 0031
Revises: 0030
"""
from alembic import op

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE public.control_controlled_policy_version_candidates (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      promotion_proposal_id UUID NOT NULL REFERENCES public.control_policy_promotion_proposals(id) ON DELETE RESTRICT,
      proposal_hash TEXT NOT NULL CHECK (proposal_hash ~ '^[0-9a-f]{64}$'),
      promotion_assessment_id UUID NOT NULL REFERENCES public.control_policy_promotion_assessments(id) ON DELETE RESTRICT,
      assessment_hash TEXT NOT NULL CHECK (assessment_hash ~ '^[0-9a-f]{64}$'),
      source_candidate_id UUID NOT NULL REFERENCES public.control_strategy_candidates(id) ON DELETE RESTRICT,
      candidate_hash TEXT NOT NULL CHECK (candidate_hash ~ '^[0-9a-f]{64}$'),
      strategy_type TEXT NOT NULL CHECK (strategy_type IN ('proportional','threshold')),
      strategy_schema_version INTEGER NOT NULL CHECK (strategy_schema_version > 0),
      version_number INTEGER NOT NULL CHECK (version_number > 0),
      version_label TEXT NOT NULL CHECK (version_label = 'v' || version_number::text),
      configuration_snapshot JSONB NOT NULL CHECK (jsonb_typeof(configuration_snapshot) = 'object'),
      configuration_hash TEXT NOT NULL CHECK (configuration_hash ~ '^[0-9a-f]{64}$'),
      policy_version_hash TEXT NOT NULL CHECK (policy_version_hash ~ '^[0-9a-f]{64}$'),
      provenance_snapshot JSONB NOT NULL CHECK (jsonb_typeof(provenance_snapshot) = 'object'),
      status TEXT NOT NULL CHECK (status = 'CANDIDATE'),
      policy_version_schema TEXT NOT NULL CHECK (policy_version_schema = 'controlled-policy-version:v1'),
      materializer_version TEXT NOT NULL CHECK (materializer_version = 'controlled-policy-materializer:v1'),
      created_by TEXT NOT NULL CHECK (btrim(created_by) <> ''),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK (physical_effects_allowed = FALSE),
      CONSTRAINT control_controlled_policy_version_candidate_proposal_unique UNIQUE (project_id,promotion_proposal_id,materializer_version),
      CONSTRAINT control_controlled_policy_version_candidate_number_unique UNIQUE (project_id,strategy_type,version_number),
      CONSTRAINT control_controlled_policy_version_candidate_hash_unique UNIQUE (project_id,policy_version_hash)
    )""")
    op.execute("CREATE INDEX idx_controlled_policy_version_candidates_project_strategy ON public.control_controlled_policy_version_candidates(project_id,strategy_type,version_number)")
    op.execute("""CREATE OR REPLACE FUNCTION public.enforce_controlled_policy_version_candidate_immutable() RETURNS TRIGGER AS $$
      BEGIN RAISE EXCEPTION 'controlled policy version candidates are immutable'; END; $$ LANGUAGE plpgsql""")
    op.execute("CREATE TRIGGER trg_controlled_policy_version_candidates_immutable BEFORE UPDATE ON public.control_controlled_policy_version_candidates FOR EACH ROW EXECUTE FUNCTION public.enforce_controlled_policy_version_candidate_immutable()")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_controlled_policy_version_candidates_immutable ON public.control_controlled_policy_version_candidates")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_controlled_policy_version_candidate_immutable()")
    op.execute("DROP TABLE IF EXISTS public.control_controlled_policy_version_candidates")
