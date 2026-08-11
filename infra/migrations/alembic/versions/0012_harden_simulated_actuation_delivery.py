"""Add bounded retry state to simulated actuation delivery intents.

Revision ID: 0012
Revises: 0011
"""

from alembic import op


revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE public.control_actuation_delivery_intents
        ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMPTZ NULL,
        ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMPTZ NULL
        """
    )
    op.execute(
        """
        ALTER TABLE public.control_actuation_delivery_intents
        DROP CONSTRAINT IF EXISTS control_actuation_delivery_intents_status_check
        """
    )
    op.execute(
        """
        ALTER TABLE public.control_actuation_delivery_intents
        ADD CONSTRAINT control_actuation_delivery_intents_status_check
        CHECK (status IN (
            'received', 'validated', 'ready_to_dispatch', 'dispatched',
            'retry_pending', 'acknowledged', 'rejected', 'expired', 'failed_final'
        ))
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_control_actuation_delivery_intents_retry_due
        ON public.control_actuation_delivery_intents(status, next_retry_at)
        WHERE status = 'retry_pending'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS public.idx_control_actuation_delivery_intents_retry_due")
    op.execute(
        """
        ALTER TABLE public.control_actuation_delivery_intents
        DROP CONSTRAINT IF EXISTS control_actuation_delivery_intents_status_check
        """
    )
    op.execute(
        """
        ALTER TABLE public.control_actuation_delivery_intents
        ADD CONSTRAINT control_actuation_delivery_intents_status_check
        CHECK (status IN (
            'received', 'validated', 'ready_to_dispatch', 'dispatched',
            'acknowledged', 'rejected', 'expired', 'failed_final'
        ))
        """
    )
    op.execute(
        """
        ALTER TABLE public.control_actuation_delivery_intents
        DROP COLUMN IF EXISTS next_retry_at,
        DROP COLUMN IF EXISTS last_attempt_at
        """
    )
