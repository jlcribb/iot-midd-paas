import { describe, expect, it } from "vitest";
import { buildControlPolicyUpdatePayload, mapControlPolicy } from "@/lib/repositories/control-policy.repository";

describe("ControlPolicyRepository helpers", () => {
  it("maps database rows into control policy DTOs", () => {
    const policy = mapControlPolicy({
      id: "policy-1",
      project_id: "project-1",
      variable: "tank_level",
      context_selector: { sector: "tank_A" },
      policy_type: "proportional",
      params: { gain: 1 },
      priority: "10",
      enabled: true,
      version: "2",
      created_at: "2026-01-01T00:00:00.000Z",
      updated_at: "2026-01-02T00:00:00.000Z"
    });

    expect(policy.priority).toBe(10);
    expect(policy.version).toBe(2);
    expect(policy.context_selector).toMatchObject({ sector: "tank_A" });
  });

  it("serializes JSON payloads for updates", () => {
    const payload = buildControlPolicyUpdatePayload({
      context_selector: { sector: "tank_B" },
      params: { gain: 2 },
      priority: 4,
      enabled: false,
      version: 5
    });

    expect(payload).toEqual({
      context_selector: '{"sector":"tank_B"}',
      params: '{"gain":2}',
      priority: 4,
      enabled: false,
      version: 5
    });
  });
});
