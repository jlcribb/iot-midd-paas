import { describe, expect, it } from "vitest";
import {
  buildPreviewResponse,
  detectPolicyConflicts,
  matchesRequiredContext,
  stableJsonStringify
} from "@/lib/utils/control-policy-governance";

describe("control-policy-governance", () => {
  it("normalizes object key order when comparing context selectors", () => {
    expect(stableJsonStringify({ b: 2, a: 1 })).toBe(stableJsonStringify({ a: 1, b: 2 }));
  });

  it("matches only when required context is contained in actual context", () => {
    expect(matchesRequiredContext({ sector: "tank_A" }, { sector: "tank_A", mode: "night" })).toBe(true);
    expect(matchesRequiredContext({ sector: "tank_A" }, { sector: "tank_B", mode: "night" })).toBe(false);
  });

  it("detects exact-scope selection ties as blocking conflicts", () => {
    const conflicts = detectPolicyConflicts(
      {
        id: "policy-new",
        project_id: "project-1",
        variable: "tank_level",
        policy_type: "proportional",
        context_selector: { sector: "tank_A" },
        params: { gain: 1, actuator_name: "pump", setpoint_value: 70, deadband: 0, min_action: 0, variable_name: "Tank" },
        priority: 10,
        enabled: true,
        version: 4
      },
      [
        {
          id: "policy-1",
          project_id: "project-1",
          variable: "tank_level",
          context_selector: { sector: "tank_A" },
          policy_type: "proportional",
          params: { gain: 1, actuator_name: "pump", setpoint_value: 70, deadband: 0, min_action: 0, variable_name: "Tank" },
          priority: 10,
          enabled: true,
          version: 4,
          created_at: "2026-01-01T00:00:00.000Z",
          updated_at: "2026-01-02T00:00:00.000Z"
        }
      ]
    );

    expect(conflicts).toHaveLength(1);
    expect(conflicts[0]?.type).toBe("selection_tie");
    expect(conflicts[0]?.severity).toBe("error");
  });

  it("builds a preview showing the hypothetical winning policy", () => {
    const preview = buildPreviewResponse({
      project_id: "project-1",
      variable: "tank_level",
      context: { sector: "tank_A", mode: "night" },
      existingPolicies: [
        {
          id: "policy-1",
          project_id: "project-1",
          variable: "tank_level",
          context_selector: {},
          policy_type: "proportional",
          params: { gain: 1, actuator_name: "pump", setpoint_value: 70, deadband: 0, min_action: 0, variable_name: "Tank" },
          priority: 1,
          enabled: true,
          version: 1,
          created_at: "2026-01-01T00:00:00.000Z",
          updated_at: "2026-01-01T00:00:00.000Z"
        },
        {
          id: "policy-2",
          project_id: "project-1",
          variable: "tank_level",
          context_selector: { sector: "tank_A" },
          policy_type: "proportional",
          params: { gain: 2, actuator_name: "pump", setpoint_value: 70, deadband: 0, min_action: 0, variable_name: "Tank" },
          priority: 5,
          enabled: true,
          version: 2,
          created_at: "2026-01-01T00:00:00.000Z",
          updated_at: "2026-01-02T00:00:00.000Z"
        }
      ],
      candidate: {
        project_id: "project-1",
        variable: "tank_level",
        policy_type: "proportional",
        context_selector: { sector: "tank_A", mode: "night" },
        params: { gain: 3, actuator_name: "pump", setpoint_value: 70, deadband: 0, min_action: 0, variable_name: "Tank" },
        priority: 3,
        enabled: true,
        version: 1
      }
    });

    expect(preview.current_selected_policy?.id).toBe("policy-2");
    expect(preview.hypothetical_selected_policy?.id).toBe("preview-candidate");
    expect(preview.candidate_would_be_selected).toBe(true);
  });
});
