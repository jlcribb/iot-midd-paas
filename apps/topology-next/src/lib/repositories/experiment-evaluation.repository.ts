import type { QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";
import { withTransaction, type SqlExecutor, type TransactionRunner } from "@/lib/db/tx";
import type { EvaluationComputation, EvaluationContext, EvaluationMetricResult, ExperimentEvaluation, SimulationResultEvidence, SimulationTraceEvidence } from "@/lib/dto/experiment-evaluation.dto";
import type { EvaluationProfileConstraint } from "@/lib/dto/evaluation-profile.dto";

function object(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function constraintDefinitions(value: unknown): EvaluationProfileConstraint[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => {
    const row = object(item);
    return {
      id: typeof row.id === "string" ? row.id : undefined, metric_id: String(row.metric_id),
      kind: String(row.kind) as EvaluationProfileConstraint["kind"],
      lower_bound: row.lower_bound === null || row.lower_bound === undefined ? null : Number(row.lower_bound),
      upper_bound: row.upper_bound === null || row.upper_bound === undefined ? null : Number(row.upper_bound),
      critical: Boolean(row.critical)
    };
  });
}

function mapMetric(row: QueryResultRow): EvaluationMetricResult {
  return {
    metric_id: String(row.metric_id), metric_code: String(row.metric_code), metric_version: Number(row.metric_version),
    availability_status: String(row.availability_status) as EvaluationMetricResult["availability_status"],
    availability_reason: row.availability_reason === null ? null : String(row.availability_reason),
    raw_value: row.raw_value === null ? null : Number(row.raw_value), normalized_value: row.normalized_value === null ? null : Number(row.normalized_value),
    weight: Number(row.weight), weighted_contribution: row.weighted_contribution === null ? null : Number(row.weighted_contribution),
    direction: String(row.direction) as EvaluationMetricResult["direction"],
    normalization_method: String(row.normalization_method) as EvaluationMetricResult["normalization_method"],
    normalization_config: object(row.normalization_config), constraint_status: String(row.constraint_status) as EvaluationMetricResult["constraint_status"],
    constraint_definition: constraintDefinitions(row.constraint_definition)
  };
}

function mapEvaluation(row: QueryResultRow): ExperimentEvaluation {
  const metrics = Array.isArray(row.metrics) ? row.metrics.map((metric) => mapMetric(metric)) : [];
  return {
    id: String(row.id), project_id: String(row.project_id), simulation_run_id: String(row.simulation_run_id),
    simulation_result_id: String(row.simulation_result_id), evaluation_profile_id: String(row.evaluation_profile_id),
    evaluation_profile_version: Number(row.evaluation_profile_version), status: String(row.status) as ExperimentEvaluation["status"],
    score: row.score === null ? null : Number(row.score), evaluation_hash: String(row.evaluation_hash),
    constraint_satisfied_count: Number(row.constraint_satisfied_count), constraint_violated_count: Number(row.constraint_violated_count),
    constraint_unknown_count: Number(row.constraint_unknown_count), critical_constraint_violation: Boolean(row.critical_constraint_violation),
    schema_version: 1, engine_version: String(row.engine_version), created_by: String(row.created_by), created_at: String(row.created_at), metrics
  };
}

function mapResult(row: QueryResultRow): SimulationResultEvidence {
  const traceRow = object(row.trace);
  const points = Array.isArray(traceRow.points) ? traceRow.points.map((point) => {
    const item = object(point); return { sequence_number: Number(item.sequence_number), simulation_time_seconds: Number(item.simulation_time_seconds),
      process_value: Number(item.process_value), setpoint: Number(item.setpoint), control_output: Number(item.control_output),
      actuator_state: String(item.actuator_state), constraint_state: item.constraint_state === null ? null : String(item.constraint_state) };
  }) : [];
  const trace: SimulationTraceEvidence | null = typeof traceRow.trace_hash === "string" ? {
    trace_hash: traceRow.trace_hash, trace_schema_version: Number(traceRow.trace_schema_version), time_representation: String(traceRow.time_representation),
    point_count: Number(traceRow.point_count), simulation_duration_seconds: Number(traceRow.simulation_duration_seconds), points
  } : null;
  return {
    id: String(row.id), project_id: String(row.project_id), session_id: String(row.session_id), run_id: String(row.run_id),
    result_fingerprint: String(row.result_fingerprint), processed_events: Number(row.processed_events),
    actionable_recommendation_count: Number(row.actionable_recommendation_count), failed_domain_event_count: Number(row.failed_domain_event_count), trace
  };
}

export class ExperimentEvaluationRepository {
  constructor(private readonly db: SqlExecutor = pool, private readonly transaction: TransactionRunner = withTransaction) {}

  async findSimulationResult(projectId: string, resultId: string): Promise<SimulationResultEvidence | null> {
    const result = await this.db.query(
      `SELECT r.id, r.project_id, r.session_id, r.run_id, r.result_fingerprint, r.processed_events,
              r.actionable_recommendation_count, r.failed_domain_event_count,
        COALESCE((SELECT jsonb_build_object('trace_hash',t.trace_hash,'trace_schema_version',t.trace_schema_version,
          'time_representation',t.time_representation,'point_count',t.point_count,
          'simulation_duration_seconds',t.simulation_duration_seconds,'points',COALESCE((SELECT jsonb_agg(jsonb_build_object(
            'sequence_number',p.sequence_number,'simulation_time_seconds',p.simulation_time_seconds,'process_value',p.process_value,
            'setpoint',p.setpoint,'control_output',p.control_output,'actuator_state',p.actuator_state,'constraint_state',p.constraint_state
          ) ORDER BY p.sequence_number) FROM public.control_simulation_trace_points p WHERE p.trace_id=t.id),'[]'::jsonb))
          FROM public.control_simulation_traces t WHERE t.simulation_result_id=r.id), '{}'::jsonb) AS trace
       FROM public.control_simulation_results r WHERE r.project_id=$1::uuid AND r.id=$2::uuid`, [projectId, resultId]
    );
    return result.rows[0] ? mapResult(result.rows[0]) : null;
  }

  async createOrGet(projectId: string, createdBy: string, context: EvaluationContext, computation: EvaluationComputation): Promise<ExperimentEvaluation> {
    return this.transaction(async (tx) => {
      const inserted = await tx.query(`
        INSERT INTO public.control_experiment_evaluations
          (project_id, simulation_run_id, simulation_result_id, evaluation_profile_id, evaluation_profile_version,
           status, score, constraint_satisfied_count, constraint_violated_count, constraint_unknown_count,
           critical_constraint_violation, evaluation_hash, schema_version, engine_version, created_by, physical_effects_allowed)
        VALUES ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5, $6, $7, $8, $9, $10, $11, $12, 1, $13, $14, FALSE)
        ON CONFLICT (simulation_result_id, evaluation_profile_id, engine_version) DO NOTHING
        RETURNING id
      `, [projectId, context.result.run_id, context.result.id, context.profile.id, context.profile.version,
        computation.status, computation.score, computation.constraint_satisfied_count, computation.constraint_violated_count,
        computation.constraint_unknown_count, computation.critical_constraint_violation, computation.evaluation_hash,
        computation.engine_version, createdBy]);
      const evaluationId = inserted.rows[0]?.id as string | undefined;
      if (!evaluationId) return this.getByIdentity(tx, context.result.id, context.profile.id, computation.engine_version);

      for (const metric of computation.metrics) {
        await tx.query(`
          INSERT INTO public.control_experiment_evaluation_metrics
            (evaluation_id, metric_id, metric_code, metric_version, availability_status, availability_reason,
             raw_value, normalized_value, weight, weighted_contribution, direction, normalization_method,
             normalization_config, constraint_status, constraint_definition)
          VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13::jsonb, $14, $15::jsonb)
        `, [evaluationId, metric.metric_id, metric.metric_code, metric.metric_version, metric.availability_status,
          metric.availability_reason, metric.raw_value, metric.normalized_value, metric.weight, metric.weighted_contribution,
          metric.direction, metric.normalization_method, JSON.stringify(metric.normalization_config), metric.constraint_status,
          JSON.stringify(metric.constraint_definition)]);
      }
      await tx.query(
        `INSERT INTO iot_schema.auditoria (entidad, entidad_id, accion, cambios, contexto)
         VALUES ('control_experiment_evaluations', $1::uuid, 'EXPERIMENT_EVALUATION_CREATED', $2::jsonb, $3::jsonb)`,
        [evaluationId, JSON.stringify({ simulation_result_id: context.result.id, evaluation_profile_id: context.profile.id,
          evaluation_hash: computation.evaluation_hash, status: computation.status, engine_version: computation.engine_version }),
          JSON.stringify({ subsystem: "apps/topology-next", capability: "deterministic-experiment-evaluation", project_id: projectId,
            actor_id: createdBy, execution_context: "SIMULATION", physical_effects: false })]
      );
      return this.getById(tx, projectId, evaluationId);
    });
  }

  async listByProject(projectId: string): Promise<ExperimentEvaluation[]> {
    const result = await this.db.query(this.evaluationQuery("WHERE e.project_id=$1::uuid"), [projectId]);
    return result.rows.map(mapEvaluation);
  }

  async findByProjectAndId(projectId: string, evaluationId: string): Promise<ExperimentEvaluation | null> {
    const result = await this.db.query(this.evaluationQuery("WHERE e.project_id=$1::uuid AND e.id=$2::uuid"), [projectId, evaluationId]);
    return result.rows[0] ? mapEvaluation(result.rows[0]) : null;
  }

  private async getByIdentity(tx: SqlExecutor, simulationResultId: string, profileId: string, engineVersion: string): Promise<ExperimentEvaluation> {
    const result = await tx.query(this.evaluationQuery("WHERE e.simulation_result_id=$1::uuid AND e.evaluation_profile_id=$2::uuid AND e.engine_version=$3"), [simulationResultId, profileId, engineVersion]);
    return mapEvaluation(result.rows[0]);
  }

  private async getById(tx: SqlExecutor, projectId: string, evaluationId: string): Promise<ExperimentEvaluation> {
    const result = await tx.query(this.evaluationQuery("WHERE e.project_id=$1::uuid AND e.id=$2::uuid"), [projectId, evaluationId]);
    return mapEvaluation(result.rows[0]);
  }

  private evaluationQuery(where: string): string {
    return `
      SELECT e.*, COALESCE((SELECT jsonb_agg(jsonb_build_object(
        'metric_id', m.metric_id, 'metric_code', m.metric_code, 'metric_version', m.metric_version,
        'availability_status', m.availability_status, 'availability_reason', m.availability_reason,
        'raw_value', m.raw_value, 'normalized_value', m.normalized_value, 'weight', m.weight,
        'weighted_contribution', m.weighted_contribution, 'direction', m.direction,
        'normalization_method', m.normalization_method, 'normalization_config', m.normalization_config,
        'constraint_status', m.constraint_status, 'constraint_definition', m.constraint_definition
      ) ORDER BY m.metric_code, m.metric_version)
      FROM public.control_experiment_evaluation_metrics m
      WHERE m.evaluation_id=e.id), '[]'::jsonb) AS metrics
      FROM public.control_experiment_evaluations e
      ${where}
      ORDER BY e.created_at DESC, e.id DESC`;
  }
}
