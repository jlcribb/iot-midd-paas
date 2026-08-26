"""Create deterministic, simulation-only experiment evaluations.

Revision ID: 0021
Revises: 0020
"""

from alembic import op


revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # M6.1 intentionally declared the normalization method, while M6.2 makes
    # its v1 parameters explicit and persistent.  No runtime defaults exist.
    op.get_bind().exec_driver_sql("""
      UPDATE public.control_evaluation_metrics
      SET normalization_config = CASE code
        WHEN 'tracking_error' THEN '{"schema_version":1,"best":0,"worst":100}'::jsonb
        WHEN 'settling_time' THEN '{"schema_version":1,"best":0,"worst":3600}'::jsonb
        WHEN 'overshoot' THEN '{"schema_version":1,"best":0,"worst":1}'::jsonb
        WHEN 'undershoot' THEN '{"schema_version":1,"best":0,"worst":1}'::jsonb
        WHEN 'control_effort' THEN '{"schema_version":1,"best":0,"worst":1000}'::jsonb
        WHEN 'energy_cost' THEN '{"schema_version":1,"best":0,"worst":1000}'::jsonb
        WHEN 'actuation_count' THEN '{"schema_version":1,"best":0,"worst":100}'::jsonb
        WHEN 'constraint_violations' THEN '{"schema_version":1,"best":0,"worst":10}'::jsonb
        WHEN 'stability_score' THEN '{"schema_version":1,"best":1,"worst":0}'::jsonb
        WHEN 'response_time' THEN '{"schema_version":1,"best":0,"worst":3600}'::jsonb
        WHEN 'resource_consumption' THEN '{"schema_version":1,"best":0,"worst":1000}'::jsonb
      END
      WHERE version = 1
    """)
    op.execute("""
      CREATE TABLE public.control_evaluation_profile_constraints (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        profile_id UUID NOT NULL REFERENCES public.control_evaluation_profiles(id) ON DELETE CASCADE,
        metric_id UUID NOT NULL REFERENCES public.control_evaluation_metrics(id) ON DELETE RESTRICT,
        kind TEXT NOT NULL CHECK (kind IN ('MINIMUM', 'MAXIMUM', 'RANGE')),
        lower_bound NUMERIC(18, 9) NULL,
        upper_bound NUMERIC(18, 9) NULL,
        critical BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT control_evaluation_profile_constraints_one_per_metric UNIQUE (profile_id, metric_id),
        CONSTRAINT control_evaluation_profile_constraints_bounds_valid CHECK (
          (kind = 'MINIMUM' AND lower_bound IS NOT NULL AND upper_bound IS NULL)
          OR (kind = 'MAXIMUM' AND lower_bound IS NULL AND upper_bound IS NOT NULL)
          OR (kind = 'RANGE' AND lower_bound IS NOT NULL AND upper_bound IS NOT NULL AND lower_bound <= upper_bound)
        )
      )
    """)
    op.execute("""
      CREATE TABLE public.control_experiment_evaluations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
        simulation_run_id UUID NOT NULL REFERENCES public.control_simulation_runs(id) ON DELETE RESTRICT,
        simulation_result_id UUID NOT NULL REFERENCES public.control_simulation_results(id) ON DELETE RESTRICT,
        evaluation_profile_id UUID NOT NULL REFERENCES public.control_evaluation_profiles(id) ON DELETE RESTRICT,
        evaluation_profile_version INTEGER NOT NULL CHECK (evaluation_profile_version >= 1),
        status TEXT NOT NULL CHECK (status IN ('PENDING', 'COMPLETED', 'COMPLETED_WITH_WARNINGS', 'INVALID_INPUT', 'NOT_EVALUABLE')),
        score NUMERIC(12, 9) NULL CHECK (score >= 0 AND score <= 1),
        constraint_satisfied_count INTEGER NOT NULL DEFAULT 0 CHECK (constraint_satisfied_count >= 0),
        constraint_violated_count INTEGER NOT NULL DEFAULT 0 CHECK (constraint_violated_count >= 0),
        constraint_unknown_count INTEGER NOT NULL DEFAULT 0 CHECK (constraint_unknown_count >= 0),
        critical_constraint_violation BOOLEAN NOT NULL DEFAULT FALSE,
        evaluation_hash TEXT NOT NULL CHECK (evaluation_hash ~ '^[0-9a-f]{64}$'),
        schema_version INTEGER NOT NULL CHECK (schema_version = 1),
        engine_version TEXT NOT NULL,
        created_by TEXT NOT NULL CHECK (btrim(created_by) <> ''),
        physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK (physical_effects_allowed = FALSE),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT control_experiment_evaluations_idempotency_unique
          UNIQUE (simulation_result_id, evaluation_profile_id, engine_version)
      )
    """)
    op.execute("""
      CREATE TABLE public.control_experiment_evaluation_metrics (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        evaluation_id UUID NOT NULL REFERENCES public.control_experiment_evaluations(id) ON DELETE CASCADE,
        metric_id UUID NOT NULL REFERENCES public.control_evaluation_metrics(id) ON DELETE RESTRICT,
        metric_code TEXT NOT NULL,
        metric_version INTEGER NOT NULL CHECK (metric_version >= 1),
        availability_status TEXT NOT NULL CHECK (availability_status IN ('AVAILABLE', 'MISSING', 'NOT_APPLICABLE', 'INVALID', 'NOT_AVAILABLE')),
        availability_reason TEXT NULL,
        raw_value NUMERIC(18, 9) NULL,
        normalized_value NUMERIC(12, 9) NULL CHECK (normalized_value >= 0 AND normalized_value <= 1),
        weight NUMERIC(12, 9) NOT NULL CHECK (weight > 0 AND weight <= 1),
        weighted_contribution NUMERIC(12, 9) NULL CHECK (weighted_contribution >= 0 AND weighted_contribution <= 1),
        direction TEXT NOT NULL CHECK (direction IN ('MINIMIZE', 'MAXIMIZE', 'TARGET', 'RANGE')),
        normalization_method TEXT NOT NULL CHECK (normalization_method IN ('MIN_MAX', 'TARGET_DISTANCE', 'RANGE_DISTANCE')),
        normalization_config JSONB NOT NULL CHECK (jsonb_typeof(normalization_config) = 'object'),
        constraint_status TEXT NOT NULL CHECK (constraint_status IN ('SATISFIED', 'VIOLATED', 'UNKNOWN', 'NOT_APPLICABLE')),
        constraint_definition JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(constraint_definition) = 'array'),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT control_experiment_evaluation_metrics_unique UNIQUE (evaluation_id, metric_id)
      )
    """)
    op.execute("CREATE INDEX idx_control_experiment_evaluations_project_created ON public.control_experiment_evaluations(project_id, created_at DESC, id DESC)")
    op.execute("CREATE INDEX idx_control_experiment_evaluations_hash ON public.control_experiment_evaluations(evaluation_hash)")
    op.execute("CREATE INDEX idx_control_experiment_evaluation_metrics_evaluation ON public.control_experiment_evaluation_metrics(evaluation_id, metric_code)")
    op.execute("""
      CREATE OR REPLACE FUNCTION public.enforce_control_experiment_evaluation_immutable()
      RETURNS TRIGGER AS $$
      BEGIN
        RAISE EXCEPTION 'experiment evaluations are immutable';
      END;
      $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_control_experiment_evaluations_immutable BEFORE UPDATE ON public.control_experiment_evaluations FOR EACH ROW EXECUTE FUNCTION public.enforce_control_experiment_evaluation_immutable()")
    op.execute("CREATE TRIGGER trg_control_experiment_evaluation_metrics_immutable BEFORE UPDATE ON public.control_experiment_evaluation_metrics FOR EACH ROW EXECUTE FUNCTION public.enforce_control_experiment_evaluation_immutable()")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_control_experiment_evaluation_metrics_immutable ON public.control_experiment_evaluation_metrics")
    op.execute("DROP TRIGGER IF EXISTS trg_control_experiment_evaluations_immutable ON public.control_experiment_evaluations")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_control_experiment_evaluation_immutable()")
    op.execute("DROP INDEX IF EXISTS public.idx_control_experiment_evaluation_metrics_evaluation")
    op.execute("DROP INDEX IF EXISTS public.idx_control_experiment_evaluations_hash")
    op.execute("DROP INDEX IF EXISTS public.idx_control_experiment_evaluations_project_created")
    op.execute("DROP TABLE IF EXISTS public.control_experiment_evaluation_metrics")
    op.execute("DROP TABLE IF EXISTS public.control_experiment_evaluations")
    op.execute("DROP TABLE IF EXISTS public.control_evaluation_profile_constraints")
    op.execute("UPDATE public.control_evaluation_metrics SET normalization_config='{}'::jsonb WHERE version = 1")
