import { describe, expect, it, vi } from "vitest";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { ForbiddenError, ValidationError } from "@/lib/errors/domain-errors";
import type { ControlOperationsRepository } from "@/lib/repositories/control-operations.repository";
import { ControlOperationsRepository as ControlOperationsReadRepository } from "@/lib/repositories/control-operations.repository";
import { ControlOperationsService } from "@/lib/services/control-operations.service";

const PROJECT_ID = "11111111-1111-4111-8111-111111111111";

function actor(projectIds = [PROJECT_ID]): ControlActor {
  return { user_id: "operator-1", display_name: "Operator", role: "operator", all_projects: false, project_ids: projectIds, project_roles: Object.fromEntries(projectIds.map((id) => [id, "operator"])) };
}

function policy(overrides: Record<string, unknown> = {}) {
  return {
    policy_id: "policy-1", project_id: PROJECT_ID, variable: "temperature", enabled: true,
    bound_asset_id: "source-1", source_name: "Sensor", binding_id: "binding-1", binding_enabled: true,
    target_asset_id: "target-1", target_name: "Relay", target_type: "relay_module", target_status: "active",
    target_metadata: { control_capabilities: [{ key: "relay", operations: ["set"] }] }, control_point: "relay", operation: "set",
    updated_at: "2026-08-20T00:00:00.000Z", ...overrides
  };
}

function delivery(overrides: Record<string, unknown> = {}) {
  return {
    delivery_intent_id: "delivery-1", command_id: "command-1", recommendation_id: "recommendation-1", correlation_id: "correlation-1",
    project_id: PROJECT_ID, policy_id: "policy-1", source_asset_id: "source-1", target_asset_id: "target-1", target_name: "Relay",
    operation: "set", intent_status: "retry_pending", retry_count: 1, last_error: "broker unavailable",
    created_at: "2026-08-20T00:00:00.000Z", updated_at: "2026-08-20T00:01:00.000Z", expires_at: "2026-08-20T01:00:00.000Z",
    event_id: "event-1", outbox_status: "pending", ...overrides
  };
}

function service(rows = [policy()], deliveries = [delivery()]) {
  const operationsRepo = {
    findPolicies: vi.fn().mockResolvedValue(rows),
    findRecommendations: vi.fn().mockResolvedValue([{ audit_id: "audit-1", recommendation_id: "recommendation-1", correlation_id: "correlation-1", project_id: PROJECT_ID, policy_id: "policy-1", source_asset_id: "source-1", target_asset_id: "target-1", created_at: "2026-08-20T00:00:00.000Z", summary: "Reduce temperature" }]),
    findDeliveries: vi.fn().mockResolvedValue(deliveries),
    getMetrics: vi.fn().mockResolvedValue({ recommendation_total: 1, last_recommendation_at: "2026-08-20T00:00:00.000Z", last_activity_at: "2026-08-20T00:01:00.000Z", delivery_counts: { retry_pending: 1 } })
  } as unknown as Pick<ControlOperationsRepository, "findPolicies" | "findRecommendations" | "findDeliveries" | "getMetrics">;
  const projectRepo = { findById: vi.fn().mockResolvedValue({ id: PROJECT_ID, name: "Project One", parametric_control_enabled: true }) };
  return { instance: new ControlOperationsService({ operationsRepo, projectRepo }), operationsRepo, projectRepo };
}

describe("ControlOperationsService", () => {
  it("reads canonical root-level audit envelopes as well as legacy nested envelopes", async () => {
    const query = vi.fn().mockResolvedValue({ rows: [] });
    const repository = new ControlOperationsReadRepository({ query } as never);
    await repository.findRecommendations(PROJECT_ID, { limit: 10, offset: 0, policyId: "policy-1" });
    const sql = String(query.mock.calls[0][0]);
    expect(sql).toContain("cambios->'publishable'->'payload'->>'recommendation_id'");
    expect(sql).toContain("cambios->'policy_selection'->>'policy_id'");
    expect(sql).toContain("cambios->'runtime_payload'->>'summary'");
  });

  it("derives actionable, recommendation-only, and misconfigured policy states from persisted bindings", async () => {
    const { instance } = service([
      policy(), policy({ policy_id: "policy-2", binding_id: null, control_point: null, operation: null }),
      policy({ policy_id: "policy-3", target_metadata: { control_capabilities: [{ key: "relay", operations: ["toggle"] }] } })
    ]);
    const result = await instance.listPolicies(actor(), PROJECT_ID);
    expect(result.items.map((item) => item.effective_status)).toEqual(["HEALTHY", "RECOMMENDATION_ONLY", "MISCONFIGURED"]);
    expect(result.items[1].reason_code).toBe("NO_VALID_ACTUATION_TARGET");
    expect(result.items[2].reason_code).toBe("UNSUPPORTED_TARGET_CAPABILITY");
  });

  it("normalizes delivery lifecycle states and exposes attention without claiming a DLQ record", async () => {
    const { instance } = service([policy()], [delivery(), delivery({ delivery_intent_id: "delivery-2", intent_status: "failed_final", outbox_status: "failed" })]);
    const deliveries = await instance.listDeliveries(actor(), PROJECT_ID, { limit: 10, offset: 0 });
    expect(deliveries.items.map((item) => item.intent_status)).toEqual(["RETRYING", "FAILED"]);
    const attention = await instance.listAttention(actor(), PROJECT_ID);
    expect(attention.some((item) => item.category === "DELIVERY" && item.severity === "warning")).toBe(true);
    expect(attention.some((item) => item.category === "OUTBOX" && item.severity === "error")).toBe(true);
  });

  it("projects pending, published, acknowledged, and expired delivery evidence without changing lifecycle semantics", async () => {
    const { instance } = service([policy()], [
      delivery({ delivery_intent_id: "pending", intent_status: "received", outbox_status: "publishing" }),
      delivery({ delivery_intent_id: "published", intent_status: "dispatched", outbox_status: "published" }),
      delivery({ delivery_intent_id: "acknowledged", intent_status: "acknowledged", outbox_status: "published" }),
      delivery({ delivery_intent_id: "expired", intent_status: "expired", outbox_status: null })
    ]);
    const result = await instance.listDeliveries(actor(), PROJECT_ID, { limit: 10, offset: 0 });
    expect(result.items.map((item) => [item.intent_status, item.outbox_status, item.ack_status])).toEqual([
      ["PENDING", "PENDING", null], ["PENDING", "PUBLISHED", null], ["ACKNOWLEDGED", "PUBLISHED", "ACKNOWLEDGED"], ["EXPIRED", null, null]
    ]);
  });

  it("treats cross-project targets as unavailable and permits programmable-node self-targets only", async () => {
    const { instance } = service([
      policy({ policy_id: "foreign-target", target_asset_id: null, target_name: null, target_type: null, target_metadata: null }),
      policy({ policy_id: "forbidden-self", target_asset_id: "source-1" }),
      policy({ policy_id: "programmable-self", target_asset_id: "source-1", target_type: "programmable_node" })
    ]);
    const result = await instance.listBindings(actor(), PROJECT_ID);
    expect(result.items.map((item) => item.reason_code)).toEqual(["TARGET_NOT_FOUND", "SELF_TARGET_NOT_ALLOWED", null]);
    expect(result.items[2].valid).toBe(true);
  });

  it("uses deterministic bounded pagination and links recommendations only within the authorized project", async () => {
    const { instance, operationsRepo } = service();
    const result = await instance.listRecommendations(actor(), PROJECT_ID, { limit: 20, offset: 40, policyId: "policy-1", correlationId: "correlation-1" });
    expect(result).toMatchObject({ limit: 20, offset: 40, items: [{ delivery_intent_id: "delivery-1", command_id: "command-1" }] });
    expect(operationsRepo.findRecommendations).toHaveBeenCalledWith(PROJECT_ID, { limit: 20, offset: 40, policyId: "policy-1", correlationId: "correlation-1" });
    await expect(instance.listDeliveries(actor(), PROJECT_ID, { limit: 101, offset: 0 })).rejects.toBeInstanceOf(ValidationError);
  });

  it("rejects cross-project access before querying the operational read model", async () => {
    const { instance, operationsRepo } = service();
    await expect(instance.getSummary(actor(["project-2"]), PROJECT_ID)).rejects.toBeInstanceOf(ForbiddenError);
    expect(operationsRepo.findPolicies).not.toHaveBeenCalled();
  });

  it("reports project-disabled policies as inactive while preserving configuration", async () => {
    const { instance, projectRepo } = service();
    projectRepo.findById.mockResolvedValue({ id: PROJECT_ID, name: "Project One", parametric_control_enabled: false });
    const result = await instance.listPolicies(actor(), PROJECT_ID);
    expect(result.items[0]).toMatchObject({ configured_status: "ENABLED", effective_status: "INACTIVE", reason_code: "PROJECT_CONTROL_DISABLED" });
  });

  it("returns an empty project summary without inventing activity", async () => {
    const { instance } = service([], []);
    const result = await instance.getSummary(actor(), PROJECT_ID);
    expect(result).toMatchObject({ policy_summary: { total: 0 }, binding_summary: { total: 0 }, attention_summary: { total: 0 } });
  });
});
