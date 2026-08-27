import { canonicalNumber } from "@/lib/evaluation/normalization";
import { sha256Canonical } from "@/lib/simulation/canonical";
import type { ExperimentEvaluation, EvaluationMetricResult } from "@/lib/dto/experiment-evaluation.dto";
import {
  COMPARISON_ENGINE_VERSION, COMPARISON_SCHEMA_VERSION, DEFAULT_COMPARISON_POLICY,
  type ComparisonComputation, type ComparisonPolicy, type CompatibilityResult, type MetricComparisonEvidence,
  type MetricComparisonRelation, type ParetoFrontResult
} from "@/lib/dto/experiment-comparison.dto";

function key(metric: Pick<EvaluationMetricResult, "metric_code" | "metric_version">): string {
  return `${metric.metric_code}@${metric.metric_version}`;
}
function completed(evaluation: ExperimentEvaluation): boolean {
  return evaluation.status === "COMPLETED" || evaluation.status === "COMPLETED_WITH_WARNINGS";
}
function sortedMetricKeys(evaluation: ExperimentEvaluation): string[] { return evaluation.metrics.map(key).sort(); }
function sameStrings(left: string[], right: string[]): boolean { return left.length === right.length && left.every((item, index) => item === right[index]); }

/** Compatibility is explicit: comparisons never bridge project, profile, evidence, engine, or schema boundaries. */
export function checkComparisonCompatibility(baseline: ExperimentEvaluation, candidate: ExperimentEvaluation): CompatibilityResult {
  const profile_metric_count = baseline.metrics.length;
  if (baseline.project_id !== candidate.project_id) return { compatible: false, reason: "PROJECT_MISMATCH", profile_metric_count };
  if (baseline.evaluation_profile_id !== candidate.evaluation_profile_id || baseline.evaluation_profile_version !== candidate.evaluation_profile_version)
    return { compatible: false, reason: "EVALUATION_PROFILE_MISMATCH", profile_metric_count };
  if (baseline.engine_version !== candidate.engine_version || baseline.schema_version !== candidate.schema_version)
    return { compatible: false, reason: "EVALUATION_SEMANTICS_MISMATCH", profile_metric_count };
  if (!sameStrings(sortedMetricKeys(baseline), sortedMetricKeys(candidate))) return { compatible: false, reason: "METRIC_SET_MISMATCH", profile_metric_count };
  if (!completed(baseline) || !completed(candidate)) return { compatible: false, reason: "EVALUATION_NOT_EVALUABLE", profile_metric_count };
  return { compatible: true, reason: null, profile_metric_count };
}

function metricRelation(delta: number, epsilon: number): MetricComparisonRelation {
  if (delta > epsilon) return "BETTER";
  if (delta < -epsilon) return "WORSE";
  return "EQUIVALENT";
}

function unavailable(metric: EvaluationMetricResult): boolean {
  return metric.availability_status !== "AVAILABLE" || metric.normalized_value === null || metric.raw_value === null;
}

function metricEvidence(baseline: EvaluationMetricResult, candidate: EvaluationMetricResult, epsilon: number): MetricComparisonEvidence {
  if (unavailable(baseline) || unavailable(candidate)) return {
    metric_id: baseline.metric_id, metric_code: baseline.metric_code, metric_version: baseline.metric_version,
    baseline_raw_value: baseline.raw_value, candidate_raw_value: candidate.raw_value,
    baseline_normalized_value: baseline.normalized_value, candidate_normalized_value: candidate.normalized_value,
    raw_delta: null, normalized_delta: null, relation: "UNAVAILABLE", epsilon
  };
  const raw_delta = canonicalNumber((candidate.raw_value as number) - (baseline.raw_value as number));
  const normalized_delta = canonicalNumber((candidate.normalized_value as number) - (baseline.normalized_value as number));
  return { metric_id: baseline.metric_id, metric_code: baseline.metric_code, metric_version: baseline.metric_version,
    baseline_raw_value: baseline.raw_value, candidate_raw_value: candidate.raw_value,
    baseline_normalized_value: baseline.normalized_value, candidate_normalized_value: candidate.normalized_value,
    raw_delta, normalized_delta, relation: metricRelation(normalized_delta, epsilon), epsilon };
}

export function compareExperimentEvaluations(
  baseline: ExperimentEvaluation, candidate: ExperimentEvaluation, policy: ComparisonPolicy = DEFAULT_COMPARISON_POLICY
): ComparisonComputation {
  const compatibility = checkComparisonCompatibility(baseline, candidate);
  const candidateByKey = new Map(candidate.metrics.map((metric) => [key(metric), metric]));
  const metrics = compatibility.compatible
    ? [...baseline.metrics].sort((a, b) => key(a).localeCompare(key(b))).map((metric) => metricEvidence(metric, candidateByKey.get(key(metric)) as EvaluationMetricResult, policy.epsilon))
    : [];
  const comparable = metrics.filter((metric) => metric.relation !== "UNAVAILABLE");
  const better = comparable.filter((metric) => metric.relation === "BETTER").length;
  const worse = comparable.filter((metric) => metric.relation === "WORSE").length;
  const candidate_dominates_baseline = compatibility.compatible && comparable.length > 0 && worse === 0 && better > 0;
  const baseline_dominates_candidate = compatibility.compatible && comparable.length > 0 && better === 0 && worse > 0;
  const newCriticalViolation = candidate.critical_constraint_violation && !baseline.critical_constraint_violation;
  let relation: ComparisonComputation["relation"] = "INCOMPARABLE";
  if (compatibility.compatible) {
    if (newCriticalViolation) relation = "TRADE_OFF";
    else if (candidate_dominates_baseline) relation = "BETTER";
    else if (baseline_dominates_candidate) relation = "WORSE";
    else if (better > 0 && worse > 0) relation = "TRADE_OFF";
    else relation = "EQUIVALENT";
  }
  const score_delta = compatibility.compatible && baseline.score !== null && candidate.score !== null
    ? canonicalNumber(candidate.score - baseline.score) : null;
  const profile_metric_count = compatibility.profile_metric_count;
  const coverage_ratio = profile_metric_count === 0 ? 0 : canonicalNumber(comparable.length / profile_metric_count);
  const canonical = { schema_version: COMPARISON_SCHEMA_VERSION, engine_version: COMPARISON_ENGINE_VERSION,
    baseline_evaluation_hash: baseline.evaluation_hash, candidate_evaluation_hash: candidate.evaluation_hash,
    policy, incompatibility_reason: compatibility.reason, relation, score_delta, candidate_dominates_baseline,
    baseline_dominates_candidate, comparable_metric_count: comparable.length, profile_metric_count, coverage_ratio,
    constraint_semantics: { baseline_critical: baseline.critical_constraint_violation, candidate_critical: candidate.critical_constraint_violation, new_critical_violation: newCriticalViolation }, metrics };
  return { ...canonical, comparison_hash: sha256Canonical(canonical), schema_version: COMPARISON_SCHEMA_VERSION,
    engine_version: COMPARISON_ENGINE_VERSION, policy, metrics };
}

/** A front is only meaningful inside one explicitly compatible semantic cohort. */
export function computeParetoFront(evaluations: ExperimentEvaluation[], policy: ComparisonPolicy = DEFAULT_COMPARISON_POLICY): ParetoFrontResult {
  const eligible = evaluations.filter(completed);
  if (eligible.length === 0) return { pareto_evaluation_ids: [], dominated_evaluation_ids: [], excluded_evaluation_ids: evaluations.map((item) => item.id), exclusions: evaluations.map((item) => ({ evaluation_id: item.id, reason: "EVALUATION_NOT_EVALUABLE" })), dominance_relations: [] };
  const anchor = eligible[0];
  const cohort = eligible.filter((evaluation) => checkComparisonCompatibility(anchor, evaluation).compatible);
  const exclusions = evaluations.filter((evaluation) => !cohort.some((item) => item.id === evaluation.id)).map((evaluation) => ({
    evaluation_id: evaluation.id, reason: completed(evaluation) ? "INCOMPATIBLE_SEMANTIC_COHORT" : "EVALUATION_NOT_EVALUABLE"
  }));
  const dominance_relations: ParetoFrontResult["dominance_relations"] = [];
  for (const candidate of cohort) for (const baseline of cohort) {
    if (candidate.id === baseline.id) continue;
    const comparison = compareExperimentEvaluations(baseline, candidate, policy);
    if (comparison.candidate_dominates_baseline && !candidate.critical_constraint_violation) {
      dominance_relations.push({ dominator_evaluation_id: candidate.id, dominated_evaluation_id: baseline.id });
    }
  }
  const dominated = new Set(dominance_relations.map((relation) => relation.dominated_evaluation_id));
  return { pareto_evaluation_ids: cohort.filter((evaluation) => !dominated.has(evaluation.id)).map((evaluation) => evaluation.id).sort(),
    dominated_evaluation_ids: [...dominated].sort(), excluded_evaluation_ids: exclusions.map((item) => item.evaluation_id).sort(), exclusions, dominance_relations };
}
