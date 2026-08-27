import type { QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";
import { withTransaction, type SqlExecutor, type TransactionRunner } from "@/lib/db/tx";
import type { ComparisonComputation, ExperimentComparison, MetricComparisonEvidence } from "@/lib/dto/experiment-comparison.dto";

function object(value: unknown): Record<string, unknown> { return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {}; }
function mapMetric(row: QueryResultRow): MetricComparisonEvidence {
  return { metric_id: String(row.metric_id), metric_code: String(row.metric_code), metric_version: Number(row.metric_version),
    baseline_raw_value: row.baseline_raw_value === null ? null : Number(row.baseline_raw_value), candidate_raw_value: row.candidate_raw_value === null ? null : Number(row.candidate_raw_value),
    baseline_normalized_value: row.baseline_normalized_value === null ? null : Number(row.baseline_normalized_value), candidate_normalized_value: row.candidate_normalized_value === null ? null : Number(row.candidate_normalized_value),
    raw_delta: row.raw_delta === null ? null : Number(row.raw_delta), normalized_delta: row.normalized_delta === null ? null : Number(row.normalized_delta),
    relation: String(row.relation) as MetricComparisonEvidence["relation"], epsilon: Number(row.epsilon) };
}
function mapComparison(row: QueryResultRow): ExperimentComparison {
  return { id: String(row.id), project_id: String(row.project_id), baseline_evaluation_id: String(row.baseline_evaluation_id), candidate_evaluation_id: String(row.candidate_evaluation_id),
    relation: String(row.relation) as ExperimentComparison["relation"], incompatibility_reason: row.incompatibility_reason === null ? null : String(row.incompatibility_reason),
    score_delta: row.score_delta === null ? null : Number(row.score_delta), candidate_dominates_baseline: Boolean(row.candidate_dominates_baseline), baseline_dominates_candidate: Boolean(row.baseline_dominates_candidate),
    comparable_metric_count: Number(row.comparable_metric_count), profile_metric_count: Number(row.profile_metric_count), coverage_ratio: Number(row.coverage_ratio),
    comparison_hash: String(row.comparison_hash), schema_version: 1, engine_version: String(row.engine_version), policy: object(row.comparison_policy) as unknown as ExperimentComparison["policy"],
    created_by: String(row.created_by), created_at: String(row.created_at), physical_effects_allowed: false,
    metrics: Array.isArray(row.metrics) ? row.metrics.map(mapMetric) : [] };
}

export class ExperimentComparisonRepository {
  constructor(private readonly db: SqlExecutor = pool, private readonly transaction: TransactionRunner = withTransaction) {}

  async createOrGet(projectId: string, createdBy: string, baselineEvaluationId: string, candidateEvaluationId: string, computation: ComparisonComputation): Promise<ExperimentComparison> {
    return this.transaction(async (tx) => {
      const inserted = await tx.query(`
        INSERT INTO public.control_experiment_comparisons
          (project_id, baseline_evaluation_id, candidate_evaluation_id, relation, incompatibility_reason, score_delta,
           candidate_dominates_baseline, baseline_dominates_candidate, comparable_metric_count, profile_metric_count,
           coverage_ratio, comparison_hash, schema_version, engine_version, comparison_policy, created_by, physical_effects_allowed)
        VALUES ($1::uuid,$2::uuid,$3::uuid,$4,$5,$6,$7,$8,$9,$10,$11,$12,1,$13,$14::jsonb,$15,FALSE)
        ON CONFLICT (comparison_hash) DO NOTHING RETURNING id
      `, [projectId, baselineEvaluationId, candidateEvaluationId, computation.relation, computation.incompatibility_reason,
        computation.score_delta, computation.candidate_dominates_baseline, computation.baseline_dominates_candidate,
        computation.comparable_metric_count, computation.profile_metric_count, computation.coverage_ratio, computation.comparison_hash,
        computation.engine_version, JSON.stringify(computation.policy), createdBy]);
      const id = inserted.rows[0]?.id as string | undefined;
      if (!id) return this.getByHash(tx, computation.comparison_hash);
      for (const metric of computation.metrics) await tx.query(`
        INSERT INTO public.control_experiment_comparison_metrics
          (comparison_id, metric_id, metric_code, metric_version, baseline_raw_value, candidate_raw_value,
           baseline_normalized_value, candidate_normalized_value, raw_delta, normalized_delta, relation, epsilon)
        VALUES ($1::uuid,$2::uuid,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
      `, [id, metric.metric_id, metric.metric_code, metric.metric_version, metric.baseline_raw_value, metric.candidate_raw_value,
        metric.baseline_normalized_value, metric.candidate_normalized_value, metric.raw_delta, metric.normalized_delta, metric.relation, metric.epsilon]);
      await tx.query(`INSERT INTO iot_schema.auditoria (entidad, entidad_id, accion, cambios, contexto)
        VALUES ('control_experiment_comparisons',$1::uuid,'EXPERIMENT_COMPARISON_CREATED',$2::jsonb,$3::jsonb)`,
      [id, JSON.stringify({ baseline_evaluation_id: baselineEvaluationId, candidate_evaluation_id: candidateEvaluationId,
        comparison_hash: computation.comparison_hash, relation: computation.relation, engine_version: computation.engine_version }),
       JSON.stringify({ subsystem: "apps/topology-next", capability: "experiment-comparison-pareto", project_id: projectId,
         actor_id: createdBy, execution_context: "SIMULATION", physical_effects: false })]);
      return this.getById(tx, projectId, id);
    });
  }
  async listByProject(projectId: string): Promise<ExperimentComparison[]> { const result = await this.db.query(this.query("WHERE c.project_id=$1::uuid"), [projectId]); return result.rows.map(mapComparison); }
  async findByProjectAndId(projectId: string, id: string): Promise<ExperimentComparison | null> { const result = await this.db.query(this.query("WHERE c.project_id=$1::uuid AND c.id=$2::uuid"), [projectId, id]); return result.rows[0] ? mapComparison(result.rows[0]) : null; }
  private async getByHash(tx: SqlExecutor, hash: string): Promise<ExperimentComparison> { const result = await tx.query(this.query("WHERE c.comparison_hash=$1"), [hash]); return mapComparison(result.rows[0]); }
  private async getById(tx: SqlExecutor, projectId: string, id: string): Promise<ExperimentComparison> { const result = await tx.query(this.query("WHERE c.project_id=$1::uuid AND c.id=$2::uuid"), [projectId, id]); return mapComparison(result.rows[0]); }
  private query(where: string): string { return `SELECT c.*, COALESCE((SELECT jsonb_agg(jsonb_build_object(
      'metric_id',m.metric_id,'metric_code',m.metric_code,'metric_version',m.metric_version,
      'baseline_raw_value',m.baseline_raw_value,'candidate_raw_value',m.candidate_raw_value,
      'baseline_normalized_value',m.baseline_normalized_value,'candidate_normalized_value',m.candidate_normalized_value,
      'raw_delta',m.raw_delta,'normalized_delta',m.normalized_delta,'relation',m.relation,'epsilon',m.epsilon
    ) ORDER BY m.metric_code,m.metric_version) FROM public.control_experiment_comparison_metrics m WHERE m.comparison_id=c.id), '[]'::jsonb) AS metrics
    FROM public.control_experiment_comparisons c ${where} ORDER BY c.created_at DESC,c.id DESC`; }
}
