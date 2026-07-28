import { describe, expect, it, vi } from "vitest";
import { ProjectService } from "@/lib/services/project.service";
import type { IProjectRepository } from "@/lib/repositories/contracts";

describe("ProjectService", () => {
  it("creates a project with valid payload", async () => {
    const create = vi.fn().mockResolvedValue({
      id: "project-1",
      name: "Proyecto Demo",
      description: null,
      status: "active",
      parametric_control_enabled: false,
      metadata: {},
      created_at: "2026-01-01T00:00:00.000Z",
      updated_at: "2026-01-01T00:00:00.000Z"
    });

    const projectRepo: IProjectRepository = {
      create,
      findById: vi.fn(),
      findAll: vi.fn(),
      update: vi.fn()
    };

    const service = new ProjectService({ projectRepo });

    const result = await service.create({
      name: "Proyecto Demo",
      description: null,
      status: "active",
      parametric_control_enabled: false,
      metadata: {}
    });

    expect(create).toHaveBeenCalledTimes(1);
    expect(result.id).toBe("project-1");
    expect(result.status).toBe("active");
    expect(result.parametric_control_enabled).toBe(false);
  });
});
