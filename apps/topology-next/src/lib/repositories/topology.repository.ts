import type { QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";
import type { SqlExecutor } from "@/lib/db/tx";
import { buildUpdateSet } from "@/lib/db/sql";
import type { TopologyLink } from "@/lib/dto/topology.dto";
import type { ITopologyRepository } from "@/lib/repositories/contracts";
import type {
  CreateTopologyLinkInput,
  UpdateTopologyLinkInput
} from "@/lib/validators/topology.schemas";

function mapTopology(row: QueryResultRow): TopologyLink {
  return {
    id: String(row.id),
    project_id: String(row.project_id),
    source_asset_id: row.source_asset_id ? String(row.source_asset_id) : null,
    target_asset_id: row.target_asset_id ? String(row.target_asset_id) : null,
    source_sector_id: row.source_sector_id ? String(row.source_sector_id) : null,
    target_sector_id: row.target_sector_id ? String(row.target_sector_id) : null,
    relation_type: row.relation_type as TopologyLink["relation_type"],
    connection_medium: row.connection_medium as string | null,
    protocol: row.protocol as string | null,
    ports: (row.ports ?? []) as unknown[],
    link_quality: row.link_quality === null ? null : Number(row.link_quality),
    status: row.status as TopologyLink["status"],
    metadata: (row.metadata ?? {}) as Record<string, unknown>,
    created_at: String(row.created_at),
    updated_at: String(row.updated_at)
  };
}

export class TopologyRepository implements ITopologyRepository {
  constructor(private readonly db: SqlExecutor = pool) {}

  async create(input: CreateTopologyLinkInput): Promise<TopologyLink> {
    const result = await this.db.query(
      `
      INSERT INTO topology_links (
        project_id, source_asset_id, target_asset_id, source_sector_id, target_sector_id,
        relation_type, connection_medium, protocol, ports, link_quality, status, metadata
      )
      VALUES (
        $1::uuid, $2::uuid, $3::uuid, $4::uuid, $5::uuid,
        $6::topology_relation_enum, $7, $8, $9::jsonb, $10, $11::link_status_enum, $12::jsonb
      )
      RETURNING *
      `,
      [
        input.project_id,
        input.source_asset_id ?? null,
        input.target_asset_id ?? null,
        input.source_sector_id ?? null,
        input.target_sector_id ?? null,
        input.relation_type,
        input.connection_medium ?? null,
        input.protocol ?? null,
        JSON.stringify(input.ports ?? []),
        input.link_quality ?? null,
        input.status,
        JSON.stringify(input.metadata ?? {})
      ]
    );
    return mapTopology(result.rows[0]);
  }

  async findById(id: string): Promise<TopologyLink | null> {
    const result = await this.db.query("SELECT * FROM topology_links WHERE id = $1::uuid", [id]);
    return result.rows[0] ? mapTopology(result.rows[0]) : null;
  }

  async findByProjectId(projectId: string): Promise<TopologyLink[]> {
    const result = await this.db.query(
      "SELECT * FROM topology_links WHERE project_id = $1::uuid ORDER BY created_at DESC",
      [projectId]
    );
    return result.rows.map(mapTopology);
  }

  async findByAssetId(assetId: string): Promise<TopologyLink[]> {
    const result = await this.db.query(
      `
      SELECT *
      FROM topology_links
      WHERE source_asset_id = $1::uuid OR target_asset_id = $1::uuid
      ORDER BY created_at DESC
      `,
      [assetId]
    );
    return result.rows.map(mapTopology);
  }

  async update(id: string, input: UpdateTopologyLinkInput): Promise<TopologyLink | null> {
    const payload: Record<string, unknown> = {};
    for (const key of [
      "source_asset_id",
      "target_asset_id",
      "source_sector_id",
      "target_sector_id",
      "relation_type",
      "connection_medium",
      "protocol",
      "link_quality",
      "status"
    ] as const) {
      if (input[key] !== undefined) {
        payload[key] = input[key] ?? null;
      }
    }
    if (input.ports !== undefined) payload.ports = JSON.stringify(input.ports ?? []);
    if (input.metadata !== undefined) payload.metadata = JSON.stringify(input.metadata ?? {});

    if (Object.keys(payload).length === 0) {
      return this.findById(id);
    }

    const { setClause, values } = buildUpdateSet(payload, {
      startIndex: 2,
      casts: {
        source_asset_id: "uuid",
        target_asset_id: "uuid",
        source_sector_id: "uuid",
        target_sector_id: "uuid",
        relation_type: "topology_relation_enum",
        status: "link_status_enum",
        ports: "jsonb",
        metadata: "jsonb"
      }
    });

    const result = await this.db.query(`UPDATE topology_links SET ${setClause} WHERE id = $1::uuid RETURNING *`, [id, ...values]);
    return result.rows[0] ? mapTopology(result.rows[0]) : null;
  }

  async delete(id: string): Promise<boolean> {
    const result = await this.db.query("DELETE FROM topology_links WHERE id = $1::uuid", [id]);
    return (result.rowCount ?? 0) > 0;
  }

  async existsExactRelation(
    projectId: string,
    relationType: string,
    sourceAssetId: string | null,
    sourceSectorId: string | null,
    targetAssetId: string | null,
    targetSectorId: string | null,
    excludeId?: string
  ): Promise<boolean> {
    const result = await this.db.query(
      `
      SELECT 1
      FROM topology_links
      WHERE project_id = $1::uuid
        AND relation_type = $2::topology_relation_enum
        AND COALESCE(source_asset_id, '00000000-0000-0000-0000-000000000000'::uuid)
            = COALESCE($3::uuid, '00000000-0000-0000-0000-000000000000'::uuid)
        AND COALESCE(source_sector_id, '00000000-0000-0000-0000-000000000000'::uuid)
            = COALESCE($4::uuid, '00000000-0000-0000-0000-000000000000'::uuid)
        AND COALESCE(target_asset_id, '00000000-0000-0000-0000-000000000000'::uuid)
            = COALESCE($5::uuid, '00000000-0000-0000-0000-000000000000'::uuid)
        AND COALESCE(target_sector_id, '00000000-0000-0000-0000-000000000000'::uuid)
            = COALESCE($6::uuid, '00000000-0000-0000-0000-000000000000'::uuid)
        AND ($7::uuid IS NULL OR id <> $7::uuid)
      LIMIT 1
      `,
      [projectId, relationType, sourceAssetId, sourceSectorId, targetAssetId, targetSectorId, excludeId ?? null]
    );
    return (result.rowCount ?? 0) > 0;
  }

  async deactivateByProject(projectId: string): Promise<void> {
    await this.db.query(
      `
      UPDATE topology_links
      SET
        status = 'inactive'::link_status_enum,
        metadata = COALESCE(metadata, '{}'::jsonb) || '{"is_active": false}'::jsonb
      WHERE project_id = $1::uuid
      `,
      [projectId]
    );
  }

  async deactivateBySectorAndAssets(sectorId: string, assetIds: string[]): Promise<void> {
    await this.db.query(
      `
      UPDATE topology_links
      SET
        status = 'inactive'::link_status_enum,
        metadata = COALESCE(metadata, '{}'::jsonb) || '{"is_active": false}'::jsonb
      WHERE source_sector_id = $1::uuid
         OR target_sector_id = $1::uuid
         OR source_asset_id = ANY($2::uuid[])
         OR target_asset_id = ANY($2::uuid[])
      `,
      [sectorId, assetIds]
    );
  }

  async deactivateByAssetIds(assetIds: string[]): Promise<void> {
    await this.db.query(
      `
      UPDATE topology_links
      SET
        status = 'inactive'::link_status_enum,
        metadata = COALESCE(metadata, '{}'::jsonb) || '{"is_active": false}'::jsonb
      WHERE source_asset_id = ANY($1::uuid[])
         OR target_asset_id = ANY($1::uuid[])
      `,
      [assetIds]
    );
  }
}
