import { describe, expect, it } from "vitest";
import { buildControlledPolicyConfigurationHash } from "@/lib/promotion/controlled-policy-version-materializer";
import { buildControlledPolicyApprovalHash, evaluateControlledPolicyValidation } from "@/lib/promotion/controlled-policy-validation-engine";

const configuration = { strategy_type: "proportional" as const, strategy_schema_version: 1, parameters: { setpoint_value: 50, gain: 0.3, deadband: 0, min_action: 0 } };
const input: any = {
  project_id: "11111111-1111-4111-8111-111111111111", candidate_id: "22222222-2222-4222-8222-222222222222", candidate_project_id: "11111111-1111-4111-8111-111111111111",
  policy_version_hash: "a".repeat(64), configuration_snapshot: configuration, configuration_hash: buildControlledPolicyConfigurationHash(configuration), strategy_type: "proportional", strategy_schema_version: 1, version_number: 1,
  proposal_hash: "b".repeat(64), assessment_hash: "c".repeat(64), candidate_hash: "d".repeat(64), provenance_snapshot: { recommendation_hash: "e".repeat(64), review_hash: "f".repeat(64), evaluation_hash: "1".repeat(64), ranking_hash: "2".repeat(64) },
  assessment_status: "PASSED", candidate_immutable: true, operational_binding: false,
};

describe("M7.3 controlled policy validation engine", () => {
  it("passes every required gate deterministically for an immutable simulation candidate", () => {
    const first = evaluateControlledPolicyValidation(input);
    const reordered = evaluateControlledPolicyValidation({ ...input, configuration_snapshot: { ...configuration, parameters: { min_action: 0, gain: 0.3, setpoint_value: 50, deadband: 0 } } });
    expect(first.status).toBe("PASSED");
    expect(first.results).toHaveLength(8);
    expect(first.results.every(gate => gate.status === "PASS")).toBe(true);
    expect(first.validation_hash).toBe(reordered.validation_hash);
  });

  it("blocks error-grade safety gates ahead of ordinary failures", () => {
    const validation = evaluateControlledPolicyValidation({ ...input, configuration_hash: "0".repeat(64), assessment_status: "FAILED", operational_binding: true });
    expect(validation.status).toBe("BLOCKED");
    expect(validation.results.find(gate => gate.gate_code === "GATE_CONFIGURATION_HASH_VALID")?.status).toBe("ERROR");
    expect(validation.results.find(gate => gate.gate_code === "GATE_PROMOTION_ASSESSMENT_PASSED")?.status).toBe("FAIL");
    expect(validation.results.find(gate => gate.gate_code === "GATE_NO_OPERATIONAL_BINDING")?.status).toBe("ERROR");
  });

  it("binds approval identity to the validation decision, rationale, and reviewer", () => {
    const first = buildControlledPolicyApprovalHash({ policy_version_hash: input.policy_version_hash, validation_hash: "3".repeat(64), decision: "REJECT", rationale: " Evidence does not meet the required criterion. ", reviewer_id: "reviewer-a" });
    expect(first).toBe(buildControlledPolicyApprovalHash({ policy_version_hash: input.policy_version_hash, validation_hash: "3".repeat(64), decision: "REJECT", rationale: "Evidence does not meet the required criterion.", reviewer_id: "reviewer-a" }));
    expect(first).not.toBe(buildControlledPolicyApprovalHash({ policy_version_hash: input.policy_version_hash, validation_hash: "3".repeat(64), decision: "REQUEST_REVALIDATION", rationale: "Evidence does not meet the required criterion.", reviewer_id: "reviewer-a" }));
  });
});
