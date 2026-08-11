"""Bind project control policies to project-scoped topology assets.

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-10 00:00:00.000000
"""

from alembic import op


revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL search_path TO public")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'assets_project_id_id_unique'
            ) THEN
                ALTER TABLE public.assets
                ADD CONSTRAINT assets_project_id_id_unique UNIQUE (project_id, id);
            END IF;
        END $$
        """
    )
    op.execute(
        """
        ALTER TABLE public.project_control_policies
        ADD COLUMN IF NOT EXISTS bound_asset_id UUID NULL
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'project_control_policies_bound_asset_project_fkey'
            ) THEN
                ALTER TABLE public.project_control_policies
                ADD CONSTRAINT project_control_policies_bound_asset_project_fkey
                FOREIGN KEY (project_id, bound_asset_id)
                REFERENCES public.assets(project_id, id)
                ON DELETE RESTRICT;
            END IF;
        END $$
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_project_control_policies_bound_asset_variable_enabled
        ON public.project_control_policies(project_id, bound_asset_id, variable, enabled)
        """
    )
    op.execute(
        """
        COMMENT ON COLUMN public.project_control_policies.bound_asset_id
        IS 'Canonical project-scoped topology asset governed by this policy; NULL marks legacy/unbound compatibility rows'
        """
    )


def downgrade() -> None:
    op.execute("SET LOCAL search_path TO public")
    op.execute(
        "DROP INDEX IF EXISTS public.idx_project_control_policies_bound_asset_variable_enabled"
    )
    op.execute(
        "ALTER TABLE public.project_control_policies DROP CONSTRAINT IF EXISTS project_control_policies_bound_asset_project_fkey"
    )
    op.execute(
        "ALTER TABLE public.project_control_policies DROP COLUMN IF EXISTS bound_asset_id"
    )
    op.execute(
        "ALTER TABLE public.assets DROP CONSTRAINT IF EXISTS assets_project_id_id_unique"
    )
