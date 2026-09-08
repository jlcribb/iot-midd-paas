import { describe, expect, it } from "vitest";
import { derivePromotionAssessmentStatus, evaluateAllPromotionGates } from "@/lib/promotion/policy-promotion-engine";

const evidence = { project_id: "p", recommendation_id: "r", recommendation_hash: "a".repeat(64), review_id: "v", review_hash: "b".repeat(64), review_decision: "APPROVE_FOR_FURTHER_TESTING", recommendation_outcome: "UNIQUE_CANDIDATE", candidate_id: "c", candidate_hash: "c".repeat(64), evaluation_id: "e", evaluation_hash: "d".repeat(64), ranking_id: "k", ranking_hash: "e".repeat(64), batch_id: "b", batch_hash: "f".repeat(64), eligibility: "ELIGIBLE", rank: 1, critical_constraint_violation: false, result_fingerprint: "1".repeat(64), trace_hash: "2".repeat(64), trace_schema_version: 1, execution_context: "SIMULATION", physical_effects: false };

describe("M7.1 negative promotion gates", () => {
  it("fails a critical-constraint fixture without inventing inconsistent M6 history", () => {
    const results = evaluateAllPromotionGates({ ...evidence, critical_constraint_violation: true });
    expect(results.find((gate) => gate.gate_code === "GATE_NO_CRITICAL_CONSTRAINT_VIOLATION")).toMatchObject({ status: "FAIL" });
    expect(derivePromotionAssessmentStatus(results)).toBe("FAILED");
  });
});
