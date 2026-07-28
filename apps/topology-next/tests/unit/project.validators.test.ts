import { describe, expect, it } from "vitest";
import { createProjectSchema, updateProjectSchema } from "@/lib/validators/project.schemas";

describe("Project validators", () => {
  it("defaults parametric_control_enabled to false on create", () => {
    const payload = createProjectSchema.parse({
      name: "Proyecto Demo",
      description: null,
      status: "active",
      metadata: {}
    });

    expect(payload.parametric_control_enabled).toBe(false);
  });

  it("preserves an explicit false value on create", () => {
    const payload = createProjectSchema.parse({
      name: "Proyecto Demo",
      description: null,
      status: "active",
      parametric_control_enabled: false,
      metadata: {}
    });

    expect(payload.parametric_control_enabled).toBe(false);
  });

  it("accepts explicit parametric_control_enabled updates", () => {
    const payload = updateProjectSchema.parse({
      parametric_control_enabled: true
    });

    expect(payload.parametric_control_enabled).toBe(true);
  });

  it("accepts explicit false updates", () => {
    const payload = updateProjectSchema.parse({
      parametric_control_enabled: false
    });

    expect(payload.parametric_control_enabled).toBe(false);
  });

  it("rejects non boolean control flag values", () => {
    expect(() =>
      createProjectSchema.parse({
        name: "Proyecto Demo",
        description: null,
        status: "active",
        parametric_control_enabled: "true",
        metadata: {}
      })
    ).toThrow();
  });

  it("rejects empty update payloads", () => {
    expect(() => updateProjectSchema.parse({})).toThrow("Empty update payload is not allowed");
  });
});
