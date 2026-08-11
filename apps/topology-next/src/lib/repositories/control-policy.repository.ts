import type { QueryResultRow } from "pg";
import type { SqlExecutor } from "@/lib/db/tx";
import { pool } from "@/lib/db/pool";
import { buildUpdateSet } from "@/lib/db/sql";
import type { ControlOperation, ControlPolicy } from "@/lib/dto/control-policy.dto";
import type { IControlPolicyRepository } from "@/lib/repositories/contracts";
import type { CreateControlPolicyInput, UpdateControlPolicyInput } from "@/lib/validators/control-policy.schemas";

function asObject(value: unknown): Record<string, unknown> {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
}

export function mapControlPolicy(row: QueryResultRow): ControlPolicy {
  return {
    id: String(row.id),
    project_id: String(row.project_id),
    variable: String(row.variable),
    binding: row.bound_asset_id ? {
      asset_id: String(row.bound_asset_id),
      variable_key: String(row.variable)
    } : null,
    actuation_binding: row.actuation_binding_id ? {
      id: String(row.actuation_binding_id),
      source_asset_id: String(row.actuation_source_asset_id),
      target_asset_id: String(row.actuation_target_asset_id),
      control_point: String(row.actuation_control_point),
      operation: String(row.actuation_operation) as ControlOperation,
      enabled: Boolean(row.actuation_binding_enabled),
      version: Number(row.actuation_binding_version),
      created_at: String(row.actuation_binding_created_at),
      updated_at: String(row.actuation_binding_updated_at)
    } : null,
    context_selector: asObject(row.context_selector),
    policy_type: String(row.policy_type) as ControlPolicy["policy_type"],
    params: asObject(row.params),
    priority: Number(row.priority),
    enabled: Boolean(row.enabled),
    version: Number(row.version),
    created_at: String(row.created_at),
    updated_at: String(row.updated_at)
  };
}

export function buildControlPolicyUpdatePayload(
  input: UpdateControlPolicyInput & { version?: number }
): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  if (input.context_selector !== undefined) payload.context_selector = JSON.stringify(input.context_selector);
  if (input.binding !== undefined) payload.bound_asset_id = input.binding.asset_id;
  if (input.params !== undefined) payload.params = JSON.stringify(input.params);
  if (input.priority !== undefined) payload.priority = input.priority;
  if (input.enabled !== undefined) payload.enabled = input.enabled;
  if (input.version !== undefined) payload.version = input.version;
  return payload;
}

export class ControlPolicyRepository implements IControlPolicyRepository {
  constructor(private readonly db: SqlExecutor = pool) {}

  async create(input: CreateControlPolicyInput): Promise<ControlPolicy> {
    const result = await this.db.query(
      `
      INSERT INTO public.project_control_policies (
        project_id,
        variable,
        bound_asset_id,
        context_selector,
        policy_type,
        params,
        priority,
        enabled
      )
      VALUES ($1::uuid, $2, $3::uuid, $4::jsonb, $5, $6::jsonb, $7, $8)
      RETURNING *
      `,
      [
        input.project_id,
        input.variable,
        input.binding.asset_id,
        JSON.stringify(input.context_selector),
        input.policy_type,
        JSON.stringify(input.params),
        input.priority,
        input.enabled
      ]
    );

    return mapControlPolicy(result.rows[0]);
  }

  async findById(id: string): Promise<ControlPolicy | null> {
    const result = await this.db.query(
      `${this.selectWithActuationBinding()} WHERE p.id = $1::uuid`,
      [id]
    );
    return result.rows[0] ? mapControlPolicy(result.rows[0]) : null;
  }

  async findAll(filters?: {
    projectId?: string;
    projectIds?: string[];
    variable?: string;
    enabled?: boolean;
  }): Promise<ControlPolicy[]> {
    const conditions: string[] = [];
    const values: Array<string | string[] | boolean> = [];

    if (filters?.projectId) {
      values.push(filters.projectId);
      conditions.push(`project_id = $${values.length}::uuid`);
    } else if (filters?.projectIds) {
      if (filters.projectIds.length === 0) {
        return [];
      }
      values.push(filters.projectIds);
      conditions.push(`project_id = ANY($${values.length}::uuid[])`);
    }

    if (filters?.variable) {
      values.push(filters.variable);
      conditions.push(`variable = $${values.length}`);
    }

    if (filters?.enabled !== undefined) {
      values.push(filters.enabled);
      conditions.push(`enabled = $${values.length}`);
    }

    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

    const result = await this.db.query(
      `${this.selectWithActuationBinding()} ${whereClause.replaceAll("project_id", "p.project_id").replaceAll("variable", "p.variable").replaceAll("enabled", "p.enabled")}
      ORDER BY p.project_id ASC, p.variable ASC, p.priority DESC, p.version DESC, p.updated_at DESC`,
      values
    );

    return result.rows.map(mapControlPolicy);
  }

  private selectWithActuationBinding() {
    return `
      SELECT p.*,
        ab.id AS actuation_binding_id,
        ab.source_asset_id AS actuation_source_asset_id,
        ab.target_asset_id AS actuation_target_asset_id,
        ab.control_point AS actuation_control_point,
        ab.operation AS actuation_operation,
        ab.enabled AS actuation_binding_enabled,
        ab.version AS actuation_binding_version,
        ab.created_at AS actuation_binding_created_at,
        ab.updated_at AS actuation_binding_updated_at
      FROM public.project_control_policies p
      LEFT JOIN public.project_control_policy_actuation_bindings ab ON ab.policy_id = p.id`;
  }

  async update(id: string, input: UpdateControlPolicyInput & { version?: number }): Promise<ControlPolicy | null> {
    const payload = buildControlPolicyUpdatePayload(input);
    if (Object.keys(payload).length === 0) {
      return this.findById(id);
    }

    const { setClause, values } = buildUpdateSet(payload, {
      startIndex: 2,
      casts: {
        bound_asset_id: "uuid",
        context_selector: "jsonb",
        params: "jsonb"
      }
    });

    const result = await this.db.query(
      `UPDATE public.project_control_policies SET ${setClause} WHERE id = $1::uuid RETURNING *`,
      [id, ...values]
    );
    return result.rows[0] ? mapControlPolicy(result.rows[0]) : null;
  }
}
