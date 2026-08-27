import type { ExperimentEvaluation, EvaluationMetricResult } from "@/lib/dto/experiment-evaluation.dto";

export const COMPARISON_ENGINE_VERSION = "experiment-comparison-engine:v1";
export const COMPARISON_SCHEMA_VERSION = 1 as const;
/** Explicit semantic tolerance for canonical normalized values (nine decimals). */
export const COMPARISON_EPSILON = 0.000001;

export type ComparisonRelation = "BETTER" | "WORSE" | "EQUIVALENT" | "TRADE_OFF" | "INCOMPARABLE";
export type MetricComparisonRelation = "BETTER" | "WORSE" | "EQUIVALENT" | "UNAVAILABLE";

export interface ComparisonPolicy {
  schema_version: 1;
  epsilon: number;
  constraints: { new_critical_violation_relation: "TRADE_OFF" };
  unavailable_metrics: "EXCLUDE_FROM_DOMINANCE_AND_REPORT_COVERAGE";
}

export const DEFAULT_COMPARISON_POLICY: ComparisonPolicy = {
  schema_version: 1,
  epsilon: COMPARISON_EPSILON,
  constraints: { new_critical_violation_relation: "TRADE_OFF" },
  unavailable_metrics: "EXCLUDE_FROM_DOMINANCE_AND_REPORT_COVERAGE"
};

export interface MetricComparisonEvidence {
  metric_id: string; metric_code: string; metric_version: number;
  baseline_raw_value: number | null; candidate_raw_value: number | null;
  baseline_normalized_value: number | null; candidate_normalized_value: number | null;
  raw_delta: number | null; normalized_delta: number | null;
  relation: MetricComparisonRelation; epsilon: number;
}

export interface ComparisonComputation {
  relation: ComparisonRelation; incompatibility_reason: string | null;
  score_delta: number | null; candidate_dominates_baseline: boolean; baseline_dominates_candidate: boolean;
  comparable_metric_count: number; profile_metric_count: number; coverage_ratio: number;
  comparison_hash: string; schema_version: 1; engine_version: string; policy: ComparisonPolicy;
  metrics: MetricComparisonEvidence[];
}

export interface ExperimentComparison extends ComparisonComputation {
  id: string; project_id: string; baseline_evaluation_id: string; candidate_evaluation_id: string;
  created_by: string; created_at: string; physical_effects_allowed: false;
}

export interface ComparisonContext { baseline: ExperimentEvaluation; candidate: ExperimentEvaluation; }
export interface CompatibilityResult { compatible: boolean; reason: string | null; profile_metric_count: number; }
export interface ParetoFrontResult {
  pareto_evaluation_ids: string[]; dominated_evaluation_ids: string[]; excluded_evaluation_ids: string[];
  exclusions: Array<{ evaluation_id: string; reason: string }>;
  dominance_relations: Array<{ dominator_evaluation_id: string; dominated_evaluation_id: string }>;
}

export type EvaluationMetricSnapshot = Pick<EvaluationMetricResult, "metric_id" | "metric_code" | "metric_version" | "availability_status" | "raw_value" | "normalized_value">;
