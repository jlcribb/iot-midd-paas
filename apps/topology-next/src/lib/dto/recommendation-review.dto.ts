import type { RecommendationOutcome, StrategyRecommendationStatus } from "@/lib/dto/strategy-recommendation.dto";

export const HUMAN_REVIEW_POLICY_VERSION = "human-review-policy:v1";
export const RECOMMENDATION_REVIEW_SCHEMA_VERSION = 1 as const;
export type HumanReviewDecision = "APPROVE_FOR_FURTHER_TESTING" | "REJECT" | "REQUEST_MORE_EXPERIMENTS";
export const HUMAN_REVIEW_DECISIONS: HumanReviewDecision[] = ["APPROVE_FOR_FURTHER_TESTING", "REJECT", "REQUEST_MORE_EXPERIMENTS"];
export interface HumanReviewPolicy { version: typeof HUMAN_REVIEW_POLICY_VERSION; reviewable_statuses: StrategyRecommendationStatus[]; one_authoritative_review: true; decision_matrix: Record<RecommendationOutcome, HumanReviewDecision[]>; }
export const DEFAULT_HUMAN_REVIEW_POLICY: HumanReviewPolicy = { version: HUMAN_REVIEW_POLICY_VERSION, reviewable_statuses: ["REVIEW_REQUIRED"], one_authoritative_review: true, decision_matrix: { UNIQUE_CANDIDATE: ["APPROVE_FOR_FURTHER_TESTING", "REQUEST_MORE_EXPERIMENTS", "REJECT"], AMBIGUOUS: ["REQUEST_MORE_EXPERIMENTS", "REJECT"], NO_ELIGIBLE_CANDIDATE: ["REQUEST_MORE_EXPERIMENTS", "REJECT"], NO_RANKING: ["REQUEST_MORE_EXPERIMENTS", "REJECT"] } };
export interface ReviewableRecommendation { id: string; project_id: string; recommendation_hash: string; outcome: RecommendationOutcome; status: StrategyRecommendationStatus; }
export interface RecommendationReviewInput { decision: HumanReviewDecision; rationale: string; }
export interface RecommendationReviewComputation { decision: HumanReviewDecision; rationale: string; recommendation_hash: string; review_hash: string; review_policy: HumanReviewPolicy; schema_version: 1; }
export interface RecommendationReview extends RecommendationReviewComputation { id: string; project_id: string; recommendation_id: string; reviewer_id: string; created_at: string; physical_effects_allowed: false; }
