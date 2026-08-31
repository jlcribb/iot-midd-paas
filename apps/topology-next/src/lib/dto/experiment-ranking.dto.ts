import type { ExperimentEvaluation } from "@/lib/dto/experiment-evaluation.dto";

export const RANKING_ENGINE_VERSION = "experiment-ranking-engine:v1";
export const RANKING_SCHEMA_VERSION = 1 as const;
export const RANKING_SCORE_EPSILON = 0.000001;
export const RANKING_POLICY_VERSION = "ranking-policy:v1";

export type CandidateEligibility = "ELIGIBLE" | "INELIGIBLE" | "UNDETERMINED";
export type EligibilityReason = "CRITICAL_CONSTRAINT_VIOLATION" | "NOT_EVALUABLE" | "INCOMPATIBLE_PROFILE" | "MISSING_EVALUATION" | "UNSUPPORTED_ENGINE_VERSION";
export type ExperimentRankingStatus = "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "NOT_RANKABLE";

export interface RankingPolicy {
  version: typeof RANKING_POLICY_VERSION;
  score_epsilon: number;
  tie_style: "DENSE";
  technical_tie_break: "CANDIDATE_HASH_ASC";
  pareto_role: "ANNOTATION_ONLY";
  eligibility: { completed_statuses: ["COMPLETED", "COMPLETED_WITH_WARNINGS"]; critical_constraint_violation: "INELIGIBLE" };
}

export const DEFAULT_RANKING_POLICY: RankingPolicy = {
  version: RANKING_POLICY_VERSION, score_epsilon: RANKING_SCORE_EPSILON, tie_style: "DENSE",
  technical_tie_break: "CANDIDATE_HASH_ASC", pareto_role: "ANNOTATION_ONLY",
  eligibility: { completed_statuses: ["COMPLETED", "COMPLETED_WITH_WARNINGS"], critical_constraint_violation: "INELIGIBLE" }
};

export interface RankingSourceItem {
  batch_item_id: string; candidate_id: string; candidate_hash: string; item_status: string;
  evaluation_id: string | null; evaluation_hash: string | null; evaluation: ExperimentEvaluation | null;
}
export interface RankingCohort { project_id: string; batch_id: string; batch_hash: string; evaluation_profile_id: string | null; evaluation_profile_version: number | null; items: RankingSourceItem[]; }
export interface RankingItemComputation {
  batch_item_id: string; candidate_id: string; evaluation_id: string | null; eligibility: CandidateEligibility;
  eligibility_reason: EligibilityReason | null; score: number | null; critical_constraint_violation: boolean | null;
  pareto_optimal: boolean | null; dominates_count: number | null; dominated_by_count: number | null;
  rank: number | null; tie_group: number | null; warnings: string[];
}
export interface RankingComputation {
  ranking_hash: string; status: ExperimentRankingStatus; eligible_count: number; ineligible_count: number; unranked_count: number;
  schema_version: 1; ranking_engine_version: string; policy: RankingPolicy; items: RankingItemComputation[];
}
export interface ExperimentRanking extends RankingComputation {
  id: string; project_id: string; batch_id: string; evaluation_profile_id: string | null; evaluation_profile_version: number | null;
  created_by: string; created_at: string; physical_effects_allowed: false;
}
