import { describe, expect, it } from "vitest";
import { checkComparisonCompatibility, compareExperimentEvaluations, computeParetoFront } from "@/lib/comparison/experiment-comparison-engine";
import type { ExperimentEvaluation } from "@/lib/dto/experiment-evaluation.dto";

const project = "11111111-1111-4111-8111-111111111111";
const profile = "22222222-2222-4222-8222-222222222222";
const metric = "33333333-3333-4333-8333-333333333333";
function evaluation(id: string, normalized: number | null, options: Partial<ExperimentEvaluation> = {}): ExperimentEvaluation {
  return { id, project_id: project, simulation_run_id: "44444444-4444-4444-8444-444444444444", simulation_result_id: `${id.slice(0, 8)}-5555-4555-8555-555555555555`,
    evaluation_profile_id: profile, evaluation_profile_version: 1, status: "COMPLETED", score: normalized,
    evaluation_hash: id.replace(/-/g, "").padEnd(64, "a").slice(0, 64), constraint_satisfied_count: 0, constraint_violated_count: 0,
    constraint_unknown_count: 0, critical_constraint_violation: false, schema_version: 1, engine_version: "evaluation-engine:v1", created_by: "operator@example.test", created_at: "2026-08-26T00:00:00Z",
    metrics: [{ metric_id: metric, metric_code: "actuation_count", metric_version: 1, availability_status: normalized === null ? "NOT_AVAILABLE" : "AVAILABLE", availability_reason: null,
      raw_value: normalized === null ? null : 100 - normalized * 100, normalized_value: normalized, weight: 1, weighted_contribution: normalized,
      direction: "MINIMIZE", normalization_method: "MIN_MAX", normalization_config: { schema_version: 1, best: 0, worst: 100 }, constraint_status: "NOT_APPLICABLE", constraint_definition: [] }], ...options };
}

describe("M6.3 pure comparison and Pareto", () => {
  it("requires the same immutable semantic cohort", () => {
    const baseline = evaluation("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", 0.8);
    expect(checkComparisonCompatibility(baseline, evaluation("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", 0.9))).toMatchObject({ compatible: true });
    expect(checkComparisonCompatibility(baseline, evaluation("cccccccc-cccc-4ccc-8ccc-cccccccccccc", 0.9, { evaluation_profile_version: 2 }))).toMatchObject({ compatible: false, reason: "EVALUATION_PROFILE_MISMATCH" });
    expect(checkComparisonCompatibility(baseline, evaluation("dddddddd-dddd-4ddd-8ddd-dddddddddddd", 0.9, { project_id: "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee" }))).toMatchObject({ compatible: false, reason: "PROJECT_MISMATCH" });
  });

  it("uses normalized evidence, epsilon and unavailable coverage without recomputing KPIs", () => {
    const baseline = evaluation("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", 0.8);
    const better = compareExperimentEvaluations(baseline, evaluation("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", 0.9));
    expect(better).toMatchObject({ relation: "BETTER", score_delta: 0.1, candidate_dominates_baseline: true, coverage_ratio: 1 });
    const equivalent = compareExperimentEvaluations(baseline, evaluation("cccccccc-cccc-4ccc-8ccc-cccccccccccc", 0.8000005));
    expect(equivalent.relation).toBe("EQUIVALENT");
    const unavailable = compareExperimentEvaluations(baseline, evaluation("dddddddd-dddd-4ddd-8ddd-dddddddddddd", null, { status: "COMPLETED_WITH_WARNINGS", score: 0 }));
    expect(unavailable).toMatchObject({ relation: "EQUIVALENT", coverage_ratio: 0, comparable_metric_count: 0 });
    expect(unavailable.metrics[0].relation).toBe("UNAVAILABLE");
  });

  it("does not hide a new critical constraint violation behind a performance gain", () => {
    const comparison = compareExperimentEvaluations(evaluation("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", 0.8), evaluation("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", 0.9, { critical_constraint_violation: true }));
    expect(comparison).toMatchObject({ relation: "TRADE_OFF", candidate_dominates_baseline: true });
  });

  it("is directional, canonical, and evaluates Pareto only within a compatible cohort", () => {
    const low = evaluation("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", 0.7);
    const high = evaluation("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", 0.9);
    const repeated = compareExperimentEvaluations(low, high);
    expect(compareExperimentEvaluations(low, high).comparison_hash).toBe(repeated.comparison_hash);
    expect(compareExperimentEvaluations(high, low).comparison_hash).not.toBe(repeated.comparison_hash);
    const front = computeParetoFront([low, high, evaluation("cccccccc-cccc-4ccc-8ccc-cccccccccccc", null, { status: "NOT_EVALUABLE", score: null })]);
    expect(front.pareto_evaluation_ids).toEqual([high.id]);
    expect(front.dominated_evaluation_ids).toEqual([low.id]);
    expect(front.excluded_evaluation_ids).toContain("cccccccc-cccc-4ccc-8ccc-cccccccccccc");
  });
});
