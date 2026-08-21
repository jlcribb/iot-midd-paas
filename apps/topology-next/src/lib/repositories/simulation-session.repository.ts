import type { QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";
import type { SqlExecutor } from "@/lib/db/tx";
import type { CreateSimulationSessionInput, SimulationSession } from "@/lib/dto/simulation-session.dto";

function mapSession(row: QueryResultRow): SimulationSession {
  return {
    id: String(row.id),
    project_id: String(row.project_id),
    execution_context: "SIMULATION",
    status: row.status as SimulationSession["status"],
    created_by: String(row.created_by),
    snapshot_refs: (row.snapshot_refs ?? {}) as Record<string, unknown>,
    metadata: (row.metadata ?? {}) as Record<string, unknown>,
    created_at: String(row.created_at),
    started_at: row.started_at ? String(row.started_at) : null,
    completed_at: row.completed_at ? String(row.completed_at) : null
  };
}

export class SimulationSessionRepository {
  constructor(private readonly db: SqlExecutor = pool) {}

  async create(projectId: string, createdBy: string, input: CreateSimulationSessionInput): Promise<SimulationSession> {
    const result = await this.db.query(
      `INSERT INTO public.control_simulation_sessions
        (project_id, execution_context, status, created_by, snapshot_refs, metadata)
       VALUES ($1::uuid, 'SIMULATION', 'DRAFT', $2, $3::jsonb, $4::jsonb)
       RETURNING *`,
      [projectId, createdBy, JSON.stringify(input.snapshot_refs ?? {}), JSON.stringify(input.metadata ?? {})]
    );
    return mapSession(result.rows[0]);
  }

  async findByProjectAndId(projectId: string, sessionId: string): Promise<SimulationSession | null> {
    const result = await this.db.query(
      "SELECT * FROM public.control_simulation_sessions WHERE project_id = $1::uuid AND id = $2::uuid",
      [projectId, sessionId]
    );
    return result.rows[0] ? mapSession(result.rows[0]) : null;
  }

  async listByProject(projectId: string): Promise<SimulationSession[]> {
    const result = await this.db.query(
      "SELECT * FROM public.control_simulation_sessions WHERE project_id = $1::uuid ORDER BY created_at DESC, id DESC",
      [projectId]
    );
    return result.rows.map(mapSession);
  }
}
