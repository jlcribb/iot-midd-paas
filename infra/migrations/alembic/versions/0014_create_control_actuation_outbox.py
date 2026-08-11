"""Create transactional outbox for simulated actuation dispatch."""
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE public.control_actuation_outbox (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), event_id UUID NOT NULL UNIQUE,
      event_type TEXT NOT NULL, schema_version TEXT NOT NULL, aggregate_type TEXT NOT NULL,
      command_id UUID NOT NULL, recommendation_id TEXT NOT NULL, correlation_id TEXT NOT NULL,
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
      target_asset_id UUID, control_point TEXT, binding_id UUID, binding_version INTEGER,
      routing_key TEXT NOT NULL, payload JSONB NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
      attempt_count INTEGER NOT NULL DEFAULT 0, available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      claimed_at TIMESTAMPTZ, lease_until TIMESTAMPTZ, published_at TIMESTAMPTZ,
      last_error TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      CONSTRAINT control_actuation_outbox_status_valid CHECK (status IN ('pending','publishing','published','failed')),
      CONSTRAINT control_actuation_outbox_attempt_nonnegative CHECK (attempt_count >= 0),
      CONSTRAINT control_actuation_outbox_command_event_unique UNIQUE (command_id, event_type)
    )
    """)
    op.execute("CREATE INDEX idx_control_actuation_outbox_claim ON public.control_actuation_outbox(status, available_at) WHERE status IN ('pending','publishing')")
    op.execute("CREATE TRIGGER trg_control_actuation_outbox_updated_at BEFORE UPDATE ON public.control_actuation_outbox FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_control_actuation_outbox_updated_at ON public.control_actuation_outbox")
    op.execute("DROP TABLE IF EXISTS public.control_actuation_outbox")
