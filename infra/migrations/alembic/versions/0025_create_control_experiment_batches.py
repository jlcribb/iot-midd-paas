"""Create governed, immutable-membership experiment batches.

Revision ID: 0025
Revises: 0024
"""
from alembic import op

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE public.control_experiment_batches (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      search_space_id UUID NOT NULL REFERENCES public.control_strategy_search_spaces(id) ON DELETE RESTRICT,
      base_session_id UUID NOT NULL REFERENCES public.control_simulation_sessions(id) ON DELETE RESTRICT,
      base_experiment_fingerprint TEXT NOT NULL CHECK (base_experiment_fingerprint ~ '^[0-9a-f]{64}$'),
      evaluation_profile_id UUID NULL REFERENCES public.control_evaluation_profiles(id) ON DELETE RESTRICT,
      evaluation_profile_version INTEGER NULL CHECK (evaluation_profile_version > 0),
      name TEXT NOT NULL CHECK (btrim(name) <> ''), description TEXT NOT NULL DEFAULT '',
      batch_hash TEXT NOT NULL CHECK (batch_hash ~ '^[0-9a-f]{64}$'),
      status TEXT NOT NULL CHECK (status IN ('READY','RUNNING','COMPLETED','COMPLETED_WITH_WARNINGS','PARTIALLY_FAILED','FAILED')),
      total_items INTEGER NOT NULL CHECK (total_items > 0), pending_items INTEGER NOT NULL DEFAULT 0 CHECK (pending_items >= 0),
      running_items INTEGER NOT NULL DEFAULT 0 CHECK (running_items >= 0), completed_items INTEGER NOT NULL DEFAULT 0 CHECK (completed_items >= 0),
      completed_with_warnings_items INTEGER NOT NULL DEFAULT 0 CHECK (completed_with_warnings_items >= 0),
      not_evaluable_items INTEGER NOT NULL DEFAULT 0 CHECK (not_evaluable_items >= 0), failed_items INTEGER NOT NULL DEFAULT 0 CHECK (failed_items >= 0),
      schema_version INTEGER NOT NULL CHECK (schema_version = 1), orchestrator_version TEXT NOT NULL,
      created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), started_at TIMESTAMPTZ NULL, completed_at TIMESTAMPTZ NULL,
      physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK (physical_effects_allowed = FALSE),
      CONSTRAINT control_experiment_batch_hash_unique UNIQUE (project_id, batch_hash),
      CONSTRAINT control_experiment_batch_counts_consistent CHECK (pending_items + running_items + completed_items + completed_with_warnings_items + not_evaluable_items + failed_items = total_items),
      CONSTRAINT control_experiment_batch_evaluation_version CHECK ((evaluation_profile_id IS NULL AND evaluation_profile_version IS NULL) OR (evaluation_profile_id IS NOT NULL AND evaluation_profile_version IS NOT NULL))
    )""")
    op.execute("""CREATE TABLE public.control_experiment_batch_items (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), batch_id UUID NOT NULL REFERENCES public.control_experiment_batches(id) ON DELETE RESTRICT,
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      candidate_id UUID NOT NULL REFERENCES public.control_strategy_candidates(id) ON DELETE RESTRICT, candidate_hash TEXT NOT NULL CHECK (candidate_hash ~ '^[0-9a-f]{64}$'),
      item_index INTEGER NOT NULL CHECK (item_index > 0), status TEXT NOT NULL CHECK (status IN ('PENDING','RUNNING','COMPLETED','COMPLETED_WITH_WARNINGS','NOT_EVALUABLE','FAILED')),
      simulation_session_id UUID NULL REFERENCES public.control_simulation_sessions(id) ON DELETE RESTRICT,
      experiment_fingerprint TEXT NULL CHECK (experiment_fingerprint IS NULL OR experiment_fingerprint ~ '^[0-9a-f]{64}$'),
      simulation_run_id UUID NULL REFERENCES public.control_simulation_runs(id) ON DELETE RESTRICT,
      simulation_result_id UUID NULL REFERENCES public.control_simulation_results(id) ON DELETE RESTRICT,
      result_fingerprint TEXT NULL CHECK (result_fingerprint IS NULL OR result_fingerprint ~ '^[0-9a-f]{64}$'),
      trace_id UUID NULL REFERENCES public.control_simulation_traces(id) ON DELETE RESTRICT, trace_hash TEXT NULL CHECK (trace_hash IS NULL OR trace_hash ~ '^[0-9a-f]{64}$'),
      evaluation_id UUID NULL REFERENCES public.control_experiment_evaluations(id) ON DELETE RESTRICT, evaluation_hash TEXT NULL CHECK (evaluation_hash IS NULL OR evaluation_hash ~ '^[0-9a-f]{64}$'),
      attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0), last_error_code TEXT NULL, last_error_summary TEXT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), started_at TIMESTAMPTZ NULL, completed_at TIMESTAMPTZ NULL,
      CONSTRAINT control_experiment_batch_item_index_unique UNIQUE (batch_id, item_index),
      CONSTRAINT control_experiment_batch_item_candidate_unique UNIQUE (batch_id, candidate_id),
      CONSTRAINT control_experiment_batch_item_session_unique UNIQUE (simulation_session_id)
    )""")
    op.execute("CREATE INDEX idx_control_experiment_batches_project_created ON public.control_experiment_batches(project_id, created_at DESC, id DESC)")
    op.execute("CREATE INDEX idx_control_experiment_batch_items_batch_status ON public.control_experiment_batch_items(batch_id, status, item_index)")
    op.execute("""CREATE OR REPLACE FUNCTION public.enforce_control_experiment_batch_membership_immutable() RETURNS TRIGGER AS $$
      BEGIN
        IF TG_TABLE_NAME='control_experiment_batches' AND (to_jsonb(OLD)->>'project_id' IS DISTINCT FROM to_jsonb(NEW)->>'project_id' OR to_jsonb(OLD)->>'search_space_id' IS DISTINCT FROM to_jsonb(NEW)->>'search_space_id' OR to_jsonb(OLD)->>'base_session_id' IS DISTINCT FROM to_jsonb(NEW)->>'base_session_id' OR to_jsonb(OLD)->>'base_experiment_fingerprint' IS DISTINCT FROM to_jsonb(NEW)->>'base_experiment_fingerprint' OR to_jsonb(OLD)->>'evaluation_profile_id' IS DISTINCT FROM to_jsonb(NEW)->>'evaluation_profile_id' OR to_jsonb(OLD)->>'evaluation_profile_version' IS DISTINCT FROM to_jsonb(NEW)->>'evaluation_profile_version' OR to_jsonb(OLD)->>'batch_hash' IS DISTINCT FROM to_jsonb(NEW)->>'batch_hash') THEN RAISE EXCEPTION 'experiment batch definition is immutable'; END IF;
        IF TG_TABLE_NAME='control_experiment_batch_items' AND (to_jsonb(OLD)->>'batch_id' IS DISTINCT FROM to_jsonb(NEW)->>'batch_id' OR to_jsonb(OLD)->>'project_id' IS DISTINCT FROM to_jsonb(NEW)->>'project_id' OR to_jsonb(OLD)->>'candidate_id' IS DISTINCT FROM to_jsonb(NEW)->>'candidate_id' OR to_jsonb(OLD)->>'candidate_hash' IS DISTINCT FROM to_jsonb(NEW)->>'candidate_hash' OR to_jsonb(OLD)->>'item_index' IS DISTINCT FROM to_jsonb(NEW)->>'item_index') THEN RAISE EXCEPTION 'experiment batch membership is immutable'; END IF;
        RETURN NEW;
      END; $$ LANGUAGE plpgsql""")
    op.execute("CREATE TRIGGER trg_control_experiment_batches_membership_immutable BEFORE UPDATE ON public.control_experiment_batches FOR EACH ROW EXECUTE FUNCTION public.enforce_control_experiment_batch_membership_immutable()")
    op.execute("CREATE TRIGGER trg_control_experiment_batch_items_membership_immutable BEFORE UPDATE ON public.control_experiment_batch_items FOR EACH ROW EXECUTE FUNCTION public.enforce_control_experiment_batch_membership_immutable()")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_control_experiment_batch_items_membership_immutable ON public.control_experiment_batch_items")
    op.execute("DROP TRIGGER IF EXISTS trg_control_experiment_batches_membership_immutable ON public.control_experiment_batches")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_control_experiment_batch_membership_immutable()")
    op.execute("DROP TABLE IF EXISTS public.control_experiment_batch_items")
    op.execute("DROP TABLE IF EXISTS public.control_experiment_batches")
