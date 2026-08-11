import { describe, expect, it } from "vitest";
import {
  buildPreviewPayload,
  buildCreatePolicyPayload,
  buildUpdatePolicyPayload,
  collectListWarnings,
  createEmptyPolicyFormState,
  defaultParamsText,
  policyToDraft
} from "@/components/control/control-policies.helpers";

describe("control-policies.helpers", () => {
  it("builds create payload from form state", () => {
    const form = createEmptyPolicyFormState();
    form.project_id = "8a954f52-c7b1-4fd6-84ea-a6b897f4d7f2";
    form.variable = "tank_level";
    form.binding_asset_id = "8a954f52-c7b1-4fd6-84ea-a6b897f4d7f3";

    const payload = buildCreatePolicyPayload(form);

    expect(payload.project_id).toBe("8a954f52-c7b1-4fd6-84ea-a6b897f4d7f2");
    expect(payload.variable).toBe("tank_level");
    expect(payload.binding.asset_id).toBe("8a954f52-c7b1-4fd6-84ea-a6b897f4d7f3");
    expect(payload.priority).toBe(0);
    expect(payload.params).toMatchObject({
      actuator_name: "control_output",
      gain: 1
    });
  });

  it("switches default params template per policy type", () => {
    expect(defaultParamsText("proportional")).toContain('"gain": 1');
    expect(defaultParamsText("threshold")).toContain('"tolerance": 2');
  });

  it("rejects invalid JSON objects in update payload", () => {
    expect(() =>
      buildUpdatePolicyPayload({
        binding_asset_id: "",
        params_text: "[]",
        context_selector_text: "{}",
        priority: "1",
        enabled: true,
        preview_context_text: "{}",
        preview_asset_id: ""
      }, "tank_level")
    ).toThrow("params must be a JSON object");
  });

  it("creates editable drafts from policies", () => {
    const draft = policyToDraft({
      id: "policy-1",
      project_id: "project-1",
      variable: "tank_level",
      binding: null,
      context_selector: { sector: "tank_A" },
      policy_type: "proportional",
      params: { gain: 1, actuator_name: "pump", setpoint_value: 70, deadband: 0, min_action: 0, variable_name: "Tank" },
      priority: 10,
      enabled: true,
      version: 3,
      created_at: "2026-01-01T00:00:00.000Z",
      updated_at: "2026-01-02T00:00:00.000Z"
    });

    expect(draft.priority).toBe("10");
    expect(draft.params_text).toContain('"gain": 1');
    expect(draft.context_selector_text).toContain('"sector": "tank_A"');
    expect(draft.preview_context_text).toContain('"sector": "tank_A"');
  });

  it("builds preview payload from a draft", () => {
    const payload = buildPreviewPayload({
      project_id: "8a954f52-c7b1-4fd6-84ea-a6b897f4d7f2",
      variable: "tank_level",
      policy_type: "proportional",
      version: 2,
      draft: {
        binding_asset_id: "8a954f52-c7b1-4fd6-84ea-a6b897f4d7f3",
        params_text: defaultParamsText("proportional"),
        context_selector_text: '{"sector":"tank_A"}',
        priority: "5",
        enabled: true,
        preview_context_text: '{"sector":"tank_A","mode":"night"}',
        preview_asset_id: "8a954f52-c7b1-4fd6-84ea-a6b897f4d7f3"
      }
    });

    expect(payload.context).toMatchObject({ sector: "tank_A", mode: "night" });
    expect(payload.candidate_policy.priority).toBe(5);
    expect(payload.candidate_policy.version).toBe(2);
  });

  it("collects governance warnings for exact-scope enabled conflicts", () => {
    const warnings = collectListWarnings(
      {
        id: "policy-1",
        project_id: "project-1",
        variable: "tank_level",
        context_selector: { sector: "tank_A" },
        policy_type: "proportional",
        params: { gain: 1, actuator_name: "pump", setpoint_value: 70, deadband: 0, min_action: 0, variable_name: "Tank" },
        priority: 5,
        enabled: true,
        version: 3,
        created_at: "2026-01-01T00:00:00.000Z",
        updated_at: "2026-01-02T00:00:00.000Z"
      },
      [
        {
          id: "policy-1",
          project_id: "project-1",
          variable: "tank_level",
          context_selector: { sector: "tank_A" },
          policy_type: "proportional",
          params: { gain: 1, actuator_name: "pump", setpoint_value: 70, deadband: 0, min_action: 0, variable_name: "Tank" },
          priority: 5,
          enabled: true,
          version: 3,
          created_at: "2026-01-01T00:00:00.000Z",
          updated_at: "2026-01-02T00:00:00.000Z"
        },
        {
          id: "policy-2",
          project_id: "project-1",
          variable: "tank_level",
          context_selector: { sector: "tank_A" },
          policy_type: "proportional",
          params: { gain: 1, actuator_name: "pump", setpoint_value: 70, deadband: 0, min_action: 0, variable_name: "Tank" },
          priority: 7,
          enabled: true,
          version: 4,
          created_at: "2026-01-01T00:00:00.000Z",
          updated_at: "2026-01-03T00:00:00.000Z"
        }
      ]
    );

    expect(warnings).toHaveLength(1);
    expect(warnings[0]?.type).toBe("shadowed_by_enabled_policy");
  });
});
