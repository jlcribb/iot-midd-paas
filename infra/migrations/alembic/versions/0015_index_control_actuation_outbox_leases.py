"""Index expired outbox lease recovery scans."""

from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_control_actuation_outbox_publishing_lease
        ON public.control_actuation_outbox(lease_until)
        WHERE status = 'publishing'
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS public.idx_control_actuation_outbox_publishing_lease")
