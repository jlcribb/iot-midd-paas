"""Create immutable deterministic simulation result evidence.

Revision ID: 0019
Revises: 0018
"""

from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
      CREATE TABLE public.control_simulation_results (
        id UUID PRIMARY KEY,
        project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
        session_id UUID NOT NULL REFERENCES public.control_simulation_sessions(id) ON DELETE RESTRICT,
        run_id UUID NOT NULL UNIQUE REFERENCES public.control_simulation_runs(id) ON DELETE RESTRICT,
        experiment_fingerprint TEXT NOT NULL CHECK (experiment_fingerprint ~ '^[0-9a-f]{64}$'),
        result_fingerprint TEXT NOT NULL CHECK (result_fingerprint ~ '^[0-9a-f]{64}$'),
        processed_events INTEGER NOT NULL CHECK (processed_events >= 0),
        evaluation_count INTEGER NOT NULL CHECK (evaluation_count >= 0),
        recommendation_count INTEGER NOT NULL CHECK (recommendation_count >= 0),
        actionable_recommendation_count INTEGER NOT NULL CHECK (actionable_recommendation_count >= 0),
        recommendation_only_count INTEGER NOT NULL CHECK (recommendation_only_count >= 0),
        failed_domain_event_count INTEGER NOT NULL CHECK (failed_domain_event_count >= 0),
        first_virtual_timestamp TIMESTAMPTZ NULL,
        last_virtual_timestamp TIMESTAMPTZ NULL,
        canonical_result_schema_version INTEGER NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CHECK (evaluation_count = processed_events),
        CHECK (actionable_recommendation_count + recommendation_only_count <= recommendation_count),
        CHECK (last_virtual_timestamp IS NULL OR first_virtual_timestamp IS NULL OR last_virtual_timestamp >= first_virtual_timestamp)
      )
    """)
    op.execute("CREATE INDEX idx_control_simulation_results_project_session_run ON public.control_simulation_results(project_id, session_id, run_id)")
    op.execute("""
      CREATE OR REPLACE FUNCTION public.enforce_control_simulation_result_immutable()
      RETURNS TRIGGER AS $$
      BEGIN
        RAISE EXCEPTION 'simulation results are immutable';
      END;
      $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_control_simulation_results_immutable BEFORE UPDATE ON public.control_simulation_results FOR EACH ROW EXECUTE FUNCTION public.enforce_control_simulation_result_immutable()")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_control_simulation_results_immutable ON public.control_simulation_results")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_control_simulation_result_immutable()")
    op.execute("DROP INDEX IF EXISTS public.idx_control_simulation_results_project_session_run")
    op.execute("DROP TABLE IF EXISTS public.control_simulation_results")
