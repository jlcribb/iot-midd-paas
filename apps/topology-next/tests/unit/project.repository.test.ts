import { describe, expect, it } from "vitest";
import { buildProjectWritePayload, mapProject } from "@/lib/repositories/project.repository";

describe("ProjectRepository helpers", () => {
  it("maps database rows into project DTOs with control flag", () => {
    const project = mapProject({
      id: "project-1",
      name: "Proyecto Demo",
      description: null,
      status: "active",
      parametric_control_enabled: true,
      metadata: { area: "north" },
      created_at: "2026-01-01T00:00:00.000Z",
      updated_at: "2026-01-02T00:00:00.000Z"
    });

    expect(project.parametric_control_enabled).toBe(true);
    expect(project.metadata).toMatchObject({ area: "north" });
  });

  it("defaults control flag to false when the database row omits the column", () => {
    const project = mapProject({
      id: "project-2",
      name: "Proyecto Sin Flag",
      description: null,
      status: "draft",
      metadata: {},
      created_at: "2026-01-01T00:00:00.000Z",
      updated_at: "2026-01-02T00:00:00.000Z"
    });

    expect(project.parametric_control_enabled).toBe(false);
  });

  it("serializes control flag and metadata for writes", () => {
    const payload = buildProjectWritePayload({
      name: "Proyecto Demo",
      description: null,
      status: "active",
      parametric_control_enabled: true,
      metadata: { area: "north" }
    });

    expect(payload).toEqual({
      name: "Proyecto Demo",
      description: null,
      status: "active",
      parametric_control_enabled: true,
      metadata: '{"area":"north"}'
    });
  });

  it("preserves explicit false when serializing project writes", () => {
    const payload = buildProjectWritePayload({
      name: "Proyecto Demo",
      parametric_control_enabled: false,
      metadata: {}
    });

    expect(payload).toMatchObject({
      name: "Proyecto Demo",
      parametric_control_enabled: false,
      metadata: "{}"
    });
  });

  it("omits the control flag when the update payload does not define it", () => {
    const payload = buildProjectWritePayload({
      status: "active"
    });

    expect(payload).toEqual({
      status: "active"
    });
    expect(payload).not.toHaveProperty("parametric_control_enabled");
  });
});
