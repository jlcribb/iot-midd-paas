"""Create governed evaluation metrics and project evaluation profiles.

Revision ID: 0020
Revises: 0019
"""

from alembic import op


revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
      CREATE TABLE public.control_evaluation_metrics (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        code TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
        name TEXT NOT NULL CHECK (btrim(name) <> ''),
        description TEXT NOT NULL DEFAULT '',
        unit TEXT NULL,
        direction TEXT NOT NULL CHECK (direction IN ('MINIMIZE', 'MAXIMIZE', 'TARGET', 'RANGE')),
        normalization_method TEXT NOT NULL CHECK (normalization_method IN ('MIN_MAX', 'TARGET_DISTANCE', 'RANGE_DISTANCE')),
        normalization_config JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(normalization_config) = 'object'),
        weightable BOOLEAN NOT NULL DEFAULT TRUE,
        active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT control_evaluation_metrics_code_valid CHECK (code ~ '^[a-z][a-z0-9_]{2,63}$'),
        CONSTRAINT control_evaluation_metrics_code_version_unique UNIQUE (code, version)
      )
    """)
    op.execute("""
      CREATE TABLE public.control_evaluation_profiles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
        code TEXT NOT NULL,
        version INTEGER NOT NULL CHECK (version >= 1),
        name TEXT NOT NULL CHECK (btrim(name) <> ''),
        description TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'RETIRED')),
        schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version = 1),
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata) = 'object'),
        created_by TEXT NOT NULL CHECK (btrim(created_by) <> ''),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT control_evaluation_profiles_code_valid CHECK (code ~ '^[a-z][a-z0-9_]{2,63}$'),
        CONSTRAINT control_evaluation_profiles_project_code_version_unique UNIQUE (project_id, code, version)
      )
    """)
    op.execute("""
      CREATE TABLE public.control_evaluation_profile_metrics (
        profile_id UUID NOT NULL REFERENCES public.control_evaluation_profiles(id) ON DELETE CASCADE,
        metric_id UUID NOT NULL REFERENCES public.control_evaluation_metrics(id) ON DELETE RESTRICT,
        weight NUMERIC(12, 9) NOT NULL CHECK (weight > 0 AND weight <= 1),
        required BOOLEAN NOT NULL DEFAULT TRUE,
        PRIMARY KEY (profile_id, metric_id)
      )
    """)
    op.execute("""
      CREATE INDEX idx_control_evaluation_metrics_active_code
        ON public.control_evaluation_metrics(active, code, version DESC)
    """)
    op.execute("""
      CREATE INDEX idx_control_evaluation_profiles_project_code
        ON public.control_evaluation_profiles(project_id, code, version DESC, created_at DESC)
    """)
    op.execute("""
      CREATE OR REPLACE FUNCTION public.enforce_control_evaluation_profile_immutable()
      RETURNS TRIGGER AS $$
      BEGIN
        RAISE EXCEPTION 'evaluation profiles are immutable; create a new version';
      END;
      $$ LANGUAGE plpgsql
    """)
    op.execute("""
      CREATE TRIGGER trg_control_evaluation_profiles_immutable
      BEFORE UPDATE ON public.control_evaluation_profiles
      FOR EACH ROW EXECUTE FUNCTION public.enforce_control_evaluation_profile_immutable()
    """)
    op.execute("""
      INSERT INTO public.control_evaluation_metrics
        (code, version, name, description, unit, direction, normalization_method, weightable)
      VALUES
        ('tracking_error', 1, 'Tracking error', 'Aggregate absolute deviation from the experiment target.', 'controlled-unit', 'MINIMIZE', 'MIN_MAX', TRUE),
        ('settling_time', 1, 'Settling time', 'Virtual time required to remain inside the configured settling band.', 'seconds', 'MINIMIZE', 'MIN_MAX', TRUE),
        ('overshoot', 1, 'Overshoot', 'Maximum excursion above the experiment target.', 'controlled-unit', 'MINIMIZE', 'MIN_MAX', TRUE),
        ('undershoot', 1, 'Undershoot', 'Maximum excursion below the experiment target.', 'controlled-unit', 'MINIMIZE', 'MIN_MAX', TRUE),
        ('control_effort', 1, 'Control effort', 'Aggregate absolute control signal applied by a simulated strategy.', 'control-unit', 'MINIMIZE', 'MIN_MAX', TRUE),
        ('energy_cost', 1, 'Energy cost', 'Deterministic simulation energy proxy.', 'energy-proxy', 'MINIMIZE', 'MIN_MAX', TRUE),
        ('actuation_count', 1, 'Actuation count', 'Count of simulated actionable control recommendations.', 'count', 'MINIMIZE', 'MIN_MAX', TRUE),
        ('constraint_violations', 1, 'Constraint violations', 'Count of simulation safety-envelope constraint violations.', 'count', 'MINIMIZE', 'MIN_MAX', TRUE),
        ('stability_score', 1, 'Stability score', 'Deterministic score representing simulated stability.', 'score', 'MAXIMIZE', 'MIN_MAX', TRUE),
        ('response_time', 1, 'Response time', 'Virtual response time to a relevant simulated input change.', 'seconds', 'MINIMIZE', 'MIN_MAX', TRUE),
        ('resource_consumption', 1, 'Resource consumption', 'Aggregate deterministic resource-consumption proxy.', 'resource-proxy', 'MINIMIZE', 'MIN_MAX', TRUE)
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_control_evaluation_profiles_immutable ON public.control_evaluation_profiles")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_control_evaluation_profile_immutable()")
    op.execute("DROP INDEX IF EXISTS public.idx_control_evaluation_profiles_project_code")
    op.execute("DROP INDEX IF EXISTS public.idx_control_evaluation_metrics_active_code")
    op.execute("DROP TABLE IF EXISTS public.control_evaluation_profile_metrics")
    op.execute("DROP TABLE IF EXISTS public.control_evaluation_profiles")
    op.execute("DROP TABLE IF EXISTS public.control_evaluation_metrics")
