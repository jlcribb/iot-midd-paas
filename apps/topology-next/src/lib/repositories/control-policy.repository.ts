import type { QueryResultRow } from "pg";
import type { SqlExecutor } from "@/lib/db/tx";
import { pool } from "@/lib/db/pool";
import { buildUpdateSet } from "@/lib/db/sql";
import type { ControlPolicy } from "@/lib/dto/control-policy.dto";
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
        context_selector,
        policy_type,
        params,
        priority,
        enabled
      )
      VALUES ($1::uuid, $2, $3::jsonb, $4, $5::jsonb, $6, $7)
      RETURNING *
      `,
      [
        input.project_id,
        input.variable,
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
      "SELECT * FROM public.project_control_policies WHERE id = $1::uuid",
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
      `
      SELECT *
      FROM public.project_control_policies
      ${whereClause}
      ORDER BY project_id ASC, variable ASC, priority DESC, version DESC, updated_at DESC
      `,
      values
    );

    return result.rows.map(mapControlPolicy);
  }

  async update(id: string, input: UpdateControlPolicyInput & { version?: number }): Promise<ControlPolicy | null> {
    const payload = buildControlPolicyUpdatePayload(input);
    if (Object.keys(payload).length === 0) {
      return this.findById(id);
    }

    const { setClause, values } = buildUpdateSet(payload, {
      startIndex: 2,
      casts: {
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
