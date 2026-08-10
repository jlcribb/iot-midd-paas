"""Create persistent project-scoped control memberships.

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-10 00:00:00.000000
"""

from alembic import op


revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL search_path TO public")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.project_control_memberships (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            actor_email TEXT NOT NULL,
            project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT project_control_memberships_actor_email_normalized
                CHECK (actor_email = lower(btrim(actor_email)) AND btrim(actor_email) <> ''),
            CONSTRAINT project_control_memberships_role_valid
                CHECK (role IN ('viewer', 'operator', 'admin')),
            CONSTRAINT project_control_memberships_actor_project_unique
                UNIQUE (actor_email, project_id)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_project_control_memberships_actor_enabled
        ON public.project_control_memberships(actor_email, enabled, project_id)
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_project_control_memberships_updated_at
        BEFORE UPDATE ON public.project_control_memberships
        FOR EACH ROW
        EXECUTE FUNCTION public.set_updated_at()
        """
    )
    op.execute(
        """
        COMMENT ON TABLE public.project_control_memberships
        IS 'Persistent OAuth actor scope for project-scoped parametric control governance'
        """
    )


def downgrade() -> None:
    op.execute("SET LOCAL search_path TO public")
    op.execute("DROP TRIGGER IF EXISTS trg_project_control_memberships_updated_at ON public.project_control_memberships")
    op.execute("DROP TABLE IF EXISTS public.project_control_memberships")
