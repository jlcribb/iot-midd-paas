"""Persist immutable, simulation-only experiment comparisons.

Revision ID: 0022
Revises: 0021
"""

from alembic import op


revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
      CREATE TABLE public.control_experiment_comparisons (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
        baseline_evaluation_id UUID NOT NULL REFERENCES public.control_experiment_evaluations(id) ON DELETE RESTRICT,
        candidate_evaluation_id UUID NOT NULL REFERENCES public.control_experiment_evaluations(id) ON DELETE RESTRICT,
        relation TEXT NOT NULL CHECK (relation IN ('BETTER', 'WORSE', 'EQUIVALENT', 'TRADE_OFF', 'INCOMPARABLE')),
        incompatibility_reason TEXT NULL,
        score_delta NUMERIC(12, 9) NULL,
        candidate_dominates_baseline BOOLEAN NOT NULL DEFAULT FALSE,
        baseline_dominates_candidate BOOLEAN NOT NULL DEFAULT FALSE,
        comparable_metric_count INTEGER NOT NULL CHECK (comparable_metric_count >= 0),
        profile_metric_count INTEGER NOT NULL CHECK (profile_metric_count >= 0),
        coverage_ratio NUMERIC(12, 9) NOT NULL CHECK (coverage_ratio >= 0 AND coverage_ratio <= 1),
        comparison_hash TEXT NOT NULL CHECK (comparison_hash ~ '^[0-9a-f]{64}$'),
        schema_version INTEGER NOT NULL CHECK (schema_version = 1),
        engine_version TEXT NOT NULL,
        comparison_policy JSONB NOT NULL CHECK (jsonb_typeof(comparison_policy) = 'object'),
        created_by TEXT NOT NULL CHECK (btrim(created_by) <> ''),
        physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK (physical_effects_allowed = FALSE),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT control_experiment_comparisons_hash_unique UNIQUE (comparison_hash),
        CONSTRAINT control_experiment_comparisons_directional_pair_unique
          UNIQUE (baseline_evaluation_id, candidate_evaluation_id, engine_version),
        CONSTRAINT control_experiment_comparisons_distinct_evaluations
          CHECK (baseline_evaluation_id <> candidate_evaluation_id)
      )
    """)
    op.execute("""
      CREATE TABLE public.control_experiment_comparison_metrics (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        comparison_id UUID NOT NULL REFERENCES public.control_experiment_comparisons(id) ON DELETE CASCADE,
        metric_id UUID NOT NULL REFERENCES public.control_evaluation_metrics(id) ON DELETE RESTRICT,
        metric_code TEXT NOT NULL,
        metric_version INTEGER NOT NULL CHECK (metric_version >= 1),
        baseline_raw_value NUMERIC(18, 9) NULL,
        candidate_raw_value NUMERIC(18, 9) NULL,
        baseline_normalized_value NUMERIC(12, 9) NULL CHECK (baseline_normalized_value >= 0 AND baseline_normalized_value <= 1),
        candidate_normalized_value NUMERIC(12, 9) NULL CHECK (candidate_normalized_value >= 0 AND candidate_normalized_value <= 1),
        raw_delta NUMERIC(18, 9) NULL,
        normalized_delta NUMERIC(12, 9) NULL,
        relation TEXT NOT NULL CHECK (relation IN ('BETTER', 'WORSE', 'EQUIVALENT', 'UNAVAILABLE')),
        epsilon NUMERIC(12, 9) NOT NULL CHECK (epsilon > 0),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT control_experiment_comparison_metrics_unique UNIQUE (comparison_id, metric_id)
      )
    """)
    op.execute("CREATE INDEX idx_control_experiment_comparisons_project_created ON public.control_experiment_comparisons(project_id, created_at DESC, id DESC)")
    op.execute("CREATE INDEX idx_control_experiment_comparisons_baseline ON public.control_experiment_comparisons(baseline_evaluation_id)")
    op.execute("CREATE INDEX idx_control_experiment_comparisons_candidate ON public.control_experiment_comparisons(candidate_evaluation_id)")
    op.execute("CREATE INDEX idx_control_experiment_comparison_metrics_comparison ON public.control_experiment_comparison_metrics(comparison_id, metric_code)")
    op.execute("""
      CREATE OR REPLACE FUNCTION public.enforce_control_experiment_comparison_immutable()
      RETURNS TRIGGER AS $$
      BEGIN
        RAISE EXCEPTION 'experiment comparisons are immutable';
      END;
      $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_control_experiment_comparisons_immutable BEFORE UPDATE ON public.control_experiment_comparisons FOR EACH ROW EXECUTE FUNCTION public.enforce_control_experiment_comparison_immutable()")
    op.execute("CREATE TRIGGER trg_control_experiment_comparison_metrics_immutable BEFORE UPDATE ON public.control_experiment_comparison_metrics FOR EACH ROW EXECUTE FUNCTION public.enforce_control_experiment_comparison_immutable()")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_control_experiment_comparison_metrics_immutable ON public.control_experiment_comparison_metrics")
    op.execute("DROP TRIGGER IF EXISTS trg_control_experiment_comparisons_immutable ON public.control_experiment_comparisons")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_control_experiment_comparison_immutable()")
    op.execute("DROP INDEX IF EXISTS public.idx_control_experiment_comparison_metrics_comparison")
    op.execute("DROP INDEX IF EXISTS public.idx_control_experiment_comparisons_candidate")
    op.execute("DROP INDEX IF EXISTS public.idx_control_experiment_comparisons_baseline")
    op.execute("DROP INDEX IF EXISTS public.idx_control_experiment_comparisons_project_created")
    op.execute("DROP TABLE IF EXISTS public.control_experiment_comparison_metrics")
    op.execute("DROP TABLE IF EXISTS public.control_experiment_comparisons")
