import type { QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";
import type { SqlExecutor } from "@/lib/db/tx";
import type {
  ControlAuditView,
  ControlRecommendationView,
  ControlStatusView
} from "@/lib/dto/control.dto";
import type { IControlObservabilityRepository } from "@/lib/repositories/contracts";

function toNumberOrNull(value: unknown): number | null {
  if (value === null || value === undefined) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function mapRecommendation(row: QueryResultRow): ControlRecommendationView {
  return {
    audit_id: String(row.audit_id),
    observed_at: String(row.observed_at),
    project_id: row.project_id ? String(row.project_id) : null,
    variable_id: row.variable_id ? String(row.variable_id) : null,
    event_id: row.event_id ? String(row.event_id) : null,
    recommendation_kind: row.recommendation_kind ? String(row.recommendation_kind) : null,
    action_label: row.action_label ? String(row.action_label) : null,
    actuator_name: row.actuator_name ? String(row.actuator_name) : null,
    command_value: toNumberOrNull(row.command_value),
    summary: row.summary ? String(row.summary) : null,
    measurement_value: toNumberOrNull(row.measurement_value),
    setpoint_value: toNumberOrNull(row.setpoint_value),
    error: toNumberOrNull(row.error),
    evaluator_name: row.evaluator_name ? String(row.evaluator_name) : null,
    policy_id: row.policy_id ? String(row.policy_id) : null,
    policy_type: row.policy_type ? String(row.policy_type) : null,
    policy_version: toNumberOrNull(row.policy_version),
    policy_priority: toNumberOrNull(row.policy_priority)
  };
}

function mapAudit(row: QueryResultRow): ControlAuditView {
  return {
    id: Number(row.id),
    ts: String(row.ts),
    action: String(row.action),
    project_id: row.project_id ? String(row.project_id) : null,
    status: String(row.status) as ControlAuditView["status"],
    variable_id: row.variable_id ? String(row.variable_id) : null,
    event_id: row.event_id ? String(row.event_id) : null,
    policy_id: row.policy_id ? String(row.policy_id) : null,
    policy_type: row.policy_type ? String(row.policy_type) : null,
    policy_version: toNumberOrNull(row.policy_version),
    policy_priority: toNumberOrNull(row.policy_priority),
    summary: row.summary ? String(row.summary) : null,
    envelope: (row.envelope ?? {}) as Record<string, unknown>
  };
}

function mapStatus(row: QueryResultRow): ControlStatusView {
  return {
    activity_status: String(row.activity_status) as ControlStatusView["activity_status"],
    latest_audit_at: row.latest_audit_at ? String(row.latest_audit_at) : null,
    latest_recommendation_at: row.latest_recommendation_at ? String(row.latest_recommendation_at) : null,
    latest_skipped_at: row.latest_skipped_at ? String(row.latest_skipped_at) : null,
    enabled_projects: Number(row.enabled_projects ?? 0),
    enabled_policies: Number(row.enabled_policies ?? 0),
    projects_with_policies: Number(row.projects_with_policies ?? 0),
    audits_last_24h: Number(row.audits_last_24h ?? 0),
    recommendations_last_24h: Number(row.recommendations_last_24h ?? 0),
    skipped_last_24h: Number(row.skipped_last_24h ?? 0),
    errors_last_24h: Number(row.errors_last_24h ?? 0)
  };
}

export class ControlObservabilityRepository implements IControlObservabilityRepository {
  constructor(private readonly db: SqlExecutor = pool) {}

  async findLatestRecommendations(filters?: {
    projectId?: string;
    projectIds?: string[];
    limit?: number;
  }): Promise<ControlRecommendationView[]> {
    const conditions = [
      "entidad = 'control_engine_worker'",
      "accion = 'CONTROL_RECOMMENDATION_EMITTED'"
    ];
    const values: Array<string | string[] | number> = [];

    if (filters?.projectId) {
      values.push(filters.projectId);
      conditions.push(
        `COALESCE(entidad_id::text, cambios->'payload'->>'project_id', cambios->>'project_id') = $${values.length}`
      );
    } else if (filters?.projectIds) {
      if (filters.projectIds.length === 0) {
        return [];
      }
      values.push(filters.projectIds);
      conditions.push(
        `COALESCE(entidad_id::text, cambios->'payload'->>'project_id', cambios->>'project_id') = ANY($${values.length}::text[])`
      );
    }

    values.push(filters?.limit ?? 20);
    const limitPlaceholder = `$${values.length}`;

    const result = await this.db.query(
      `
      SELECT
        COALESCE(cambios->>'audit_id', id::text) AS audit_id,
        ts AS observed_at,
        COALESCE(entidad_id::text, cambios->'payload'->>'project_id', cambios->>'project_id') AS project_id,
        COALESCE(cambios->'payload'->>'variable_id', cambios->>'variable') AS variable_id,
        COALESCE(cambios->'payload'->>'event_id', cambios->'input_event'->>'event_id', cambios->>'event_id') AS event_id,
        cambios->'payload'->'runtime_payload'->>'recommendation_kind' AS recommendation_kind,
        cambios->'payload'->'runtime_payload'->>'action_label' AS action_label,
        cambios->'payload'->'runtime_payload'->>'actuator_name' AS actuator_name,
        cambios->'payload'->'runtime_payload'->>'command_value' AS command_value,
        cambios->'payload'->'runtime_payload'->>'summary' AS summary,
        cambios->'payload'->'runtime_payload'->>'measurement_value' AS measurement_value,
        cambios->'payload'->'runtime_payload'->>'setpoint_value' AS setpoint_value,
        cambios->'payload'->'runtime_payload'->>'error' AS error,
        cambios->'payload'->'runtime_payload'->>'evaluator_name' AS evaluator_name,
        COALESCE(cambios->'payload'->'policy_selection'->>'policy_id', cambios->'payload'->>'policy_id') AS policy_id,
        COALESCE(cambios->'payload'->'policy_selection'->>'policy_type', cambios->'payload'->>'policy_type') AS policy_type,
        COALESCE(cambios->'payload'->'policy_selection'->>'version', cambios->'payload'->>'policy_version') AS policy_version,
        COALESCE(cambios->'payload'->'policy_selection'->>'priority', cambios->'payload'->>'policy_priority') AS policy_priority
      FROM iot_schema.auditoria
      WHERE ${conditions.join(" AND ")}
      ORDER BY ts DESC
      LIMIT ${limitPlaceholder}
      `,
      values
    );

    return result.rows.map(mapRecommendation);
  }

  async findAuditEntries(filters?: {
    projectId?: string;
    projectIds?: string[];
    status?: "processed" | "skipped" | "error";
    limit?: number;
  }): Promise<ControlAuditView[]> {
    const conditions = ["entidad = 'control_engine_worker'"];
    const values: Array<string | string[] | number> = [];

    if (filters?.projectId) {
      values.push(filters.projectId);
      conditions.push(
        `COALESCE(entidad_id::text, cambios->'payload'->>'project_id', cambios->>'project_id') = $${values.length}`
      );
    } else if (filters?.projectIds) {
      if (filters.projectIds.length === 0) {
        return [];
      }
      values.push(filters.projectIds);
      conditions.push(
        `COALESCE(entidad_id::text, cambios->'payload'->>'project_id', cambios->>'project_id') = ANY($${values.length}::text[])`
      );
    }

    if (filters?.status) {
      values.push(filters.status);
      conditions.push(
        `COALESCE(cambios->>'status', 'processed') = $${values.length}`
      );
    }

    values.push(filters?.limit ?? 50);
    const limitPlaceholder = `$${values.length}`;

    const result = await this.db.query(
      `
      SELECT
        id,
        ts,
        accion AS action,
        COALESCE(entidad_id::text, cambios->'payload'->>'project_id', cambios->>'project_id') AS project_id,
        COALESCE(cambios->>'status', 'processed') AS status,
        COALESCE(cambios->'payload'->>'variable_id', cambios->>'variable') AS variable_id,
        COALESCE(cambios->'payload'->>'event_id', cambios->'input_event'->>'event_id', cambios->>'event_id') AS event_id,
        COALESCE(cambios->'payload'->'policy_selection'->>'policy_id', cambios->'payload'->>'policy_id') AS policy_id,
        COALESCE(cambios->'payload'->'policy_selection'->>'policy_type', cambios->'payload'->>'policy_type') AS policy_type,
        COALESCE(cambios->'payload'->'policy_selection'->>'version', cambios->'payload'->>'policy_version') AS policy_version,
        COALESCE(cambios->'payload'->'policy_selection'->>'priority', cambios->'payload'->>'policy_priority') AS policy_priority,
        COALESCE(
          cambios->'payload'->'runtime_payload'->>'summary',
          cambios->'payload'->'evaluation'->'recommendation'->>'summary',
          cambios->>'error',
          cambios->>'skip_reason'
        ) AS summary,
        cambios AS envelope
      FROM iot_schema.auditoria
      WHERE ${conditions.join(" AND ")}
      ORDER BY ts DESC
      LIMIT ${limitPlaceholder}
      `,
      values
    );

    return result.rows.map(mapAudit);
  }

  async getStatus(filters?: { projectIds?: string[] }): Promise<ControlStatusView> {
    const values: Array<string[]> = [];
    let auditScopeCondition = "";
    let projectScopeCondition = "";
    let policyScopeCondition = "";

    if (filters?.projectIds) {
      if (filters.projectIds.length === 0) {
        return {
          activity_status: "idle",
          latest_audit_at: null,
          latest_recommendation_at: null,
          latest_skipped_at: null,
          enabled_projects: 0,
          enabled_policies: 0,
          projects_with_policies: 0,
          audits_last_24h: 0,
          recommendations_last_24h: 0,
          skipped_last_24h: 0,
          errors_last_24h: 0
        };
      }
      values.push(filters.projectIds);
      auditScopeCondition = `
        AND COALESCE(entidad_id::text, cambios->'payload'->>'project_id', cambios->>'project_id') = ANY($1::text[])
      `;
      projectScopeCondition = " AND id = ANY($1::uuid[])";
      policyScopeCondition = " AND project_id = ANY($1::uuid[])";
    }

    const result = await this.db.query(
      `
      WITH audit_metrics AS (
        SELECT
          MAX(ts) AS latest_audit_at,
          MAX(CASE WHEN accion = 'CONTROL_RECOMMENDATION_EMITTED' THEN ts END) AS latest_recommendation_at,
          MAX(CASE WHEN accion = 'CONTROL_SKIPPED_BY_FEATURE_FLAG' THEN ts END) AS latest_skipped_at,
          COUNT(*) FILTER (WHERE ts >= now() - interval '24 hours') AS audits_last_24h,
          COUNT(*) FILTER (
            WHERE accion = 'CONTROL_RECOMMENDATION_EMITTED'
              AND ts >= now() - interval '24 hours'
          ) AS recommendations_last_24h,
          COUNT(*) FILTER (
            WHERE accion = 'CONTROL_SKIPPED_BY_FEATURE_FLAG'
              AND ts >= now() - interval '24 hours'
          ) AS skipped_last_24h,
          COUNT(*) FILTER (
            WHERE accion = 'CONTROL_EVALUATION_FAILED'
              AND ts >= now() - interval '24 hours'
          ) AS errors_last_24h
        FROM iot_schema.auditoria
        WHERE entidad = 'control_engine_worker'
        ${auditScopeCondition}
      )
      SELECT
        CASE
          WHEN audit_metrics.latest_audit_at IS NULL THEN 'idle'
          WHEN audit_metrics.latest_audit_at >= now() - interval '15 minutes' THEN 'active'
          ELSE 'stale'
        END AS activity_status,
        audit_metrics.latest_audit_at,
        audit_metrics.latest_recommendation_at,
        audit_metrics.latest_skipped_at,
        COALESCE((
          SELECT COUNT(*)
          FROM public.projects
          WHERE parametric_control_enabled = TRUE
          ${projectScopeCondition}
        ), 0) AS enabled_projects,
        COALESCE((
          SELECT COUNT(*)
          FROM public.project_control_policies
          WHERE enabled = TRUE
          ${policyScopeCondition}
        ), 0) AS enabled_policies,
        COALESCE((
          SELECT COUNT(DISTINCT project_id)
          FROM public.project_control_policies
          WHERE enabled = TRUE
          ${policyScopeCondition}
        ), 0) AS projects_with_policies,
        COALESCE(audit_metrics.audits_last_24h, 0) AS audits_last_24h,
        COALESCE(audit_metrics.recommendations_last_24h, 0) AS recommendations_last_24h,
        COALESCE(audit_metrics.skipped_last_24h, 0) AS skipped_last_24h,
        COALESCE(audit_metrics.errors_last_24h, 0) AS errors_last_24h
      FROM audit_metrics
      `,
      values
    );

    return mapStatus(result.rows[0]);
  }
}
