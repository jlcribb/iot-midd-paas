"""Create governed topology target bindings for simulated actuation.

Revision ID: 0013
Revises: 0012
"""

from alembic import op


revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The composite key lets the binding reference policy and assets in one
    # project scope; independent UUID references would allow a cross-project
    # row to be constructed by direct SQL.
    op.execute(
        """
        ALTER TABLE public.project_control_policies
        ADD CONSTRAINT project_control_policies_project_id_id_unique UNIQUE (project_id, id)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.project_control_policy_actuation_bindings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            policy_id UUID NOT NULL UNIQUE,
            project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
            source_asset_id UUID NOT NULL,
            target_asset_id UUID NOT NULL,
            control_point TEXT NOT NULL,
            operation TEXT NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT project_control_policy_actuation_bindings_control_point_not_blank
                CHECK (btrim(control_point) <> ''),
            CONSTRAINT project_control_policy_actuation_bindings_operation_valid
                CHECK (operation IN ('set', 'increase', 'decrease', 'toggle')),
            CONSTRAINT project_control_policy_actuation_bindings_policy_project_fkey
                FOREIGN KEY (project_id, policy_id)
                REFERENCES public.project_control_policies(project_id, id) ON DELETE CASCADE,
            CONSTRAINT project_control_policy_actuation_bindings_source_project_fkey
                FOREIGN KEY (project_id, source_asset_id)
                REFERENCES public.assets(project_id, id) ON DELETE RESTRICT,
            CONSTRAINT project_control_policy_actuation_bindings_target_project_fkey
                FOREIGN KEY (project_id, target_asset_id)
                REFERENCES public.assets(project_id, id) ON DELETE RESTRICT
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_control_policy_actuation_bindings_project_target
        ON public.project_control_policy_actuation_bindings(project_id, target_asset_id)
        WHERE enabled = TRUE
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_project_control_policy_actuation_bindings_updated_at
        BEFORE UPDATE ON public.project_control_policy_actuation_bindings
        FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )
    op.execute(
        """
        ALTER TABLE public.control_actuation_delivery_intents
        ADD COLUMN IF NOT EXISTS control_point TEXT NULL,
        ADD COLUMN IF NOT EXISTS actuation_binding_id UUID NULL,
        ADD COLUMN IF NOT EXISTS actuation_binding_version INTEGER NULL
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE public.control_actuation_delivery_intents
        DROP COLUMN IF EXISTS actuation_binding_version,
        DROP COLUMN IF EXISTS actuation_binding_id,
        DROP COLUMN IF EXISTS control_point
        """
    )
    op.execute("DROP TRIGGER IF EXISTS trg_project_control_policy_actuation_bindings_updated_at ON public.project_control_policy_actuation_bindings")
    op.execute("DROP INDEX IF EXISTS public.idx_control_policy_actuation_bindings_project_target")
    op.execute("DROP TABLE IF EXISTS public.project_control_policy_actuation_bindings")
    op.execute("ALTER TABLE public.project_control_policies DROP CONSTRAINT IF EXISTS project_control_policies_project_id_id_unique")
