import type { EvaluationMetric, EvaluationProfile, EvaluationProfileConstraint } from "@/lib/dto/evaluation-profile.dto";
import type { KpiAvailability } from "@/lib/evaluation/kpi-extractor";

export type ExperimentEvaluationStatus = "PENDING" | "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "INVALID_INPUT" | "NOT_EVALUABLE";
export type ConstraintStatus = "SATISFIED" | "VIOLATED" | "UNKNOWN" | "NOT_APPLICABLE";

export interface SimulationResultEvidence {
  id: string; project_id: string; session_id: string; run_id: string; result_fingerprint: string;
  processed_events: number; actionable_recommendation_count: number; failed_domain_event_count: number;
  trace?: SimulationTraceEvidence | null;
}

export interface SimulationTracePointEvidence {
  sequence_number: number; simulation_time_seconds: number; process_value: number; setpoint: number;
  control_output: number; actuator_state: string; constraint_state: string | null;
}
export interface SimulationTraceEvidence {
  trace_hash: string; trace_schema_version: number; time_representation: string;
  point_count: number; simulation_duration_seconds: number; points: SimulationTracePointEvidence[];
}

export interface EvaluationMetricResult {
  metric_id: string; metric_code: string; metric_version: number; availability_status: KpiAvailability;
  availability_reason: string | null; raw_value: number | null; normalized_value: number | null;
  weight: number; weighted_contribution: number | null; direction: EvaluationMetric["direction"];
  normalization_method: EvaluationMetric["normalization_method"]; normalization_config: Record<string, unknown>;
  constraint_status: ConstraintStatus; constraint_definition: EvaluationProfileConstraint[];
}

export interface EvaluationComputation {
  status: ExperimentEvaluationStatus; score: number | null; evaluation_hash: string;
  constraint_satisfied_count: number; constraint_violated_count: number; constraint_unknown_count: number;
  critical_constraint_violation: boolean; schema_version: 1; engine_version: string;
  metrics: EvaluationMetricResult[];
}

export interface ExperimentEvaluation extends EvaluationComputation {
  id: string; project_id: string; simulation_run_id: string; simulation_result_id: string;
  evaluation_profile_id: string; evaluation_profile_version: number; created_by: string; created_at: string;
}

export interface EvaluationContext { result: SimulationResultEvidence; profile: EvaluationProfile; }
