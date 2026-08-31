import type { ExperimentEvaluation } from "@/lib/dto/experiment-evaluation.dto";

export const STRATEGY_RECOMMENDATION_ENGINE_VERSION = "strategy-recommendation-engine:v1";
export const STRATEGY_RECOMMENDATION_SCHEMA_VERSION = 1 as const;
export const RECOMMENDATION_POLICY_VERSION = "recommendation-policy:v1";
export type RecommendationOutcome = "UNIQUE_CANDIDATE" | "AMBIGUOUS" | "NO_ELIGIBLE_CANDIDATE" | "NO_RANKING";
export type StrategyRecommendationStatus = "REVIEW_REQUIRED";
export interface RecommendationPolicy { version: typeof RECOMMENDATION_POLICY_VERSION; selection: ["ELIGIBLE_ONLY","LOWEST_NUMERIC_RANK","PARETO_RESOLVES_ONLY_UNIQUE_TIE","AMBIGUOUS_WITHOUT_TECHNICAL_TIE_BREAK"]; }
export const DEFAULT_RECOMMENDATION_POLICY: RecommendationPolicy = { version: RECOMMENDATION_POLICY_VERSION, selection: ["ELIGIBLE_ONLY","LOWEST_NUMERIC_RANK","PARETO_RESOLVES_ONLY_UNIQUE_TIE","AMBIGUOUS_WITHOUT_TECHNICAL_TIE_BREAK"] };

export interface RecommendationSourceItem { batch_item_id: string; candidate_id: string; candidate_hash: string; candidate_parameters: Record<string, unknown>; evaluation_id: string | null; result_fingerprint: string | null; trace_hash: string | null; evaluation: ExperimentEvaluation | null; eligibility: "ELIGIBLE" | "INELIGIBLE" | "UNDETERMINED"; score: number | null; rank: number | null; pareto_optimal: boolean | null; warnings: string[]; }
export interface RecommendationInput { project_id: string; batch_id: string; batch_hash: string; ranking_id: string; ranking_hash: string; ranking_engine_version: string; items: RecommendationSourceItem[]; }
export interface RecommendationCandidate { candidate_id: string; candidate_hash: string; evaluation_id: string | null; }
export interface RecommendationTradeoff { compared_candidate_hash: string; score_delta: number | null; better_metrics: string[]; worse_metrics: string[]; equivalent_metrics: string[]; unavailable_metrics: string[]; relation: string; }
export interface RecommendationEvidenceSnapshot { selection_basis: { rank: number | null; eligible: boolean; pareto_optimal: boolean | null }; candidate_parameters: Record<string, unknown> | null; constraint_summary: { critical_constraint_violation: boolean | null; violated_count: number | null }; metric_summary: Array<{ code: string; normalized_value: number | null; availability: string }>; warnings: string[]; tradeoffs: RecommendationTradeoff[]; evidence: { batch_hash: string; ranking_hash: string; candidate_hashes: string[]; evaluation_hashes: string[]; result_fingerprints: string[]; trace_hashes: string[] }; }
export interface RecommendationComputation { outcome: RecommendationOutcome; status: StrategyRecommendationStatus; selected: RecommendationCandidate | null; candidate_set: RecommendationCandidate[]; summary: string; warnings: string[]; tradeoffs: RecommendationTradeoff[]; evidence_snapshot: RecommendationEvidenceSnapshot; recommendation_hash: string; recommendation_policy: RecommendationPolicy; recommendation_engine_version: string; schema_version: 1; }
export interface StrategyRecommendation extends RecommendationComputation { id: string; project_id: string; batch_id: string; ranking_id: string; created_by: string; created_at: string; physical_effects_allowed: false; }
