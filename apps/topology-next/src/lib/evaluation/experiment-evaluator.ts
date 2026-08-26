import type { EvaluationComputation, EvaluationContext, EvaluationMetricResult, ConstraintStatus } from "@/lib/dto/experiment-evaluation.dto";
import type { EvaluationProfileConstraint } from "@/lib/dto/evaluation-profile.dto";
import { sha256Canonical } from "@/lib/simulation/canonical";
import { kpiForMetric } from "@/lib/evaluation/kpi-extractor";
import { canonicalNumber, EVALUATION_SCHEMA_VERSION, NORMALIZATION_ENGINE_VERSION, normalizeMetric } from "@/lib/evaluation/normalization";

function constraintStatus(raw: number | null, constraints: EvaluationProfileConstraint[]): ConstraintStatus {
  if (constraints.length === 0) return "NOT_APPLICABLE";
  if (raw === null) return "UNKNOWN";
  return constraints.some((constraint) =>
    (constraint.kind === "MINIMUM" && raw < (constraint.lower_bound as number)) ||
    (constraint.kind === "MAXIMUM" && raw > (constraint.upper_bound as number)) ||
    (constraint.kind === "RANGE" && (raw < (constraint.lower_bound as number) || raw > (constraint.upper_bound as number)))
  ) ? "VIOLATED" : "SATISFIED";
}

function constraintsFor(metricId: string, constraints: EvaluationProfileConstraint[]): EvaluationProfileConstraint[] {
  return constraints.filter((constraint) => constraint.metric_id === metricId)
    .map((constraint) => ({ ...constraint }));
}

export function evaluateExperiment(context: EvaluationContext): EvaluationComputation {
  const details: EvaluationMetricResult[] = [];
  let invalidInput = false;
  let requiredUnavailable = false;
  let optionalUnavailable = false;
  let score = 0;
  let satisfied = 0;
  let violated = 0;
  let unknown = 0;
  let criticalViolation = false;

  for (const profileMetric of context.profile.metrics) {
    const metric = profileMetric.metric;
    const raw = kpiForMetric(context.result, metric.code);
    const constraints = constraintsFor(metric.id, context.profile.constraints);
    let normalized: number | null = null;
    let contribution: number | null = null;
    let status = raw.status;
    let reason = raw.reason;
    if (raw.status === "AVAILABLE" && raw.value !== null) {
      try {
        normalized = normalizeMetric(metric, raw.value);
        contribution = canonicalNumber(profileMetric.weight * normalized);
        score += contribution;
      } catch (error) {
        status = "INVALID";
        reason = error instanceof Error ? error.message : "Invalid metric definition";
        invalidInput = true;
      }
    }
    if (status !== "AVAILABLE") {
      if (profileMetric.required) requiredUnavailable = true;
      else optionalUnavailable = true;
    }
    const appliedConstraintStatus = constraintStatus(status === "AVAILABLE" ? raw.value : null, constraints);
    if (constraints.length > 0) {
      if (appliedConstraintStatus === "SATISFIED") satisfied += constraints.length;
      if (appliedConstraintStatus === "VIOLATED") {
        violated += constraints.length;
        criticalViolation ||= constraints.some((constraint) => constraint.critical);
      }
      if (appliedConstraintStatus === "UNKNOWN") unknown += constraints.length;
    }
    details.push({
      metric_id: metric.id, metric_code: metric.code, metric_version: metric.version,
      availability_status: status, availability_reason: reason,
      raw_value: status === "AVAILABLE" ? canonicalNumber(raw.value as number) : null,
      normalized_value: normalized, weight: canonicalNumber(profileMetric.weight), weighted_contribution: contribution,
      direction: metric.direction, normalization_method: metric.normalization_method,
      normalization_config: metric.normalization_config, constraint_status: appliedConstraintStatus,
      constraint_definition: constraints
    });
  }

  const status = invalidInput ? "INVALID_INPUT" : requiredUnavailable ? "NOT_EVALUABLE" : optionalUnavailable || unknown > 0 ? "COMPLETED_WITH_WARNINGS" : "COMPLETED";
  const finalScore = status === "INVALID_INPUT" || status === "NOT_EVALUABLE" ? null : canonicalNumber(score);
  const canonicalMetrics = [...details].sort((left, right) => left.metric_code.localeCompare(right.metric_code) || left.metric_version - right.metric_version);
  const evaluation_hash = sha256Canonical({
    schema_version: EVALUATION_SCHEMA_VERSION, engine_version: NORMALIZATION_ENGINE_VERSION,
    simulation_result: { result_fingerprint: context.result.result_fingerprint },
    evaluation_profile: { id: context.profile.id, version: context.profile.version },
    status, score: finalScore, metrics: canonicalMetrics,
    constraint_summary: { satisfied, violated, unknown, critical_violation: criticalViolation }
  });
  return {
    status, score: finalScore, evaluation_hash, constraint_satisfied_count: satisfied,
    constraint_violated_count: violated, constraint_unknown_count: unknown,
    critical_constraint_violation: criticalViolation, schema_version: EVALUATION_SCHEMA_VERSION,
    engine_version: NORMALIZATION_ENGINE_VERSION, metrics: details
  };
}
