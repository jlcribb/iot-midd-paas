import type { QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";
import type { SqlExecutor } from "@/lib/db/tx";
import { buildUpdateSet } from "@/lib/db/sql";
import type { Asset, AssetTreeNode } from "@/lib/dto/asset.dto";
import type { IAssetRepository } from "@/lib/repositories/contracts";
import type { CreateAssetInput, UpdateAssetInput } from "@/lib/validators/asset.schemas";

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

function mapAsset(row: QueryResultRow): Asset {
  return {
    id: String(row.id),
    project_id: String(row.project_id),
    sector_id: String(row.sector_id),
    location_id: row.location_id ? String(row.location_id) : null,
    parent_asset_id: row.parent_asset_id ? String(row.parent_asset_id) : null,
    asset_type: row.asset_type as Asset["asset_type"],
    subtype: String(row.subtype),
    name: String(row.name),
    code: row.code as string | null,
    description: row.description as string | null,
    status: row.status as Asset["status"],
    role: row.role as string | null,
    serial_number: row.serial_number as string | null,
    manufacturer: row.manufacturer as string | null,
    model: row.model as string | null,
    firmware_version: row.firmware_version as string | null,
    hardware_version: row.hardware_version as string | null,
    mac_address: row.mac_address as string | null,
    ip_address: row.ip_address as string | null,
    last_seen_at: row.last_seen_at ? String(row.last_seen_at) : null,
    metadata: (row.metadata ?? {}) as Record<string, unknown>,
    created_at: String(row.created_at),
    updated_at: String(row.updated_at)
  };
}

function mapAssetTreeNode(row: QueryResultRow): AssetTreeNode {
  return {
    ...mapAsset(row),
    depth: Number(row.depth)
  };
}

export class AssetRepository implements IAssetRepository {
  constructor(private readonly db: SqlExecutor = pool) {}

  private async queryActiveByProject(projectId: string, activeCondition: string): Promise<Asset[]> {
    const result = await this.db.query(
      `
      SELECT *
      FROM assets
      WHERE project_id = $1::uuid
        AND status <> 'retired'::asset_status_enum
        AND ${activeCondition}
      ORDER BY created_at DESC
      `,
      [projectId]
    );
    return result.rows.map(mapAsset);
  }

  private async queryActiveBySector(sectorId: string, activeCondition: string): Promise<Asset[]> {
    const result = await this.db.query(
      `
      SELECT *
      FROM assets
      WHERE sector_id = $1::uuid
        AND status <> 'retired'::asset_status_enum
        AND ${activeCondition}
      ORDER BY created_at DESC
      `,
      [sectorId]
    );
    return result.rows.map(mapAsset);
  }

  private async queryOfflineAssets(projectId: string, offlineMinutes: number, activeCondition: string): Promise<Asset[]> {
    const result = await this.db.query(
      `
      SELECT *
      FROM assets
      WHERE project_id = $1::uuid
        AND status <> 'retired'::asset_status_enum
        AND ${activeCondition}
        AND (
          status = 'offline'::asset_status_enum
          OR (last_seen_at IS NOT NULL AND last_seen_at < NOW() - make_interval(mins => $2::int))
        )
      ORDER BY last_seen_at ASC NULLS FIRST
      `,
      [projectId, offlineMinutes]
    );
    return result.rows.map(mapAsset);
  }

  async create(input: CreateAssetInput): Promise<Asset> {
    const result = await this.db.query(
      `
      INSERT INTO assets (
        project_id, sector_id, location_id, parent_asset_id, asset_type, subtype,
        name, code, description, status, role, serial_number, manufacturer, model,
        firmware_version, hardware_version, mac_address, ip_address, last_seen_at, metadata
      )
      VALUES (
        $1::uuid, $2::uuid, $3::uuid, $4::uuid, $5::asset_type_enum, $6,
        $7, $8, $9, $10::asset_status_enum, $11, $12, $13, $14,
        $15, $16, $17, $18::inet, $19::timestamptz, $20::jsonb
      )
      RETURNING *
      `,
      [
        input.project_id,
        input.sector_id,
        input.location_id ?? null,
        input.parent_asset_id ?? null,
        input.asset_type,
        input.subtype,
        input.name,
        input.code ?? null,
        input.description ?? null,
        input.status,
        input.role ?? null,
        input.serial_number ?? null,
        input.manufacturer ?? null,
        input.model ?? null,
        input.firmware_version ?? null,
        input.hardware_version ?? null,
        input.mac_address ?? null,
        input.ip_address ?? null,
        input.last_seen_at ?? null,
        JSON.stringify(input.metadata ?? {})
      ]
    );
    return mapAsset(result.rows[0]);
  }

  async findById(id: string): Promise<Asset | null> {
    const result = await this.db.query("SELECT * FROM assets WHERE id = $1::uuid", [id]);
    return result.rows[0] ? mapAsset(result.rows[0]) : null;
  }

  async findByProjectId(projectId: string): Promise<Asset[]> {
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

  async findBySectorId(sectorId: string): Promise<Asset[]> {
    const activeConditions = [
      `COALESCE(is_active, true) = true AND ${ACTIVE_FROM_METADATA_SQL}`,
      ACTIVE_FROM_METADATA_SQL,
      "TRUE"
    ];

    let lastError: unknown;
    for (const activeCondition of activeConditions) {
      try {
        return await this.queryActiveBySector(sectorId, activeCondition);
      } catch (error) {
        lastError = error;
        if (!isSchemaCompatibilityError(error)) {
          throw error;
        }
      }
    }

    throw lastError;
  }

  async findChildren(parentAssetId: string): Promise<Asset[]> {
    const result = await this.db.query("SELECT * FROM assets WHERE parent_asset_id = $1::uuid ORDER BY created_at ASC", [parentAssetId]);
    return result.rows.map(mapAsset);
  }

  async findTree(rootAssetId: string): Promise<AssetTreeNode[]> {
    const result = await this.db.query(
      `
      WITH RECURSIVE asset_tree AS (
        SELECT a.*, 0::int AS depth
        FROM assets a
        WHERE a.id = $1::uuid
        UNION ALL
        SELECT c.*, t.depth + 1
        FROM assets c
        JOIN asset_tree t ON c.parent_asset_id = t.id
      )
      SELECT * FROM asset_tree ORDER BY depth, created_at
      `,
      [rootAssetId]
    );
    return result.rows.map(mapAssetTreeNode);
  }

  async findNodeDevices(nodeAssetId: string): Promise<Asset[]> {
    const result = await this.db.query(
      `
      SELECT *
      FROM assets
      WHERE parent_asset_id = $1::uuid
        AND asset_type IN ('sensor'::asset_type_enum, 'actuator'::asset_type_enum)
      ORDER BY created_at DESC
      `,
      [nodeAssetId]
    );
    return result.rows.map(mapAsset);
  }

  async findOfflineAssets(projectId: string, offlineMinutes: number): Promise<Asset[]> {
    const activeConditions = [
      `COALESCE(is_active, true) = true AND ${ACTIVE_FROM_METADATA_SQL}`,
      ACTIVE_FROM_METADATA_SQL,
      "TRUE"
    ];

    let lastError: unknown;
    for (const activeCondition of activeConditions) {
      try {
        return await this.queryOfflineAssets(projectId, offlineMinutes, activeCondition);
      } catch (error) {
        lastError = error;
        if (!isSchemaCompatibilityError(error)) {
          throw error;
        }
      }
    }

    throw lastError;
  }

  async update(id: string, input: UpdateAssetInput): Promise<Asset | null> {
    const payload: Record<string, unknown> = {};
    for (const key of [
      "sector_id",
      "location_id",
      "parent_asset_id",
      "asset_type",
      "subtype",
      "name",
      "code",
      "description",
      "status",
      "role",
      "serial_number",
      "manufacturer",
      "model",
      "firmware_version",
      "hardware_version",
      "mac_address",
      "ip_address",
      "last_seen_at"
    ] as const) {
      if (input[key] !== undefined) {
        payload[key] = input[key] ?? null;
      }
    }
    if (input.metadata !== undefined) {
      payload.metadata = JSON.stringify(input.metadata ?? {});
    }
    const shouldSyncActiveFlag = typeof input.metadata?.is_active === "boolean";
    if (shouldSyncActiveFlag) {
      payload.is_active = input.metadata?.is_active;
    }
    if (Object.keys(payload).length === 0) {
      return this.findById(id);
    }

    const runUpdate = async (data: Record<string, unknown>) => {
      const { setClause, values } = buildUpdateSet(data, {
        startIndex: 2,
        casts: {
          sector_id: "uuid",
          location_id: "uuid",
          parent_asset_id: "uuid",
          asset_type: "asset_type_enum",
          status: "asset_status_enum",
          ip_address: "inet",
          last_seen_at: "timestamptz",
          metadata: "jsonb"
        }
      });

      const result = await this.db.query(`UPDATE assets SET ${setClause} WHERE id = $1::uuid RETURNING *`, [id, ...values]);
      return result.rows[0] ? mapAsset(result.rows[0]) : null;
    };

    try {
      return await runUpdate(payload);
    } catch (error) {
      if (!shouldSyncActiveFlag || !isSchemaCompatibilityError(error)) {
        throw error;
      }

      delete payload.is_active;
      return runUpdate(payload);
    }
  }

  async deleteSafe(id: string): Promise<Asset | null> {
    try {
      const result = await this.db.query(
        `
        UPDATE assets
        SET
          status = 'retired'::asset_status_enum,
          is_active = false,
          metadata = COALESCE(metadata, '{}'::jsonb) || '{"is_active": false}'::jsonb
        WHERE id = $1::uuid
        RETURNING *
        `,
        [id]
      );
      return result.rows[0] ? mapAsset(result.rows[0]) : null;
    } catch (error) {
      if (!isSchemaCompatibilityError(error)) {
        throw error;
      }

      const fallback = await this.db.query(
        `
        UPDATE assets
        SET
          status = 'retired'::asset_status_enum,
          metadata = COALESCE(metadata, '{}'::jsonb) || '{"is_active": false}'::jsonb
        WHERE id = $1::uuid
        RETURNING *
        `,
        [id]
      );
      return fallback.rows[0] ? mapAsset(fallback.rows[0]) : null;
    }
  }

  async existsProjectCode(projectId: string, code: string, excludeId?: string): Promise<boolean> {
    const result = await this.db.query(
      `
      SELECT 1
      FROM assets
      WHERE project_id = $1::uuid
        AND code = $2
        AND ($3::uuid IS NULL OR id <> $3::uuid)
      LIMIT 1
      `,
      [projectId, code, excludeId ?? null]
    );
    return (result.rowCount ?? 0) > 0;
  }

  async existsSerialNumber(serialNumber: string, excludeId?: string): Promise<boolean> {
    const result = await this.db.query(
      `
      SELECT 1
      FROM assets
      WHERE serial_number = $1
        AND ($2::uuid IS NULL OR id <> $2::uuid)
      LIMIT 1
      `,
      [serialNumber, excludeId ?? null]
    );
    return (result.rowCount ?? 0) > 0;
  }

  async existsNormalizedMac(macAddress: string, excludeId?: string): Promise<boolean> {
    const result = await this.db.query(
      `
      SELECT 1
      FROM assets
      WHERE normalize_mac_address(mac_address) = normalize_mac_address($1)
        AND ($2::uuid IS NULL OR id <> $2::uuid)
      LIMIT 1
      `,
      [macAddress, excludeId ?? null]
    );
    return (result.rowCount ?? 0) > 0;
  }

  async softDeactivateByProject(projectId: string): Promise<void> {
    try {
      await this.db.query(
        `
        UPDATE assets
        SET
          status = 'inactive'::asset_status_enum,
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
        UPDATE assets
        SET
          status = 'inactive'::asset_status_enum,
          metadata = COALESCE(metadata, '{}'::jsonb) || '{"is_active": false}'::jsonb
        WHERE project_id = $1::uuid
        `,
        [projectId]
      );
    }
  }
}
