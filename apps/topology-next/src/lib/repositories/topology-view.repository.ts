import type { QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";
import type { SqlExecutor } from "@/lib/db/tx";
import { buildUpdateSet } from "@/lib/db/sql";
import type {
  TopologyLinkLayout,
  TopologyNodeLayout,
  TopologyView,
  TopologyViewLayout
} from "@/lib/dto/topology-view.dto";
import type {
  CreateTopologyViewInput,
  SaveTopologyViewLayoutInput,
  UpdateTopologyViewInput
} from "@/lib/validators/topology-view.schemas";

function mapTopologyView(row: QueryResultRow): TopologyView {
  return {
    id: String(row.id),
    project_id: String(row.project_id),
    name: String(row.name),
    view_type: row.view_type as TopologyView["view_type"],
    is_default: Boolean(row.is_default),
    metadata: (row.metadata ?? {}) as Record<string, unknown>,
    created_at: String(row.created_at),
    updated_at: String(row.updated_at)
  };
}

function mapNodeLayout(row: QueryResultRow): TopologyNodeLayout {
  return {
    id: String(row.id),
    topology_view_id: String(row.topology_view_id),
    asset_id: row.asset_id ? String(row.asset_id) : null,
    sector_id: row.sector_id ? String(row.sector_id) : null,
    x: Number(row.x),
    y: Number(row.y),
    width: row.width === null ? null : Number(row.width),
    height: row.height === null ? null : Number(row.height),
    collapsed: Boolean(row.collapsed),
    hidden: Boolean(row.hidden),
    z_index: Number(row.z_index),
    metadata: (row.metadata ?? {}) as Record<string, unknown>,
    created_at: String(row.created_at),
    updated_at: String(row.updated_at)
  };
}

function mapLinkLayout(row: QueryResultRow): TopologyLinkLayout {
  return {
    id: String(row.id),
    topology_view_id: String(row.topology_view_id),
    topology_link_id: String(row.topology_link_id),
    hidden: Boolean(row.hidden),
    label_offset_x: Number(row.label_offset_x),
    label_offset_y: Number(row.label_offset_y),
    metadata: (row.metadata ?? {}) as Record<string, unknown>,
    created_at: String(row.created_at),
    updated_at: String(row.updated_at)
  };
}

export class TopologyViewRepository {
  constructor(private readonly db: SqlExecutor = pool) {}

  async create(projectId: string, input: CreateTopologyViewInput): Promise<TopologyView> {
    const result = await this.db.query(
      `
      INSERT INTO topology_views (project_id, name, view_type, is_default, metadata)
      VALUES ($1::uuid, $2, $3::topology_view_type_enum, $4, $5::jsonb)
      RETURNING *
      `,
      [projectId, input.name, input.view_type, input.is_default, JSON.stringify(input.metadata ?? {})]
    );
    return mapTopologyView(result.rows[0]);
  }

  async findById(id: string): Promise<TopologyView | null> {
    const result = await this.db.query("SELECT * FROM topology_views WHERE id = $1::uuid", [id]);
    return result.rows[0] ? mapTopologyView(result.rows[0]) : null;
  }

  async findByProjectId(projectId: string, viewType?: TopologyView["view_type"]): Promise<TopologyView[]> {
    if (viewType) {
      const result = await this.db.query(
        `
        SELECT *
        FROM topology_views
        WHERE project_id = $1::uuid
          AND view_type = $2::topology_view_type_enum
        ORDER BY is_default DESC, created_at ASC
        `,
        [projectId, viewType]
      );
      return result.rows.map(mapTopologyView);
    }
    const result = await this.db.query(
      `
      SELECT *
      FROM topology_views
      WHERE project_id = $1::uuid
      ORDER BY view_type, is_default DESC, created_at ASC
      `,
      [projectId]
    );
    return result.rows.map(mapTopologyView);
  }

  async clearDefaults(projectId: string, viewType: TopologyView["view_type"]): Promise<void> {
    await this.db.query(
      `
      UPDATE topology_views
      SET is_default = false
      WHERE project_id = $1::uuid
        AND view_type = $2::topology_view_type_enum
      `,
      [projectId, viewType]
    );
  }

  async update(id: string, input: UpdateTopologyViewInput): Promise<TopologyView | null> {
    const payload: Record<string, unknown> = {};
    if (input.name !== undefined) payload.name = input.name;
    if (input.is_default !== undefined) payload.is_default = input.is_default;
    if (input.metadata !== undefined) payload.metadata = JSON.stringify(input.metadata ?? {});

    if (Object.keys(payload).length === 0) {
      return this.findById(id);
    }

    const { setClause, values } = buildUpdateSet(payload, {
      startIndex: 2,
      casts: {
        metadata: "jsonb"
      }
    });

    const result = await this.db.query(`UPDATE topology_views SET ${setClause} WHERE id = $1::uuid RETURNING *`, [id, ...values]);
    return result.rows[0] ? mapTopologyView(result.rows[0]) : null;
  }

  async getLayout(viewId: string): Promise<TopologyViewLayout> {
    const [nodeResult, linkResult] = await Promise.all([
      this.db.query(
        `
        SELECT *
        FROM topology_node_layouts
        WHERE topology_view_id = $1::uuid
        ORDER BY z_index ASC, created_at ASC
        `,
        [viewId]
      ),
      this.db.query(
        `
        SELECT *
        FROM topology_link_layouts
        WHERE topology_view_id = $1::uuid
        ORDER BY created_at ASC
        `,
        [viewId]
      )
    ]);

    return {
      node_layouts: nodeResult.rows.map(mapNodeLayout),
      link_layouts: linkResult.rows.map(mapLinkLayout)
    };
  }

  async replaceLayout(viewId: string, input: SaveTopologyViewLayoutInput): Promise<TopologyViewLayout> {
    await this.db.query("DELETE FROM topology_node_layouts WHERE topology_view_id = $1::uuid", [viewId]);
    await this.db.query("DELETE FROM topology_link_layouts WHERE topology_view_id = $1::uuid", [viewId]);

    for (const node of input.node_layouts) {
      await this.db.query(
        `
        INSERT INTO topology_node_layouts (
          topology_view_id, asset_id, sector_id, x, y, width, height, collapsed, hidden, z_index, metadata
        )
        VALUES (
          $1::uuid, $2::uuid, $3::uuid, $4, $5, $6, $7, $8, $9, $10, $11::jsonb
        )
        `,
        [
          viewId,
          node.asset_id ?? null,
          node.sector_id ?? null,
          node.x,
          node.y,
          node.width ?? null,
          node.height ?? null,
          node.collapsed,
          node.hidden,
          node.z_index,
          JSON.stringify(node.metadata ?? {})
        ]
      );
    }

    for (const link of input.link_layouts) {
      await this.db.query(
        `
        INSERT INTO topology_link_layouts (
          topology_view_id, topology_link_id, hidden, label_offset_x, label_offset_y, metadata
        )
        VALUES (
          $1::uuid, $2::uuid, $3, $4, $5, $6::jsonb
        )
        `,
        [
          viewId,
          link.topology_link_id,
          link.hidden,
          link.label_offset_x,
          link.label_offset_y,
          JSON.stringify(link.metadata ?? {})
        ]
      );
    }

    return this.getLayout(viewId);
  }
}
