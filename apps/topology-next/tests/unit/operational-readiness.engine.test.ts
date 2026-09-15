import { describe, expect, it } from "vitest";
import { buildControlledPolicyConfigurationHash, buildControlledPolicyVersionHash } from "@/lib/promotion/controlled-policy-version-materializer";
import { buildControlledPolicyApprovalHash } from "@/lib/promotion/controlled-policy-validation-engine";
import { buildControlledDeploymentPreparationHash, evaluateOperationalReadiness } from "@/lib/promotion/operational-readiness-engine";

const projectId = "11111111-1111-4111-8111-111111111111", candidateId = "22222222-2222-4222-8222-222222222222", targetAssetId = "33333333-3333-4333-8333-333333333333";
const configuration = { strategy_type: "proportional" as const, strategy_schema_version: 1, parameters: { setpoint_value: 50, gain: 0.3 } };
const configurationHash = buildControlledPolicyConfigurationHash(configuration);
const policyVersionHash = buildControlledPolicyVersionHash({ project_id: projectId, configuration_hash: configurationHash, proposal_hash: "a".repeat(64), assessment_hash: "b".repeat(64), candidate_hash: "c".repeat(64), strategy_type: "proportional", version_number: 1 });
const validationHash = "d".repeat(64), approvalHash = buildControlledPolicyApprovalHash({ policy_version_hash: policyVersionHash, validation_hash: validationHash, decision: "APPROVE_FOR_CONTROLLED_DEPLOYMENT_PREPARATION", rationale: "Approval for non-executing preparation evidence.", reviewer_id: "reviewer" });
const preparationHash = buildControlledDeploymentPreparationHash({ project_id: projectId, policy_version_candidate_id: candidateId, policy_version_hash: policyVersionHash, validation_hash: validationHash, approval_hash: approvalHash, target_asset_id: targetAssetId });
const input: any = { project_id: projectId, policy_version_candidate_id: candidateId, target_asset_id: targetAssetId, policy_version_hash: policyVersionHash, validation_id: "44444444-4444-4444-8444-444444444444", validation_hash: validationHash, approval_id: "55555555-5555-4555-8555-555555555555", approval_hash: approvalHash, approval_decision: "APPROVE_FOR_CONTROLLED_DEPLOYMENT_PREPARATION", validation_status: "PASSED", approval_rationale: "Approval for non-executing preparation evidence.", reviewer_id: "reviewer", configuration_snapshot: configuration, configuration_hash: configurationHash, strategy_type: "proportional", strategy_schema_version: 1, version_number: 1, proposal_hash: "a".repeat(64), assessment_hash: "b".repeat(64), candidate_hash: "c".repeat(64), provenance_snapshot: { recommendation_hash: "e".repeat(64), review_hash: "f".repeat(64), evaluation_hash: "1".repeat(64), ranking_hash: "2".repeat(64) }, stored_preparation_hash: preparationHash, target_project_id: projectId, target_status: "active", target_asset_type: "programmable_node", target_metadata: { control_readiness: { supported_strategy_types: ["proportional"], supported_strategy_schema_versions: [1], runtime_capabilities: ["strategy_evaluator","input_signal","output_channel","policy_schema"], security_boundary: { governed_control: true }, observability: { telemetry: true, runtime_status: true, control_output: true, audit_path: true } } }, has_conflicting_active_binding: false, rollback_status: "NO_PRIOR_POLICY", development_fallback_enabled: false, no_deployment_executed: true };

describe("M7.4 operational readiness engine", () => {
  it("passes all twelve deterministic gates for a declared non-physical target", () => {
    const first = evaluateOperationalReadiness(input), replay = evaluateOperationalReadiness({ ...input, target_metadata: JSON.parse(JSON.stringify(input.target_metadata)) });
    expect(first.status).toBe("PASSED"); expect(first.results).toHaveLength(12); expect(first.results.every(gate => gate.status === "PASS")).toBe(true); expect(first.readiness_hash).toBe(replay.readiness_hash);
  });
  it("gives blocked evidence precedence over ordinary readiness failures", () => {
    const readiness = evaluateOperationalReadiness({ ...input, target_metadata: { control_readiness: { ...input.target_metadata.control_readiness, runtime_capabilities: [] } }, has_conflicting_active_binding: true, development_fallback_enabled: true });
    expect(readiness.status).toBe("BLOCKED"); expect(readiness.results.find(gate => gate.gate_code === "GATE_REQUIRED_RUNTIME_CAPABILITIES_DECLARED")?.status).toBe("FAIL"); expect(readiness.results.find(gate => gate.gate_code === "GATE_NO_CONFLICTING_ACTIVE_BINDING")?.status).toBe("ERROR");
  });
  it("blocks broken approval and policy identity instead of treating them as ordinary readiness gaps", () => {
    const readiness = evaluateOperationalReadiness({ ...input, approval_decision: "REJECT", configuration_hash: "0".repeat(64) });
    expect(readiness.status).toBe("BLOCKED"); expect(readiness.results.find(gate => gate.gate_code === "GATE_M7_3_APPROVAL_VALID")?.status).toBe("ERROR"); expect(readiness.results.find(gate => gate.gate_code === "GATE_POLICY_VERSION_IDENTITY_VALID")?.status).toBe("ERROR");
  });
  it("classifies unmet target declarations as failed and safety-boundary violations as blocked", () => {
    const cases: Array<[string, any, "FAILED" | "BLOCKED"]> = [
      ["missing topology", { target_status: "inactive" }, "FAILED"],
      ["incompatible target", { target_metadata: { control_readiness: { ...input.target_metadata.control_readiness, supported_strategy_types: ["threshold"] } } }, "FAILED"],
      ["missing rollback declaration", { rollback_status: "MISSING" }, "FAILED"],
      ["missing observability declaration", { target_metadata: { control_readiness: { ...input.target_metadata.control_readiness, observability: {} } } }, "FAILED"],
      ["security fallback enabled", { development_fallback_enabled: true }, "BLOCKED"],
      ["operational side effect detected", { no_deployment_executed: false }, "BLOCKED"],
    ];
    for (const [, change, expected] of cases) expect(evaluateOperationalReadiness({ ...input, ...change }).status).toBe(expected);
  });
});
