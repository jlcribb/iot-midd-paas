"""Create isolated simulation-session records.

Revision ID: 0016
Revises: 0015
"""

from alembic import op


revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE public.control_simulation_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
            execution_context TEXT NOT NULL DEFAULT 'SIMULATION',
            status TEXT NOT NULL DEFAULT 'DRAFT',
            created_by TEXT NOT NULL,
            snapshot_refs JSONB NOT NULL DEFAULT '{}'::jsonb,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            started_at TIMESTAMPTZ NULL,
            completed_at TIMESTAMPTZ NULL,
            CONSTRAINT control_simulation_sessions_context_valid
                CHECK (execution_context = 'SIMULATION'),
            CONSTRAINT control_simulation_sessions_status_valid
                CHECK (status IN ('DRAFT', 'READY', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED')),
            CONSTRAINT control_simulation_sessions_completion_order_valid
                CHECK (completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX idx_control_simulation_sessions_project_created
        ON public.control_simulation_sessions(project_id, created_at DESC, id DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS public.idx_control_simulation_sessions_project_created")
    op.execute("DROP TABLE IF EXISTS public.control_simulation_sessions")
