import type { QueryResultRow } from "pg";
import type { SqlExecutor } from "@/lib/db/tx";
import { pool } from "@/lib/db/pool";
import { buildUpdateSet } from "@/lib/db/sql";
import type { Project } from "@/lib/dto/project.dto";
import type { IProjectRepository } from "@/lib/repositories/contracts";
import type { CreateProjectInput, UpdateProjectInput } from "@/lib/validators/project.schemas";

function mapProject(row: QueryResultRow): Project {
  return {
    id: String(row.id),
    name: String(row.name),
    description: row.description as string | null,
    status: row.status as Project["status"],
    metadata: (row.metadata ?? {}) as Record<string, unknown>,
    created_at: String(row.created_at),
    updated_at: String(row.updated_at)
  };
}

export class ProjectRepository implements IProjectRepository {
  constructor(private readonly db: SqlExecutor = pool) {}

  async create(input: CreateProjectInput): Promise<Project> {
    const result = await this.db.query(
      `
      INSERT INTO projects (name, description, status, metadata)
      VALUES ($1, $2, $3::project_status_enum, $4::jsonb)
      RETURNING *
      `,
      [input.name, input.description ?? null, input.status, JSON.stringify(input.metadata ?? {})]
    );
    return mapProject(result.rows[0]);
  }

  async findById(id: string): Promise<Project | null> {
    const result = await this.db.query("SELECT * FROM projects WHERE id = $1::uuid", [id]);
    return result.rows[0] ? mapProject(result.rows[0]) : null;
  }

  async findAll(filters?: { status?: Project["status"] }): Promise<Project[]> {
    if (filters?.status) {
      const result = await this.db.query(
        "SELECT * FROM projects WHERE status = $1::project_status_enum ORDER BY created_at DESC",
        [filters.status]
      );
      return result.rows.map(mapProject);
    }
    const result = await this.db.query("SELECT * FROM projects ORDER BY created_at DESC");
    return result.rows.map(mapProject);
  }

  async update(id: string, input: UpdateProjectInput): Promise<Project | null> {
    const payload: Record<string, unknown> = {};
    if (input.name !== undefined) payload.name = input.name;
    if (input.description !== undefined) payload.description = input.description ?? null;
    if (input.status !== undefined) payload.status = input.status;
    if (input.metadata !== undefined) payload.metadata = JSON.stringify(input.metadata ?? {});

    if (Object.keys(payload).length === 0) {
      return this.findById(id);
    }

    const { setClause, values } = buildUpdateSet(payload, {
      startIndex: 2,
      casts: {
        status: "project_status_enum",
        metadata: "jsonb"
      }
    });

    const result = await this.db.query(`UPDATE projects SET ${setClause} WHERE id = $1::uuid RETURNING *`, [id, ...values]);
    return result.rows[0] ? mapProject(result.rows[0]) : null;
  }
}
