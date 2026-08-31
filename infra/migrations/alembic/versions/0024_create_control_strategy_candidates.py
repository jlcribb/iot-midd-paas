"""Create immutable, deterministic strategy search spaces and candidates.

Revision ID: 0024
Revises: 0023
"""
from alembic import op

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE public.control_strategy_search_spaces (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      name TEXT NOT NULL CHECK (btrim(name) <> ''),
      description TEXT NOT NULL DEFAULT '',
      strategy_type TEXT NOT NULL CHECK (strategy_type IN ('proportional', 'threshold')),
      parameter_schema_version INTEGER NOT NULL CHECK (parameter_schema_version = 1),
      generation_method TEXT NOT NULL CHECK (generation_method = 'GRID'),
      search_space_definition JSONB NOT NULL CHECK (jsonb_typeof(search_space_definition) = 'object'),
      search_space_hash TEXT NOT NULL CHECK (search_space_hash ~ '^[0-9a-f]{64}$'),
      raw_combination_count INTEGER NOT NULL CHECK (raw_combination_count > 0),
      candidate_count INTEGER NOT NULL CHECK (candidate_count >= 0),
      invalid_combination_count INTEGER NOT NULL CHECK (invalid_combination_count >= 0),
      invalid_combination_summary JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(invalid_combination_summary) = 'array'),
      status TEXT NOT NULL CHECK (status = 'GENERATED'),
      schema_version INTEGER NOT NULL CHECK (schema_version = 1),
      generator_version TEXT NOT NULL CHECK (btrim(generator_version) <> ''),
      created_by TEXT NOT NULL CHECK (btrim(created_by) <> ''),
      physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK (physical_effects_allowed = FALSE),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      CONSTRAINT control_strategy_search_space_semantic_unique UNIQUE (project_id, search_space_hash),
      CONSTRAINT control_strategy_search_space_counts_consistent CHECK (candidate_count + invalid_combination_count = raw_combination_count)
    )""")
    op.execute("""CREATE TABLE public.control_strategy_candidates (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      search_space_id UUID NOT NULL REFERENCES public.control_strategy_search_spaces(id) ON DELETE RESTRICT,
      strategy_type TEXT NOT NULL CHECK (strategy_type IN ('proportional', 'threshold')),
      parameters JSONB NOT NULL CHECK (jsonb_typeof(parameters) = 'object'),
      candidate_index INTEGER NOT NULL CHECK (candidate_index > 0),
      candidate_hash TEXT NOT NULL CHECK (candidate_hash ~ '^[0-9a-f]{64}$'),
      source TEXT NOT NULL CHECK (source = 'GRID_SEARCH'),
      schema_version INTEGER NOT NULL CHECK (schema_version = 1),
      generator_version TEXT NOT NULL CHECK (btrim(generator_version) <> ''),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      CONSTRAINT control_strategy_candidate_index_unique UNIQUE (search_space_id, candidate_index),
      CONSTRAINT control_strategy_candidate_hash_unique UNIQUE (search_space_id, candidate_hash)
    )""")
    op.execute("CREATE INDEX idx_control_strategy_search_spaces_project_created ON public.control_strategy_search_spaces(project_id, created_at DESC, id DESC)")
    op.execute("CREATE INDEX idx_control_strategy_candidates_project_space_index ON public.control_strategy_candidates(project_id, search_space_id, candidate_index)")
    op.execute("CREATE INDEX idx_control_strategy_candidates_hash ON public.control_strategy_candidates(candidate_hash)")
    op.execute("""CREATE OR REPLACE FUNCTION public.enforce_control_strategy_search_space_immutable() RETURNS TRIGGER AS $$
      BEGIN RAISE EXCEPTION 'strategy search spaces and candidates are immutable'; END; $$ LANGUAGE plpgsql""")
    op.execute("CREATE TRIGGER trg_control_strategy_search_spaces_immutable BEFORE UPDATE ON public.control_strategy_search_spaces FOR EACH ROW EXECUTE FUNCTION public.enforce_control_strategy_search_space_immutable()")
    op.execute("CREATE TRIGGER trg_control_strategy_candidates_immutable BEFORE UPDATE ON public.control_strategy_candidates FOR EACH ROW EXECUTE FUNCTION public.enforce_control_strategy_search_space_immutable()")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_control_strategy_candidates_immutable ON public.control_strategy_candidates")
    op.execute("DROP TRIGGER IF EXISTS trg_control_strategy_search_spaces_immutable ON public.control_strategy_search_spaces")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_control_strategy_search_space_immutable()")
    op.execute("DROP TABLE IF EXISTS public.control_strategy_candidates")
    op.execute("DROP TABLE IF EXISTS public.control_strategy_search_spaces")
