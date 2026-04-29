"""Add parametric_control_enabled to public.projects.

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-28 00:00:00.000000
"""

from alembic import op


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL search_path TO public")
    op.execute(
        """
        ALTER TABLE IF EXISTS public.projects
        ADD COLUMN IF NOT EXISTS parametric_control_enabled boolean NOT NULL DEFAULT false
        """
    )
    op.execute(
        """
        COMMENT ON COLUMN public.projects.parametric_control_enabled
        IS 'Feature flag operativo del parametric-control-engine por proyecto'
        """
    )


def downgrade() -> None:
    op.execute("SET LOCAL search_path TO public")
    op.execute(
        """
        ALTER TABLE IF EXISTS public.projects
        DROP COLUMN IF EXISTS parametric_control_enabled
        """
    )
