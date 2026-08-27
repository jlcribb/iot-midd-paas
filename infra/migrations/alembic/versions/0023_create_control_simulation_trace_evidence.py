"""Create immutable, experiment-scoped simulation process traces.

Revision ID: 0023
Revises: 0022
"""
from alembic import op

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("""CREATE TABLE public.control_simulation_traces (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      simulation_run_id UUID NOT NULL UNIQUE REFERENCES public.control_simulation_runs(id) ON DELETE RESTRICT,
      simulation_result_id UUID NOT NULL UNIQUE REFERENCES public.control_simulation_results(id) ON DELETE RESTRICT,
      trace_schema_version INTEGER NOT NULL CHECK (trace_schema_version = 1),
      time_representation TEXT NOT NULL CHECK (time_representation = 'elapsed_seconds_from_first_virtual_timestamp:v1'),
      trace_hash TEXT NOT NULL CHECK (trace_hash ~ '^[0-9a-f]{64}$'),
      point_count INTEGER NOT NULL CHECK (point_count > 0),
      simulation_duration_seconds NUMERIC(18, 9) NOT NULL CHECK (simulation_duration_seconds >= 0),
      physical_effects_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK (physical_effects_allowed = FALSE),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    op.execute("""CREATE TABLE public.control_simulation_trace_points (
      id BIGSERIAL PRIMARY KEY,
      trace_id UUID NOT NULL REFERENCES public.control_simulation_traces(id) ON DELETE CASCADE,
      sequence_number INTEGER NOT NULL CHECK (sequence_number > 0),
      simulation_time_seconds NUMERIC(18, 9) NOT NULL CHECK (simulation_time_seconds >= 0),
      process_value NUMERIC(18, 9) NOT NULL,
      setpoint NUMERIC(18, 9) NOT NULL,
      control_output NUMERIC(18, 9) NOT NULL,
      actuator_state TEXT NOT NULL CHECK (btrim(actuator_state) <> ''),
      constraint_state TEXT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata) = 'object'),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      CONSTRAINT control_simulation_trace_points_order_unique UNIQUE (trace_id, sequence_number)
    )""")
    op.execute("CREATE INDEX idx_control_simulation_traces_project_hash ON public.control_simulation_traces(project_id, trace_hash)")
    op.execute("CREATE INDEX idx_control_simulation_trace_points_trace_sequence ON public.control_simulation_trace_points(trace_id, sequence_number)")
    op.execute("""CREATE OR REPLACE FUNCTION public.enforce_control_simulation_trace_immutable() RETURNS TRIGGER AS $$
      BEGIN RAISE EXCEPTION 'simulation trace evidence is immutable'; END; $$ LANGUAGE plpgsql""")
    op.execute("CREATE TRIGGER trg_control_simulation_traces_immutable BEFORE UPDATE ON public.control_simulation_traces FOR EACH ROW EXECUTE FUNCTION public.enforce_control_simulation_trace_immutable()")
    op.execute("CREATE TRIGGER trg_control_simulation_trace_points_immutable BEFORE UPDATE ON public.control_simulation_trace_points FOR EACH ROW EXECUTE FUNCTION public.enforce_control_simulation_trace_immutable()")

def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_control_simulation_trace_points_immutable ON public.control_simulation_trace_points")
    op.execute("DROP TRIGGER IF EXISTS trg_control_simulation_traces_immutable ON public.control_simulation_traces")
    op.execute("DROP FUNCTION IF EXISTS public.enforce_control_simulation_trace_immutable()")
    op.execute("DROP INDEX IF EXISTS public.idx_control_simulation_trace_points_trace_sequence")
    op.execute("DROP INDEX IF EXISTS public.idx_control_simulation_traces_project_hash")
    op.execute("DROP TABLE IF EXISTS public.control_simulation_trace_points")
    op.execute("DROP TABLE IF EXISTS public.control_simulation_traces")
