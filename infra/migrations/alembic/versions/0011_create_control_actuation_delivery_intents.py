"""Create persistent intents for simulated actuation delivery.

Revision ID: 0011
Revises: 0010
"""

from alembic import op


revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.control_actuation_delivery_intents (
            id UUID PRIMARY KEY,
            command_id UUID NOT NULL UNIQUE,
            recommendation_id TEXT NOT NULL,
            correlation_id TEXT NOT NULL,
            project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
            policy_id TEXT NOT NULL,
            policy_version INTEGER NOT NULL,
            source_asset_id UUID NULL,
            target_asset_id UUID NULL,
            target_kind TEXT NOT NULL,
            target_reference TEXT NOT NULL,
            variable_id TEXT NOT NULL,
            operation TEXT NOT NULL,
            requested_value DOUBLE PRECISION NOT NULL,
            idempotency_key TEXT NOT NULL UNIQUE,
            governance_mode TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'received',
            retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            last_error TEXT NULL,
            simulated BOOLEAN NOT NULL DEFAULT TRUE,
            CHECK (status IN ('received', 'validated', 'ready_to_dispatch', 'dispatched', 'acknowledged', 'rejected', 'expired', 'failed_final')),
            CHECK (governance_mode IN ('simulated', 'recommendation_only', 'approval_required', 'automatic')),
            CHECK (target_kind IN ('simulated', 'asset')),
            CHECK (simulated = TRUE)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_control_actuation_delivery_intents_project_status
        ON public.control_actuation_delivery_intents(project_id, status, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_control_actuation_delivery_intents_expires_at
        ON public.control_actuation_delivery_intents(expires_at)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS public.control_actuation_delivery_intents")
