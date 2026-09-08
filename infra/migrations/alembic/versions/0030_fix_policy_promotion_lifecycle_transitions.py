"""Fix policy promotion lifecycle transition constraints.

Revision ID: 0030
Revises: 0029
"""
from alembic import op

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE public.control_policy_promotion_proposals DROP CONSTRAINT IF EXISTS control_policy_promotion_proposals_status_check")
    op.execute("ALTER TABLE public.control_policy_promotion_proposals ADD CONSTRAINT control_policy_promotion_proposals_status_check CHECK (status IN ('CREATED','VALIDATION_PENDING','VALIDATED','VALIDATION_FAILED','BLOCKED'))")
    op.execute("""CREATE OR REPLACE FUNCTION public.enforce_control_policy_promotion_immutable() RETURNS TRIGGER AS $$
    BEGIN
      IF TG_TABLE_NAME='control_policy_promotion_proposals'
         AND to_jsonb(NEW)-'status'=to_jsonb(OLD)-'status'
         AND ((OLD.status='CREATED' AND NEW.status='VALIDATION_PENDING')
              OR (OLD.status='VALIDATION_PENDING' AND NEW.status IN ('VALIDATED','VALIDATION_FAILED','BLOCKED')))
      THEN RETURN NEW; END IF;
      RAISE EXCEPTION 'policy promotion evidence is immutable';
    END; $$ LANGUAGE plpgsql""")


def downgrade() -> None:
    op.execute("ALTER TABLE public.control_policy_promotion_proposals DROP CONSTRAINT IF EXISTS control_policy_promotion_proposals_status_check")
    op.execute("ALTER TABLE public.control_policy_promotion_proposals ADD CONSTRAINT control_policy_promotion_proposals_status_check CHECK (status='CREATED')")
    op.execute("""CREATE OR REPLACE FUNCTION public.enforce_control_policy_promotion_immutable() RETURNS TRIGGER AS $$
    BEGIN
      IF TG_TABLE_NAME='control_policy_promotion_proposals' AND OLD.status='CREATED' AND NEW.status IN ('VALIDATED','VALIDATION_FAILED','BLOCKED') AND to_jsonb(NEW)-'status'=to_jsonb(OLD)-'status' THEN RETURN NEW; END IF;
      RAISE EXCEPTION 'policy promotion evidence is immutable';
    END; $$ LANGUAGE plpgsql""")
