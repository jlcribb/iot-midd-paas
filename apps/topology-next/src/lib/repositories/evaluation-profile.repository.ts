import type { QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";
import { withTransaction, type SqlExecutor, type TransactionRunner } from "@/lib/db/tx";
import type { CreateEvaluationProfileInput, EvaluationMetric, EvaluationProfile, EvaluationProfileConstraint, EvaluationProfileMetric } from "@/lib/dto/evaluation-profile.dto";
import { ConflictError, NotFoundError } from "@/lib/errors/domain-errors";

function object(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

export function mapEvaluationMetric(row: QueryResultRow): EvaluationMetric {
  return {
    id: String(row.id), code: String(row.code), version: Number(row.version), name: String(row.name),
    description: String(row.description ?? ""), unit: row.unit === null ? null : String(row.unit),
    direction: String(row.direction) as EvaluationMetric["direction"],
    normalization_method: String(row.normalization_method) as EvaluationMetric["normalization_method"],
    normalization_config: object(row.normalization_config), weightable: Boolean(row.weightable),
    active: Boolean(row.active), created_at: String(row.created_at)
  };
}

function mapProfile(row: QueryResultRow): EvaluationProfile {
  const metrics = Array.isArray(row.metrics) ? row.metrics : [];
  const constraints = Array.isArray(row.constraints) ? row.constraints : [];
  return {
    id: String(row.id), project_id: String(row.project_id), code: String(row.code), version: Number(row.version),
    name: String(row.name), description: String(row.description ?? ""), status: String(row.status) as EvaluationProfile["status"],
    schema_version: 1, metadata: object(row.metadata), created_by: String(row.created_by), created_at: String(row.created_at),
    metrics: metrics.map((entry): EvaluationProfileMetric => ({
      metric: mapEvaluationMetric(entry), weight: Number(entry.weight), required: Boolean(entry.required)
    })),
    constraints: constraints.map((entry): EvaluationProfileConstraint => ({
      id: String(entry.id), metric_id: String(entry.metric_id), kind: String(entry.kind) as EvaluationProfileConstraint["kind"],
      lower_bound: entry.lower_bound === null ? null : Number(entry.lower_bound),
      upper_bound: entry.upper_bound === null ? null : Number(entry.upper_bound), critical: Boolean(entry.critical)
    }))
  };
}

const metricColumns = `id, code, version, name, description, unit, direction, normalization_method,
  normalization_config, weightable, active, created_at`;

export class EvaluationProfileRepository {
  constructor(private readonly db: SqlExecutor = pool, private readonly transaction: TransactionRunner = withTransaction) {}

  async listMetrics(): Promise<EvaluationMetric[]> {
    const result = await this.db.query(`SELECT ${metricColumns} FROM public.control_evaluation_metrics WHERE active=TRUE ORDER BY code, version DESC`);
    return result.rows.map(mapEvaluationMetric);
  }

  async listByProject(projectId: string): Promise<EvaluationProfile[]> {
    const result = await this.db.query(this.profileQuery("WHERE p.project_id=$1::uuid"), [projectId]);
    return result.rows.map(mapProfile);
  }

  async findByProjectAndId(projectId: string, profileId: string): Promise<EvaluationProfile | null> {
    const result = await this.db.query(this.profileQuery("WHERE p.project_id=$1::uuid AND p.id=$2::uuid"), [projectId, profileId]);
    return result.rows[0] ? mapProfile(result.rows[0]) : null;
  }

  async create(projectId: string, createdBy: string, input: CreateEvaluationProfileInput): Promise<EvaluationProfile> {
    return this.transaction(async (tx) => {
      const ids = input.metrics.map((metric) => metric.metric_id);
      const metricResult = await tx.query(`SELECT ${metricColumns} FROM public.control_evaluation_metrics WHERE active=TRUE AND id = ANY($1::uuid[]) FOR SHARE`, [ids]);
      if (metricResult.rows.length !== ids.length) throw new NotFoundError("One or more active evaluation metrics were not found");
      if (metricResult.rows.some((row) => !Boolean(row.weightable))) throw new ConflictError("An evaluation profile may only weight weightable metrics");

      const versionResult = await tx.query(
        "SELECT COALESCE(MAX(version), 0) + 1 AS next_version FROM public.control_evaluation_profiles WHERE project_id=$1::uuid AND code=$2",
        [projectId, input.code]
      );
      const version = Number(versionResult.rows[0].next_version);
      const profileResult = await tx.query(`
        INSERT INTO public.control_evaluation_profiles
          (project_id, code, version, name, description, status, schema_version, metadata, created_by)
        VALUES ($1::uuid, $2, $3, $4, $5, 'ACTIVE', 1, $6::jsonb, $7)
        RETURNING *
      `, [projectId, input.code, version, input.name, input.description ?? "", JSON.stringify(input.metadata ?? {}), createdBy]);
      const profile = profileResult.rows[0];
      for (const metric of input.metrics) {
        await tx.query(
          "INSERT INTO public.control_evaluation_profile_metrics (profile_id, metric_id, weight, required) VALUES ($1::uuid, $2::uuid, $3, $4)",
          [profile.id, metric.metric_id, metric.weight, metric.required ?? true]
        );
      }
      for (const constraint of input.constraints ?? []) {
        await tx.query(
          `INSERT INTO public.control_evaluation_profile_constraints
            (profile_id, metric_id, kind, lower_bound, upper_bound, critical)
           VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6)`,
          [profile.id, constraint.metric_id, constraint.kind, constraint.lower_bound ?? null, constraint.upper_bound ?? null, constraint.critical ?? false]
        );
      }
      await tx.query(
        `INSERT INTO iot_schema.auditoria (entidad, entidad_id, accion, cambios, contexto)
         VALUES ('control_evaluation_profiles', $1::uuid, 'EVALUATION_PROFILE_VERSION_CREATED', $2::jsonb, $3::jsonb)`,
        [profile.id, JSON.stringify({ code: input.code, version, metric_ids: ids, weights: input.metrics.map((metric) => metric.weight) }),
          JSON.stringify({ subsystem: "apps/topology-next", capability: "adaptive-experimentation-evaluation", project_id: projectId,
            actor_id: createdBy, execution_context: "SIMULATION", physical_effects: false })]
      );
      const persisted = await tx.query(this.profileQuery("WHERE p.id=$1::uuid"), [profile.id]);
      return mapProfile(persisted.rows[0]);
    });
  }

  private profileQuery(where: string): string {
    return `
      SELECT p.*, COALESCE((SELECT jsonb_agg(jsonb_build_object(
        'id', m.id, 'code', m.code, 'version', m.version, 'name', m.name, 'description', m.description,
        'unit', m.unit, 'direction', m.direction, 'normalization_method', m.normalization_method,
        'normalization_config', m.normalization_config, 'weightable', m.weightable, 'active', m.active,
        'created_at', m.created_at, 'weight', pm.weight, 'required', pm.required
      ) ORDER BY m.code, m.version DESC)
      FROM public.control_evaluation_profile_metrics pm
      JOIN public.control_evaluation_metrics m ON m.id=pm.metric_id
      WHERE pm.profile_id=p.id), '[]'::jsonb) AS metrics,
      COALESCE((SELECT jsonb_agg(jsonb_build_object(
        'id', c.id, 'metric_id', c.metric_id, 'kind', c.kind, 'lower_bound', c.lower_bound,
        'upper_bound', c.upper_bound, 'critical', c.critical
      ) ORDER BY c.metric_id)
      FROM public.control_evaluation_profile_constraints c
      WHERE c.profile_id=p.id), '[]'::jsonb) AS constraints
      FROM public.control_evaluation_profiles p
      ${where}
      ORDER BY p.code, p.version DESC, p.created_at DESC`;
  }
}
