import type { QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";
import type { SqlExecutor } from "@/lib/db/tx";

export interface ControlOperationsPolicyRecord extends QueryResultRow {
  policy_id: string;
  project_id: string;
  variable: string;
  enabled: boolean;
  bound_asset_id: string | null;
  source_name: string | null;
  binding_id: string | null;
  binding_enabled: boolean | null;
  target_asset_id: string | null;
  target_name: string | null;
  target_type: string | null;
  target_status: string | null;
  target_metadata: Record<string, unknown> | null;
  control_point: string | null;
  operation: string | null;
  updated_at: string;
}

export interface ControlOperationsRecommendationRecord extends QueryResultRow {
  audit_id: string;
  recommendation_id: string | null;
  correlation_id: string | null;
  project_id: string;
  policy_id: string | null;
  source_asset_id: string | null;
  target_asset_id: string | null;
  created_at: string;
  summary: string | null;
}

export interface ControlOperationsDeliveryRecord extends QueryResultRow {
  delivery_intent_id: string;
  command_id: string;
  recommendation_id: string;
  correlation_id: string;
  project_id: string;
  policy_id: string;
  source_asset_id: string | null;
  target_asset_id: string | null;
  target_name: string | null;
  operation: string;
  intent_status: string;
  retry_count: number;
  last_error: string | null;
  created_at: string;
  updated_at: string;
  expires_at: string;
  event_id: string | null;
  outbox_status: string | null;
}

export interface ControlOperationsMetrics {
  recommendation_total: number;
  last_recommendation_at: string | null;
  last_activity_at: string | null;
  delivery_counts: Record<string, number>;
}

export class ControlOperationsRepository {
  constructor(private readonly db: SqlExecutor = pool) {}

  async findPolicies(projectId: string, args?: { limit: number; offset: number }): Promise<ControlOperationsPolicyRecord[]> {
    const result = await this.db.query(`
      SELECT p.id::text AS policy_id, p.project_id::text, p.variable, p.enabled, p.bound_asset_id::text,
        source.name AS source_name, binding.id::text AS binding_id, binding.enabled AS binding_enabled,
        binding.target_asset_id::text, target.name AS target_name, target.asset_type::text AS target_type,
        target.status::text AS target_status, target.metadata AS target_metadata,
        binding.control_point, binding.operation, p.updated_at::text
      FROM public.project_control_policies p
      LEFT JOIN public.project_control_policy_actuation_bindings binding
        ON binding.policy_id = p.id AND binding.project_id = p.project_id
      LEFT JOIN public.assets source ON source.id = p.bound_asset_id AND source.project_id = p.project_id
      LEFT JOIN public.assets target ON target.id = binding.target_asset_id AND target.project_id = p.project_id
      WHERE p.project_id = $1::uuid
      ORDER BY p.variable ASC, p.priority DESC, p.version DESC, p.id ASC
      ${args ? "LIMIT $2 OFFSET $3" : ""}
    `, args ? [projectId, args.limit, args.offset] : [projectId]);
    return result.rows as ControlOperationsPolicyRecord[];
  }

  async findRecommendations(projectId: string, args: { limit: number; offset: number; policyId?: string; correlationId?: string }): Promise<ControlOperationsRecommendationRecord[]> {
    const values: Array<string | number> = [projectId];
    const conditions = ["COALESCE(entidad_id::text, cambios->'payload'->>'project_id', cambios->>'project_id') = $1"];
    if (args.policyId) { values.push(args.policyId); conditions.push(`COALESCE(cambios->'payload'->'policy_selection'->>'policy_id', cambios->'payload'->>'policy_id') = $${values.length}`); }
    if (args.correlationId) { values.push(args.correlationId); conditions.push(`COALESCE(cambios->'payload'->>'correlation_id', cambios->>'correlation_id') = $${values.length}`); }
    values.push(args.limit, args.offset);
    const limit = `$${values.length - 1}`;
    const offset = `$${values.length}`;
    const result = await this.db.query(`
      SELECT id::text AS audit_id,
        COALESCE(cambios->'payload'->'publishable'->'payload'->>'recommendation_id', cambios->'payload'->>'recommendation_id') AS recommendation_id,
        COALESCE(cambios->'payload'->>'correlation_id', cambios->>'correlation_id') AS correlation_id,
        COALESCE(entidad_id::text, cambios->'payload'->>'project_id', cambios->>'project_id') AS project_id,
        COALESCE(cambios->'payload'->'policy_selection'->>'policy_id', cambios->'payload'->>'policy_id') AS policy_id,
        COALESCE(cambios->'payload'->'publishable'->'payload'->>'source_asset_id', cambios->'payload'->>'source_asset_id') AS source_asset_id,
        COALESCE(cambios->'payload'->'publishable'->'payload'->'actuation_binding'->>'target_asset_id', cambios->'payload'->'actuation_binding'->>'target_asset_id') AS target_asset_id,
        ts::text AS created_at,
        COALESCE(cambios->'payload'->'runtime_payload'->>'summary', cambios->'payload'->'evaluation'->'recommendation'->>'summary') AS summary
      FROM iot_schema.auditoria
      WHERE entidad = 'control_engine_worker' AND accion = 'CONTROL_RECOMMENDATION_EMITTED'
        AND ${conditions.join(" AND ")}
      ORDER BY ts DESC, id DESC LIMIT ${limit} OFFSET ${offset}
    `, values);
    return result.rows as ControlOperationsRecommendationRecord[];
  }

  async findDeliveries(projectId: string, args: { limit: number; offset: number; status?: string; recommendationId?: string; commandId?: string; correlationId?: string }): Promise<ControlOperationsDeliveryRecord[]> {
    const values: Array<string | number> = [projectId];
    const conditions = ["d.project_id = $1::uuid"];
    for (const [field, value] of [["d.status", args.status], ["d.recommendation_id", args.recommendationId], ["d.command_id::text", args.commandId], ["d.correlation_id", args.correlationId]] as const) {
      if (value) { values.push(value); conditions.push(`${field} = $${values.length}`); }
    }
    values.push(args.limit, args.offset);
    const result = await this.db.query(`
      SELECT d.id::text AS delivery_intent_id, d.command_id::text, d.recommendation_id, d.correlation_id,
        d.project_id::text, d.policy_id, d.source_asset_id::text, d.target_asset_id::text,
        target.name AS target_name, d.operation, d.status AS intent_status, d.retry_count, d.last_error,
        d.created_at::text, d.updated_at::text, d.expires_at::text,
        outbox.event_id::text, outbox.status AS outbox_status
      FROM public.control_actuation_delivery_intents d
      LEFT JOIN public.assets target ON target.id = d.target_asset_id AND target.project_id = d.project_id
      LEFT JOIN LATERAL (
        SELECT event_id, status FROM public.control_actuation_outbox o
        WHERE o.project_id = d.project_id AND o.command_id = d.command_id
        ORDER BY o.created_at DESC, o.id DESC LIMIT 1
      ) outbox ON TRUE
      WHERE ${conditions.join(" AND ")}
      ORDER BY d.created_at DESC, d.id DESC LIMIT $${values.length - 1} OFFSET $${values.length}
    `, values);
    return result.rows as ControlOperationsDeliveryRecord[];
  }

  async getMetrics(projectId: string): Promise<ControlOperationsMetrics> {
    const result = await this.db.query(`
      WITH recommendations AS (
        SELECT COUNT(*)::int AS total, MAX(ts)::text AS last_at
        FROM iot_schema.auditoria
        WHERE entidad = 'control_engine_worker' AND accion = 'CONTROL_RECOMMENDATION_EMITTED'
          AND COALESCE(entidad_id::text, cambios->'payload'->>'project_id', cambios->>'project_id') = $1
      ), deliveries AS (
        SELECT COALESCE(jsonb_object_agg(status, count), '{}'::jsonb) AS counts
        FROM (SELECT status, COUNT(*)::int AS count FROM public.control_actuation_delivery_intents WHERE project_id = $1::uuid GROUP BY status) grouped
      ), activity AS (
        SELECT MAX(ts)::text AS last_at FROM iot_schema.auditoria
        WHERE entidad = 'control_engine_worker' AND COALESCE(entidad_id::text, cambios->'payload'->>'project_id', cambios->>'project_id') = $1
      )
      SELECT recommendations.total AS recommendation_total, recommendations.last_at AS last_recommendation_at,
        activity.last_at AS last_activity_at, deliveries.counts AS delivery_counts
      FROM recommendations, deliveries, activity
    `, [projectId]);
    const row = result.rows[0];
    return {
      recommendation_total: Number(row.recommendation_total ?? 0),
      last_recommendation_at: row.last_recommendation_at ? String(row.last_recommendation_at) : null,
      last_activity_at: row.last_activity_at ? String(row.last_activity_at) : null,
      delivery_counts: (row.delivery_counts ?? {}) as Record<string, number>
    };
  }
}
