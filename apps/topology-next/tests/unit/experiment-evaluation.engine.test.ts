import { describe, expect, it } from "vitest";
import type { EvaluationContext } from "@/lib/dto/experiment-evaluation.dto";
import { evaluateExperiment } from "@/lib/evaluation/experiment-evaluator";
import { normalizeMetric } from "@/lib/evaluation/normalization";

const projectId = "11111111-1111-4111-8111-111111111111";
const metricId = "22222222-2222-4222-8222-222222222222";
const profileId = "33333333-3333-4333-8333-333333333333";

function metric(direction: "MINIMIZE" | "MAXIMIZE" | "TARGET" | "RANGE", method: "MIN_MAX" | "TARGET_DISTANCE" | "RANGE_DISTANCE", config: Record<string, unknown>, code = "actuation_count") {
  return { id: metricId, code, version: 1, name: code, description: "", unit: "count", direction,
    normalization_method: method, normalization_config: { schema_version: 1, ...config }, weightable: true, active: true, created_at: "2026-08-26T00:00:00.000Z" };
}

function context(overrides: Partial<EvaluationContext> = {}): EvaluationContext {
  const profile = {
    id: profileId, project_id: projectId, code: "actuation_profile", version: 1, name: "Actuation profile", description: "",
    status: "ACTIVE" as const, schema_version: 1 as const, metadata: {}, created_by: "operator@example.test", created_at: "2026-08-26T00:00:00.000Z",
    metrics: [{ metric: metric("MINIMIZE", "MIN_MAX", { best: 0, worst: 100 }), weight: 1, required: true }], constraints: []
  };
  const result = { id: "44444444-4444-4444-8444-444444444444", project_id: projectId, session_id: "55555555-5555-4555-8555-555555555555",
    run_id: "66666666-6666-4666-8666-666666666666", result_fingerprint: "a".repeat(64), processed_events: 3,
    actionable_recommendation_count: 10, failed_domain_event_count: 0 };
  return { result, profile, ...overrides };
}

describe("M6.2 deterministic normalization", () => {
  it("normalizes all supported directions using explicit bounds and clipping", () => {
    expect(normalizeMetric(metric("MINIMIZE", "MIN_MAX", { best: 0, worst: 100 }), 0)).toBe(1);
    expect(normalizeMetric(metric("MINIMIZE", "MIN_MAX", { best: 0, worst: 100 }), 50)).toBe(0.5);
    expect(normalizeMetric(metric("MINIMIZE", "MIN_MAX", { best: 0, worst: 100 }), 150)).toBe(0);
    expect(normalizeMetric(metric("MAXIMIZE", "MIN_MAX", { best: 100, worst: 0 }), 50)).toBe(0.5);
    expect(normalizeMetric(metric("TARGET", "TARGET_DISTANCE", { target: 60, tolerance: 5, worst_distance: 30 }), 65)).toBe(1);
    expect(normalizeMetric(metric("TARGET", "TARGET_DISTANCE", { target: 60, tolerance: 5, worst_distance: 30 }), 90)).toBe(0);
    expect(normalizeMetric(metric("RANGE", "RANGE_DISTANCE", { min: 20, max: 90, soft_margin: 10 }), 90)).toBe(1);
    expect(normalizeMetric(metric("RANGE", "RANGE_DISTANCE", { min: 20, max: 90, soft_margin: 10 }), 95)).toBe(0.5);
  });

  it("keeps performance score independent from a violated critical constraint", () => {
    const source = context();
    source.profile.constraints = [{ metric_id: metricId, kind: "MAXIMUM", lower_bound: null, upper_bound: 5, critical: true }];
    const evaluation = evaluateExperiment(source);
    expect(evaluation.status).toBe("COMPLETED");
    expect(evaluation.score).toBe(0.9);
    expect(evaluation.constraint_violated_count).toBe(1);
    expect(evaluation.critical_constraint_violation).toBe(true);
  });

  it("does not convert unavailable required KPIs into zero", () => {
    const source = context();
    source.profile.metrics = [{ metric: metric("MINIMIZE", "MIN_MAX", { best: 0, worst: 100 }, "tracking_error"), weight: 1, required: true }];
    const evaluation = evaluateExperiment(source);
    expect(evaluation.status).toBe("NOT_EVALUABLE");
    expect(evaluation.score).toBeNull();
    expect(evaluation.metrics[0]).toMatchObject({ availability_status: "NOT_AVAILABLE", raw_value: null, normalized_value: null });
  });

  it("is canonical and sensitive only to semantic evaluation input", () => {
    const first = evaluateExperiment(context());
    const repeated = evaluateExperiment(context());
    expect(repeated).toMatchObject({ evaluation_hash: first.evaluation_hash, score: first.score, metrics: first.metrics });
    const changedRaw = context();
    changedRaw.result.actionable_recommendation_count = 11;
    expect(evaluateExperiment(changedRaw).evaluation_hash).not.toBe(first.evaluation_hash);
    const changedProfile = context();
    changedProfile.profile.id = "77777777-7777-4777-8777-777777777777";
    expect(evaluateExperiment(changedProfile).evaluation_hash).not.toBe(first.evaluation_hash);
    const changedMetricVersion = context();
    changedMetricVersion.profile.metrics[0].metric.version = 2;
    expect(evaluateExperiment(changedMetricVersion).evaluation_hash).not.toBe(first.evaluation_hash);
    const reorderedConfig = context();
    reorderedConfig.profile.metrics[0].metric.normalization_config = { worst: 100, schema_version: 1, best: 0 };
    expect(evaluateExperiment(reorderedConfig).evaluation_hash).toBe(first.evaluation_hash);
  });
});
