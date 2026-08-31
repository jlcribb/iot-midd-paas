"""Create immutable governed strategy recommendations.

Revision ID: 0027
Revises: 0026
"""
from alembic import op

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("""CREATE TABLE public.control_strategy_recommendations (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      batch_id UUID NOT NULL REFERENCES public.control_experiment_batches(id) ON DELETE RESTRICT, ranking_id UUID NOT NULL REFERENCES public.control_experiment_rankings(id) ON DELETE RESTRICT,
      selected_candidate_id UUID NULL REFERENCES public.control_strategy_candidates(id) ON DELETE RESTRICT, selected_evaluation_id UUID NULL REFERENCES public.control_experiment_evaluations(id) ON DELETE RESTRICT,
      recommendation_hash TEXT NOT NULL CHECK (recommendation_hash ~ '^[0-9a-f]{64}$'), outcome TEXT NOT NULL CHECK (outcome IN ('UNIQUE_CANDIDATE','AMBIGUOUS','NO_ELIGIBLE_CANDIDATE','NO_RANKING')),
      status TEXT NOT NULL CHECK (status='REVIEW_REQUIRED'), recommendation_policy JSONB NOT NULL CHECK (jsonb_typeof(recommendation_policy)='object'), recommendation_engine_version TEXT NOT NULL,
      summary TEXT NOT NULL, warnings JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(warnings)='array'), tradeoffs JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(tradeoffs)='array'), evidence_snapshot JSONB NOT NULL CHECK (jsonb_typeof(evidence_snapshot)='object'), schema_version INTEGER NOT NULL CHECK (schema_version=1), created_by TEXT NOT NULL CHECK (btrim(created_by)<>''), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK (physical_effects_allowed=FALSE),
      CONSTRAINT control_strategy_recommendations_hash_unique UNIQUE (project_id,recommendation_hash), CONSTRAINT control_strategy_recommendations_unique_candidate CHECK ((outcome='UNIQUE_CANDIDATE' AND selected_candidate_id IS NOT NULL AND selected_evaluation_id IS NOT NULL) OR (outcome<>'UNIQUE_CANDIDATE' AND selected_candidate_id IS NULL AND selected_evaluation_id IS NULL))
    )""")
    op.execute("""CREATE TABLE public.control_strategy_recommendation_candidates (
      recommendation_id UUID NOT NULL REFERENCES public.control_strategy_recommendations(id) ON DELETE RESTRICT, candidate_id UUID NOT NULL REFERENCES public.control_strategy_candidates(id) ON DELETE RESTRICT, candidate_hash TEXT NOT NULL CHECK (candidate_hash ~ '^[0-9a-f]{64}$'), evaluation_id UUID NULL REFERENCES public.control_experiment_evaluations(id) ON DELETE RESTRICT, role TEXT NOT NULL CHECK (role IN ('SELECTED','AMBIGUOUS')), PRIMARY KEY(recommendation_id,candidate_id), CONSTRAINT control_strategy_recommendation_candidate_role CHECK ((role='SELECTED') OR role='AMBIGUOUS')
    )""")
    op.execute("CREATE INDEX idx_control_strategy_recommendations_project_created ON public.control_strategy_recommendations(project_id,created_at DESC,id DESC)")
    op.execute("""CREATE OR REPLACE FUNCTION public.enforce_control_strategy_recommendation_immutable() RETURNS TRIGGER AS $$ BEGIN RAISE EXCEPTION 'strategy recommendations are immutable'; END; $$ LANGUAGE plpgsql""")
    op.execute("CREATE TRIGGER trg_control_strategy_recommendations_immutable BEFORE UPDATE ON public.control_strategy_recommendations FOR EACH ROW EXECUTE FUNCTION public.enforce_control_strategy_recommendation_immutable()")
    op.execute("CREATE TRIGGER trg_control_strategy_recommendation_candidates_immutable BEFORE UPDATE ON public.control_strategy_recommendation_candidates FOR EACH ROW EXECUTE FUNCTION public.enforce_control_strategy_recommendation_immutable()")

def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_control_strategy_recommendation_candidates_immutable ON public.control_strategy_recommendation_candidates")
    op.execute("DROP TRIGGER IF EXISTS trg_control_strategy_recommendations_immutable ON public.control_strategy_recommendations")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_control_strategy_recommendation_immutable()")
    op.execute("DROP TABLE IF EXISTS public.control_strategy_recommendation_candidates")
    op.execute("DROP TABLE IF EXISTS public.control_strategy_recommendations")
