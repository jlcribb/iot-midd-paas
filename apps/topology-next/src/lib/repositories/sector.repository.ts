import type { QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";
import type { SqlExecutor } from "@/lib/db/tx";
import { buildUpdateSet } from "@/lib/db/sql";
import type { Sector } from "@/lib/dto/sector.dto";
import type { ISectorRepository } from "@/lib/repositories/contracts";
import type { CreateSectorInput, UpdateSectorInput } from "@/lib/validators/sector.schemas";

const ACTIVE_FROM_METADATA_SQL = `
        (
          metadata->>'is_active' IS NULL
          OR lower(metadata->>'is_active') IN ('true', 't', '1', 'yes', 'y', 'on')
        )
`;

function isSchemaCompatibilityError(error: unknown): boolean {
  if (typeof error !== "object" || error === null) {
    return false;
  }
  const code = (error as { code?: string }).code;
  return code === "42703" || code === "42883";
}

function mapSector(row: QueryResultRow): Sector {
  return {
    id: String(row.id),
    project_id: String(row.project_id),
    location_id: row.location_id ? String(row.location_id) : null,
    name: String(row.name),
    code: row.code as string | null,
    description: row.description as string | null,
    metadata: (row.metadata ?? {}) as Record<string, unknown>,
    created_at: String(row.created_at),
    updated_at: String(row.updated_at)
  };
}

export class SectorRepository implements ISectorRepository {
  constructor(private readonly db: SqlExecutor = pool) {}

  private async queryActiveByProject(projectId: string, activeCondition: string): Promise<Sector[]> {
    const result = await this.db.query(
      `
      SELECT *
      FROM sectors
      WHERE project_id = $1::uuid
        AND ${activeCondition}
      ORDER BY created_at DESC
      `,
      [projectId]
    );
    return result.rows.map(mapSector);
  }

  async create(input: CreateSectorInput): Promise<Sector> {
    const result = await this.db.query(
      `
      INSERT INTO sectors (project_id, location_id, name, code, description, metadata)
      VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6::jsonb)
      RETURNING *
      `,
      [
        input.project_id,
        input.location_id ?? null,
        input.name,
        input.code ?? null,
        input.description ?? null,
        JSON.stringify(input.metadata ?? {})
      ]
    );
    return mapSector(result.rows[0]);
  }

  async findById(id: string): Promise<Sector | null> {
    const result = await this.db.query("SELECT * FROM sectors WHERE id = $1::uuid", [id]);
    return result.rows[0] ? mapSector(result.rows[0]) : null;
  }

  async findByProjectId(projectId: string): Promise<Sector[]> {
    const activeConditions = [
      `COALESCE(is_active, true) = true AND ${ACTIVE_FROM_METADATA_SQL}`,
      ACTIVE_FROM_METADATA_SQL,
      "TRUE"
    ];

    let lastError: unknown;
    for (const activeCondition of activeConditions) {
      try {
        return await this.queryActiveByProject(projectId, activeCondition);
      } catch (error) {
        lastError = error;
        if (!isSchemaCompatibilityError(error)) {
          throw error;
        }
      }
    }

    throw lastError;
  }

  async update(id: string, input: UpdateSectorInput): Promise<Sector | null> {
    const payload: Record<string, unknown> = {};
    if (input.location_id !== undefined) payload.location_id = input.location_id ?? null;
    if (input.name !== undefined) payload.name = input.name;
    if (input.code !== undefined) payload.code = input.code ?? null;
    if (input.description !== undefined) payload.description = input.description ?? null;
    if (input.metadata !== undefined) payload.metadata = JSON.stringify(input.metadata ?? {});

    if (Object.keys(payload).length === 0) {
      return this.findById(id);
    }

    const { setClause, values } = buildUpdateSet(payload, {
      startIndex: 2,
      casts: {
        location_id: "uuid",
        metadata: "jsonb"
      }
    });

    const result = await this.db.query(`UPDATE sectors SET ${setClause} WHERE id = $1::uuid RETURNING *`, [id, ...values]);
    return result.rows[0] ? mapSector(result.rows[0]) : null;
  }

  async existsNameInProject(projectId: string, name: string, excludeId?: string): Promise<boolean> {
    const result = await this.db.query(
      `
      SELECT 1
      FROM sectors
      WHERE project_id = $1::uuid
        AND lower(name) = lower($2)
        AND ($3::uuid IS NULL OR id <> $3::uuid)
      LIMIT 1
      `,
      [projectId, name, excludeId ?? null]
    );
    return (result.rowCount ?? 0) > 0;
  }

  async existsCodeInProject(projectId: string, code: string, excludeId?: string): Promise<boolean> {
    const result = await this.db.query(
      `
      SELECT 1
      FROM sectors
      WHERE project_id = $1::uuid
        AND code = $2
        AND ($3::uuid IS NULL OR id <> $3::uuid)
      LIMIT 1
      `,
      [projectId, code, excludeId ?? null]
    );
    return (result.rowCount ?? 0) > 0;
  }

  async softDeactivate(id: string): Promise<Sector | null> {
    try {
      const result = await this.db.query(
        `
        UPDATE sectors
        SET
          is_active = false,
          metadata = COALESCE(metadata, '{}'::jsonb) || '{"is_active": false}'::jsonb
        WHERE id = $1::uuid
        RETURNING *
        `,
        [id]
      );
      return result.rows[0] ? mapSector(result.rows[0]) : null;
    } catch (error) {
      if (!isSchemaCompatibilityError(error)) {
        throw error;
      }

      const fallback = await this.db.query(
        `
        UPDATE sectors
        SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"is_active": false}'::jsonb
        WHERE id = $1::uuid
        RETURNING *
        `,
        [id]
      );
      return fallback.rows[0] ? mapSector(fallback.rows[0]) : null;
    }
  }

  async softDeactivateByProject(projectId: string): Promise<void> {
    try {
      await this.db.query(
        `
        UPDATE sectors
        SET
          is_active = false,
          metadata = COALESCE(metadata, '{}'::jsonb) || '{"is_active": false}'::jsonb
        WHERE project_id = $1::uuid
        `,
        [projectId]
      );
    } catch (error) {
      if (!isSchemaCompatibilityError(error)) {
        throw error;
      }

      await this.db.query(
        `
        UPDATE sectors
        SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"is_active": false}'::jsonb
        WHERE project_id = $1::uuid
        `,
        [projectId]
      );
    }
  }
}
