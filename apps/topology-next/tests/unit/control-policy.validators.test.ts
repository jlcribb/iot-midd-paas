import { describe, expect, it } from "vitest";
import {
  createControlPolicySchema,
  previewControlPolicySchema,
  updateControlPolicySchema
} from "@/lib/validators/control-policy.schemas";

describe("control-policy.schemas", () => {
  it("accepts proportional policies with required params", () => {
    const parsed = createControlPolicySchema.parse({
      project_id: "8a954f52-c7b1-4fd6-84ea-a6b897f4d7f2",
      variable: "tank_level",
      policy_type: "proportional",
      context_selector: { sector: "tank_A" },
      params: {
        variable_name: "Tank Level",
        actuator_name: "control_output",
        setpoint_value: 70,
        gain: 1,
        deadband: 0,
        min_action: 0
      },
      priority: 10,
      enabled: true
    });

    expect(parsed.policy_type).toBe("proportional");
    expect(parsed.priority).toBe(10);
  });

  it("rejects threshold policies without tolerance", () => {
    expect(() =>
      createControlPolicySchema.parse({
        project_id: "8a954f52-c7b1-4fd6-84ea-a6b897f4d7f2",
        variable: "tank_level",
        policy_type: "threshold",
        context_selector: {},
        params: {
          variable_name: "Tank Level",
          actuator_name: "control_output",
          setpoint_value: 70,
          increase_step: 1.5,
          decrease_step: 1.5,
          hold_signal: 0
        },
        priority: 0,
        enabled: true
      })
    ).toThrow();
  });

  it("rejects empty patch payloads", () => {
    expect(() => updateControlPolicySchema.parse({})).toThrow("Empty update payload is not allowed");
  });

  it("rejects proportional params with invalid operational bounds", () => {
    expect(() =>
      createControlPolicySchema.parse({
        project_id: "8a954f52-c7b1-4fd6-84ea-a6b897f4d7f2",
        variable: "tank_level",
        policy_type: "proportional",
        context_selector: {},
        params: {
          variable_name: "Tank Level",
          actuator_name: "control_output",
          setpoint_value: 70,
          gain: 0,
          deadband: -1,
          min_action: 5,
          max_action: 4
        },
        priority: 0,
        enabled: true
      })
    ).toThrow();
  });

  it("rejects threshold params with negative steps or tolerance", () => {
    expect(() =>
      createControlPolicySchema.parse({
        project_id: "8a954f52-c7b1-4fd6-84ea-a6b897f4d7f2",
        variable: "tank_level",
        policy_type: "threshold",
        context_selector: {},
        params: {
          variable_name: "Tank Level",
          actuator_name: "control_output",
          setpoint_value: 70,
          tolerance: -1,
          increase_step: -0.5,
          decrease_step: 1.5,
          hold_signal: 0
        },
        priority: 0,
        enabled: true
      })
    ).toThrow();
  });

  it("rejects preview requests where candidate scope diverges from outer scope", () => {
    expect(() =>
      previewControlPolicySchema.parse({
        project_id: "8a954f52-c7b1-4fd6-84ea-a6b897f4d7f2",
        variable: "tank_level",
        context: {},
        candidate_policy: {
          project_id: "6059884a-252e-4f87-a072-dd8d338a0bc2",
          variable: "ph",
          policy_type: "proportional",
          context_selector: {},
          params: {
            variable_name: "Tank Level",
            actuator_name: "control_output",
            setpoint_value: 70,
            gain: 1,
            deadband: 0,
            min_action: 0
          },
          priority: 0,
          enabled: true
        }
      })
    ).toThrow();
  });
});
