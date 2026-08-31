"""Create immutable human recommendation reviews.

Revision ID: 0028
Revises: 0027
"""
from alembic import op

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("""CREATE TABLE public.control_strategy_recommendation_reviews (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      recommendation_id UUID NOT NULL UNIQUE REFERENCES public.control_strategy_recommendations(id) ON DELETE RESTRICT,
      decision TEXT NOT NULL CHECK (decision IN ('APPROVE_FOR_FURTHER_TESTING','REJECT','REQUEST_MORE_EXPERIMENTS')),
      reviewer_id TEXT NOT NULL CHECK (btrim(reviewer_id)<>''), rationale TEXT NOT NULL CHECK (char_length(btrim(rationale)) BETWEEN 3 AND 2000),
      recommendation_hash TEXT NOT NULL CHECK (recommendation_hash ~ '^[0-9a-f]{64}$'), review_hash TEXT NOT NULL CHECK (review_hash ~ '^[0-9a-f]{64}$'),
      review_policy JSONB NOT NULL CHECK (jsonb_typeof(review_policy)='object'), schema_version INTEGER NOT NULL CHECK (schema_version=1),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK (physical_effects_allowed=FALSE),
      CONSTRAINT control_strategy_recommendation_reviews_hash_unique UNIQUE (project_id,review_hash)
    )""")
    op.execute("CREATE INDEX idx_control_strategy_recommendation_reviews_project_created ON public.control_strategy_recommendation_reviews(project_id,created_at DESC,id DESC)")
    op.execute("""CREATE OR REPLACE FUNCTION public.enforce_control_strategy_recommendation_review_immutable() RETURNS TRIGGER AS $$ BEGIN RAISE EXCEPTION 'strategy recommendation reviews are immutable'; END; $$ LANGUAGE plpgsql""")
    op.execute("CREATE TRIGGER trg_control_strategy_recommendation_reviews_immutable BEFORE UPDATE ON public.control_strategy_recommendation_reviews FOR EACH ROW EXECUTE FUNCTION public.enforce_control_strategy_recommendation_review_immutable()")

def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_control_strategy_recommendation_reviews_immutable ON public.control_strategy_recommendation_reviews")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_control_strategy_recommendation_review_immutable()")
    op.execute("DROP TABLE IF EXISTS public.control_strategy_recommendation_reviews")
