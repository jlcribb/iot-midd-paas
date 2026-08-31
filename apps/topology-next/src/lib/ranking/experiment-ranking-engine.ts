import { checkComparisonCompatibility, computeParetoFront } from "@/lib/comparison/experiment-comparison-engine";
import type { ExperimentEvaluation } from "@/lib/dto/experiment-evaluation.dto";
import { DEFAULT_RANKING_POLICY, RANKING_ENGINE_VERSION, RANKING_SCHEMA_VERSION, type CandidateEligibility, type EligibilityReason, type RankingCohort, type RankingComputation, type RankingItemComputation, type RankingPolicy, type RankingSourceItem } from "@/lib/dto/experiment-ranking.dto";
import { sha256Canonical } from "@/lib/simulation/canonical";

function technicallyEvaluable(evaluation: ExperimentEvaluation | null): evaluation is ExperimentEvaluation {
  return evaluation !== null && (evaluation.status === "COMPLETED" || evaluation.status === "COMPLETED_WITH_WARNINGS") && evaluation.score !== null;
}

export function determineEligibility(item: RankingSourceItem, compatible: boolean): { eligibility: CandidateEligibility; reason: EligibilityReason | null; warnings: string[] } {
  if (!item.evaluation) return { eligibility: "UNDETERMINED", reason: "MISSING_EVALUATION", warnings: [] };
  if (!technicallyEvaluable(item.evaluation)) return { eligibility: "UNDETERMINED", reason: "NOT_EVALUABLE", warnings: [] };
  if (!compatible) return { eligibility: "UNDETERMINED", reason: "INCOMPATIBLE_PROFILE", warnings: [] };
  if (item.evaluation.critical_constraint_violation) return { eligibility: "INELIGIBLE", reason: "CRITICAL_CONSTRAINT_VIOLATION", warnings: [] };
  return { eligibility: "ELIGIBLE", reason: null, warnings: item.evaluation.constraint_violated_count > 0 ? ["NON_CRITICAL_CONSTRAINT_VIOLATION"] : [] };
}

/** Chooses one reproducible semantic cohort; incompatible items remain visible but unranked. */
export function buildRankingCohort(items: RankingSourceItem[]): { compatibleIds: Set<string>; evaluable: RankingSourceItem[] } {
  const evaluable = items.filter((item) => technicallyEvaluable(item.evaluation)).sort((left, right) => left.candidate_hash.localeCompare(right.candidate_hash));
  const anchor = evaluable[0]?.evaluation;
  if (!anchor) return { compatibleIds: new Set(), evaluable };
  return { compatibleIds: new Set(evaluable.filter((item) => checkComparisonCompatibility(anchor, item.evaluation as ExperimentEvaluation).compatible).map((item) => item.batch_item_id)), evaluable };
}

export function compareRankingScores(left: RankingItemComputation & { candidate_hash: string }, right: RankingItemComputation & { candidate_hash: string }): number {
  if ((right.score as number) !== (left.score as number)) return (right.score as number) - (left.score as number);
  return left.candidate_hash.localeCompare(right.candidate_hash);
}

export function assignDenseRanks(items: Array<RankingItemComputation & { candidate_hash: string }>, epsilon: number): void {
  let rank = 0, tieGroup = 0, previous: number | null = null;
  for (const item of items) {
    if (previous === null || Math.abs((item.score as number) - previous) > epsilon) { rank += 1; tieGroup += 1; previous = item.score as number; }
    item.rank = rank; item.tie_group = tieGroup;
  }
}

export function computeTieGroups(items: Array<RankingItemComputation & { candidate_hash: string }>, epsilon: number): void { assignDenseRanks(items, epsilon); }

export function buildRankingIdentity(cohort: RankingCohort, policy: RankingPolicy = DEFAULT_RANKING_POLICY): string {
  const items = [...cohort.items].map((item) => ({ candidate_hash: item.candidate_hash, item_status: item.item_status, evaluation_hash: item.evaluation_hash, evaluation_status: item.evaluation?.status ?? null, persisted_score: item.evaluation?.score ?? null, critical_constraint_violation: item.evaluation?.critical_constraint_violation ?? null })).sort((left, right) => left.candidate_hash.localeCompare(right.candidate_hash));
  return sha256Canonical({ schema_version: RANKING_SCHEMA_VERSION, ranking_engine_version: RANKING_ENGINE_VERSION, batch: { project_id: cohort.project_id, batch_id: cohort.batch_id, batch_hash: cohort.batch_hash, evaluation_profile_id: cohort.evaluation_profile_id, evaluation_profile_version: cohort.evaluation_profile_version }, items, eligibility_policy: policy.eligibility, ranking_policy_version: policy.version, score_epsilon: policy.score_epsilon, pareto_engine_version: "experiment-comparison-engine:v1" });
}

export function rankExperimentBatch(cohort: RankingCohort, policy: RankingPolicy = DEFAULT_RANKING_POLICY): RankingComputation {
  const { compatibleIds, evaluable } = buildRankingCohort(cohort.items);
  const paretoInputs = evaluable.filter((item) => compatibleIds.has(item.batch_item_id));
  const pareto = computeParetoFront(paretoInputs.map((item) => item.evaluation as ExperimentEvaluation));
  const dominates = new Map<string, number>(); const dominatedBy = new Map<string, number>();
  for (const relation of pareto.dominance_relations) { dominates.set(relation.dominator_evaluation_id, (dominates.get(relation.dominator_evaluation_id) ?? 0) + 1); dominatedBy.set(relation.dominated_evaluation_id, (dominatedBy.get(relation.dominated_evaluation_id) ?? 0) + 1); }
  const items = cohort.items.map((source) => {
    const eligibility = determineEligibility(source, compatibleIds.has(source.batch_item_id)); const evaluation = source.evaluation;
    const paretoComputable = !!evaluation && compatibleIds.has(source.batch_item_id) && technicallyEvaluable(evaluation);
    return { batch_item_id: source.batch_item_id, candidate_id: source.candidate_id, evaluation_id: source.evaluation_id, eligibility: eligibility.eligibility, eligibility_reason: eligibility.reason, score: evaluation?.score ?? null, critical_constraint_violation: evaluation?.critical_constraint_violation ?? null, pareto_optimal: paretoComputable ? pareto.pareto_evaluation_ids.includes(evaluation!.id) : null, dominates_count: paretoComputable ? (dominates.get(evaluation!.id) ?? 0) : null, dominated_by_count: paretoComputable ? (dominatedBy.get(evaluation!.id) ?? 0) : null, rank: null, tie_group: null, warnings: eligibility.warnings, candidate_hash: source.candidate_hash };
  });
  const ranked = items.filter((item) => item.eligibility === "ELIGIBLE" && item.score !== null).sort(compareRankingScores);
  assignDenseRanks(ranked, policy.score_epsilon);
  const publicItems = items.map(({ candidate_hash: _candidateHash, ...item }) => item);
  const eligible_count = ranked.length, ineligible_count = publicItems.filter((item) => item.eligibility === "INELIGIBLE").length, unranked_count = publicItems.length - eligible_count;
  return { ranking_hash: buildRankingIdentity(cohort, policy), status: eligible_count === 0 ? "NOT_RANKABLE" : unranked_count > 0 ? "COMPLETED_WITH_WARNINGS" : "COMPLETED", eligible_count, ineligible_count, unranked_count, schema_version: RANKING_SCHEMA_VERSION, ranking_engine_version: RANKING_ENGINE_VERSION, policy, items: publicItems };
}
