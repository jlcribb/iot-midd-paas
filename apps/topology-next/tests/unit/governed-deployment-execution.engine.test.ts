import { describe, expect, it } from "vitest";
import { buildGovernedDeploymentExecutionHash, buildGovernedDeploymentExecutionResultHash } from "@/lib/promotion/governed-deployment-execution-engine";

describe("M7.6 governed deployment execution hashes", () => {
  it("binds semantic intent, policy, target, and execution contract only", () => {
    const input = { intent_hash: "a".repeat(64), policy_version_hash: "b".repeat(64), target_asset_id: "11111111-1111-4111-8111-111111111111" };
    expect(buildGovernedDeploymentExecutionHash(input)).toBe(buildGovernedDeploymentExecutionHash({ ...input, created_at: "ignored" } as any));
    expect(buildGovernedDeploymentExecutionHash(input)).not.toBe(buildGovernedDeploymentExecutionHash({ ...input, target_asset_id: "22222222-2222-4222-8222-222222222222" }));
  });

  it("binds final delivery and rollback evidence", () => {
    const common = { execution_hash: "c".repeat(64), attempts: [{ attempt_number: 1, result_classification: "SUCCEEDED" }], delivery_result: { status: "STAGED" }, rollback_result: { status: "NOT_REQUIRED" } };
    expect(buildGovernedDeploymentExecutionResultHash(common)).toBe(buildGovernedDeploymentExecutionResultHash({ ...common, id: "ignored" } as any));
    expect(buildGovernedDeploymentExecutionResultHash(common)).not.toBe(buildGovernedDeploymentExecutionResultHash({ ...common, rollback_result: { status: "SUCCEEDED" } }));
  });
});
