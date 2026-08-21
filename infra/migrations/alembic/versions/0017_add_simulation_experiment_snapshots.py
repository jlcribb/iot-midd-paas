"""Add immutable reproducible snapshots to simulation sessions.

Revision ID: 0017
Revises: 0016
"""

from alembic import op


revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE public.control_simulation_sessions
          ADD COLUMN policy_snapshot JSONB NULL,
          ADD COLUMN topology_snapshot JSONB NULL,
          ADD COLUMN dataset_snapshot JSONB NULL,
          ADD COLUMN configuration_snapshot JSONB NULL,
          ADD COLUMN policy_snapshot_hash TEXT NULL,
          ADD COLUMN topology_snapshot_hash TEXT NULL,
          ADD COLUMN dataset_snapshot_hash TEXT NULL,
          ADD COLUMN configuration_snapshot_hash TEXT NULL,
          ADD COLUMN experiment_fingerprint TEXT NULL,
          ADD COLUMN snapshot_schema_version INTEGER NULL,
          ADD COLUMN prepared_at TIMESTAMPTZ NULL
        """
    )
    op.execute(
        """
        ALTER TABLE public.control_simulation_sessions
        ADD CONSTRAINT control_simulation_sessions_ready_snapshot_complete
        CHECK (
          status <> 'READY' OR (
            policy_snapshot IS NOT NULL AND topology_snapshot IS NOT NULL
            AND dataset_snapshot IS NOT NULL AND configuration_snapshot IS NOT NULL
            AND policy_snapshot_hash ~ '^[0-9a-f]{64}$'
            AND topology_snapshot_hash ~ '^[0-9a-f]{64}$'
            AND dataset_snapshot_hash ~ '^[0-9a-f]{64}$'
            AND configuration_snapshot_hash ~ '^[0-9a-f]{64}$'
            AND experiment_fingerprint ~ '^[0-9a-f]{64}$'
            AND snapshot_schema_version = 1 AND prepared_at IS NOT NULL
          )
        )
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.enforce_control_simulation_session_lifecycle()
        RETURNS TRIGGER AS $$
        BEGIN
          IF OLD.status = 'READY' AND NEW IS DISTINCT FROM OLD THEN
            RAISE EXCEPTION 'READY simulation sessions are immutable';
          END IF;
          IF OLD.status = 'DRAFT' AND NEW.status NOT IN ('DRAFT', 'READY') THEN
            RAISE EXCEPTION 'simulation session may transition only from DRAFT to READY';
          END IF;
          IF OLD.status <> 'DRAFT' AND OLD.status <> 'READY' AND NEW.status IS DISTINCT FROM OLD.status THEN
            RAISE EXCEPTION 'simulation session lifecycle transition is not enabled';
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_control_simulation_sessions_lifecycle
        BEFORE UPDATE ON public.control_simulation_sessions
        FOR EACH ROW EXECUTE FUNCTION public.enforce_control_simulation_session_lifecycle()
        """
    )
    op.execute(
        """
        CREATE INDEX idx_control_simulation_sessions_project_status_prepared
        ON public.control_simulation_sessions(project_id, status, prepared_at DESC, id DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_control_simulation_sessions_fingerprint
        ON public.control_simulation_sessions(project_id, experiment_fingerprint)
        WHERE experiment_fingerprint IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS public.idx_control_simulation_sessions_fingerprint")
    op.execute("DROP INDEX IF EXISTS public.idx_control_simulation_sessions_project_status_prepared")
    op.execute("DROP TRIGGER IF EXISTS trg_control_simulation_sessions_lifecycle ON public.control_simulation_sessions")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_control_simulation_session_lifecycle()")
    op.execute("ALTER TABLE public.control_simulation_sessions DROP CONSTRAINT IF EXISTS control_simulation_sessions_ready_snapshot_complete")
    op.execute(
        """
        ALTER TABLE public.control_simulation_sessions
          DROP COLUMN IF EXISTS prepared_at,
          DROP COLUMN IF EXISTS snapshot_schema_version,
          DROP COLUMN IF EXISTS experiment_fingerprint,
          DROP COLUMN IF EXISTS configuration_snapshot_hash,
          DROP COLUMN IF EXISTS dataset_snapshot_hash,
          DROP COLUMN IF EXISTS topology_snapshot_hash,
          DROP COLUMN IF EXISTS policy_snapshot_hash,
          DROP COLUMN IF EXISTS configuration_snapshot,
          DROP COLUMN IF EXISTS dataset_snapshot,
          DROP COLUMN IF EXISTS topology_snapshot,
          DROP COLUMN IF EXISTS policy_snapshot
        """
    )
