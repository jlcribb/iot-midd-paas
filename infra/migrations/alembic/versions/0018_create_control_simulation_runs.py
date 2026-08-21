"""Create isolated deterministic simulation run persistence.

Revision ID: 0018
Revises: 0017
"""

from alembic import op


revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE public.control_simulation_runs (
          id UUID PRIMARY KEY,
          project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
          session_id UUID NOT NULL REFERENCES public.control_simulation_sessions(id) ON DELETE RESTRICT,
          status TEXT NOT NULL DEFAULT 'CREATED'
            CHECK (status IN ('CREATED', 'RUNNING', 'COMPLETED', 'FAILED')),
          created_by TEXT NOT NULL,
          engine_version TEXT NOT NULL,
          replay_engine_version TEXT NOT NULL,
          clock_model_version TEXT NOT NULL,
          physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE
            CHECK (physical_effects_allowed = FALSE),
          output_count INTEGER NOT NULL DEFAULT 0 CHECK (output_count >= 0),
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          started_at TIMESTAMPTZ NULL,
          completed_at TIMESTAMPTZ NULL,
          failure_code TEXT NULL,
          failure_detail TEXT NULL,
          CHECK (
            (status = 'CREATED' AND started_at IS NULL AND completed_at IS NULL)
            OR (status = 'RUNNING' AND started_at IS NOT NULL AND completed_at IS NULL)
            OR (status IN ('COMPLETED', 'FAILED') AND started_at IS NOT NULL AND completed_at IS NOT NULL)
          )
        )
        """
    )
    op.execute(
        """
        CREATE TABLE public.control_simulation_run_events (
          id BIGSERIAL PRIMARY KEY,
          run_id UUID NOT NULL REFERENCES public.control_simulation_runs(id) ON DELETE CASCADE,
          sequence INTEGER NOT NULL CHECK (sequence > 0),
          event_id UUID NOT NULL,
          virtual_timestamp TIMESTAMPTZ NOT NULL,
          output JSONB NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          UNIQUE (run_id, sequence),
          UNIQUE (run_id, event_id)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX idx_control_simulation_runs_project_session_created
          ON public.control_simulation_runs(project_id, session_id, created_at DESC, id DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_control_simulation_run_events_run_sequence
          ON public.control_simulation_run_events(run_id, sequence)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS public.idx_control_simulation_run_events_run_sequence")
    op.execute("DROP INDEX IF EXISTS public.idx_control_simulation_runs_project_session_created")
    op.execute("DROP TABLE IF EXISTS public.control_simulation_run_events")
    op.execute("DROP TABLE IF EXISTS public.control_simulation_runs")
