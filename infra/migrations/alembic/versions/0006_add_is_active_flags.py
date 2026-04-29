"""Add explicit is_active flags for sectors and locations.

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-27 00:30:00.000000
"""

from alembic import op


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL search_path TO public")

    op.execute(
        """
        ALTER TABLE IF EXISTS public.sectors
        ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true
        """
    )
    op.execute(
        """
        ALTER TABLE IF EXISTS public.locations
        ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true
        """
    )

    op.execute(
        """
        UPDATE public.sectors
        SET is_active = COALESCE((metadata->>'is_active')::boolean, true)
        """
    )
    op.execute(
        """
        UPDATE public.locations
        SET is_active = COALESCE((metadata->>'is_active')::boolean, true)
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS ix_sectors_is_active ON public.sectors(is_active)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_locations_is_active ON public.locations(is_active)")


def downgrade() -> None:
    op.execute("SET LOCAL search_path TO public")
    op.execute("DROP INDEX IF EXISTS public.ix_locations_is_active")
    op.execute("DROP INDEX IF EXISTS public.ix_sectors_is_active")
    op.execute("ALTER TABLE IF EXISTS public.locations DROP COLUMN IF EXISTS is_active")
    op.execute("ALTER TABLE IF EXISTS public.sectors DROP COLUMN IF EXISTS is_active")
