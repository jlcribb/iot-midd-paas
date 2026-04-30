import { describe, expect, it } from "vitest";
import {
  buildCreatePolicyPayload,
  buildUpdatePolicyPayload,
  createEmptyPolicyFormState,
  defaultParamsText,
  policyToDraft
} from "@/components/control/control-policies.helpers";

describe("control-policies.helpers", () => {
  it("builds create payload from form state", () => {
    const form = createEmptyPolicyFormState();
    form.project_id = "8a954f52-c7b1-4fd6-84ea-a6b897f4d7f2";
    form.variable = "tank_level";

    const payload = buildCreatePolicyPayload(form);

    expect(payload.project_id).toBe("8a954f52-c7b1-4fd6-84ea-a6b897f4d7f2");
    expect(payload.variable).toBe("tank_level");
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
        params_text: "[]",
        context_selector_text: "{}",
        priority: "1",
        enabled: true
      })
    ).toThrow("params must be a JSON object");
  });

  it("creates editable drafts from policies", () => {
    const draft = policyToDraft({
      id: "policy-1",
      project_id: "project-1",
      variable: "tank_level",
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
  });
});
