"""Create immutable deterministic experiment rankings.

Revision ID: 0026
Revises: 0025
"""
from alembic import op

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE public.control_experiment_rankings (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      batch_id UUID NOT NULL REFERENCES public.control_experiment_batches(id) ON DELETE RESTRICT,
      evaluation_profile_id UUID NULL REFERENCES public.control_evaluation_profiles(id) ON DELETE RESTRICT,
      evaluation_profile_version INTEGER NULL CHECK (evaluation_profile_version IS NULL OR evaluation_profile_version > 0),
      ranking_hash TEXT NOT NULL CHECK (ranking_hash ~ '^[0-9a-f]{64}$'),
      ranking_engine_version TEXT NOT NULL, status TEXT NOT NULL CHECK (status IN ('COMPLETED','COMPLETED_WITH_WARNINGS','NOT_RANKABLE')),
      eligible_count INTEGER NOT NULL CHECK (eligible_count >= 0), ineligible_count INTEGER NOT NULL CHECK (ineligible_count >= 0),
      unranked_count INTEGER NOT NULL CHECK (unranked_count >= 0), ranking_policy JSONB NOT NULL CHECK (jsonb_typeof(ranking_policy)='object'),
      schema_version INTEGER NOT NULL CHECK (schema_version=1), created_by TEXT NOT NULL CHECK (btrim(created_by)<>''),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK (physical_effects_allowed=FALSE),
      CONSTRAINT control_experiment_rankings_hash_unique UNIQUE (project_id,ranking_hash),
      CONSTRAINT control_experiment_rankings_profile_version CHECK ((evaluation_profile_id IS NULL AND evaluation_profile_version IS NULL) OR (evaluation_profile_id IS NOT NULL AND evaluation_profile_version IS NOT NULL))
    )""")
    op.execute("""CREATE TABLE public.control_experiment_ranking_items (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), ranking_id UUID NOT NULL REFERENCES public.control_experiment_rankings(id) ON DELETE RESTRICT,
      batch_item_id UUID NOT NULL REFERENCES public.control_experiment_batch_items(id) ON DELETE RESTRICT,
      candidate_id UUID NOT NULL REFERENCES public.control_strategy_candidates(id) ON DELETE RESTRICT,
      evaluation_id UUID NULL REFERENCES public.control_experiment_evaluations(id) ON DELETE RESTRICT,
      eligibility TEXT NOT NULL CHECK (eligibility IN ('ELIGIBLE','INELIGIBLE','UNDETERMINED')),
      eligibility_reason TEXT NULL CHECK (eligibility_reason IN ('CRITICAL_CONSTRAINT_VIOLATION','NOT_EVALUABLE','INCOMPATIBLE_PROFILE','MISSING_EVALUATION','UNSUPPORTED_ENGINE_VERSION')),
      score NUMERIC(12,9) NULL, critical_constraint_violation BOOLEAN NULL, pareto_optimal BOOLEAN NULL,
      dominates_count INTEGER NULL CHECK (dominates_count IS NULL OR dominates_count>=0), dominated_by_count INTEGER NULL CHECK (dominated_by_count IS NULL OR dominated_by_count>=0),
      rank INTEGER NULL CHECK (rank IS NULL OR rank>0), tie_group INTEGER NULL CHECK (tie_group IS NULL OR tie_group>0),
      warnings JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(warnings)='array'), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      CONSTRAINT control_experiment_ranking_items_unique UNIQUE (ranking_id,batch_item_id),
      CONSTRAINT control_experiment_ranking_items_rank_eligibility CHECK ((eligibility='ELIGIBLE' AND rank IS NOT NULL AND tie_group IS NOT NULL) OR (eligibility<>'ELIGIBLE' AND rank IS NULL AND tie_group IS NULL))
    )""")
    op.execute("CREATE INDEX idx_control_experiment_rankings_project_batch ON public.control_experiment_rankings(project_id,batch_id,created_at DESC,id DESC)")
    op.execute("CREATE INDEX idx_control_experiment_ranking_items_ranking_rank ON public.control_experiment_ranking_items(ranking_id,rank NULLS LAST,tie_group NULLS LAST,candidate_id)")
    op.execute("""CREATE OR REPLACE FUNCTION public.enforce_control_experiment_ranking_immutable() RETURNS TRIGGER AS $$
      BEGIN RAISE EXCEPTION 'experiment rankings are immutable'; END; $$ LANGUAGE plpgsql""")
    op.execute("CREATE TRIGGER trg_control_experiment_rankings_immutable BEFORE UPDATE ON public.control_experiment_rankings FOR EACH ROW EXECUTE FUNCTION public.enforce_control_experiment_ranking_immutable()")
    op.execute("CREATE TRIGGER trg_control_experiment_ranking_items_immutable BEFORE UPDATE ON public.control_experiment_ranking_items FOR EACH ROW EXECUTE FUNCTION public.enforce_control_experiment_ranking_immutable()")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_control_experiment_ranking_items_immutable ON public.control_experiment_ranking_items")
    op.execute("DROP TRIGGER IF EXISTS trg_control_experiment_rankings_immutable ON public.control_experiment_rankings")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_control_experiment_ranking_immutable()")
    op.execute("DROP TABLE IF EXISTS public.control_experiment_ranking_items")
    op.execute("DROP TABLE IF EXISTS public.control_experiment_rankings")
