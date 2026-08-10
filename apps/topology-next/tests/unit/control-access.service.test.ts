import { describe, expect, it, vi } from "vitest";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import type { Project } from "@/lib/dto/project.dto";
import type { IProjectRepository } from "@/lib/repositories/contracts";
import { ControlAccessService } from "@/lib/services/control-access.service";

const projects: Project[] = [
  {
    id: "project-admin",
    name: "Proyecto administrable",
    description: null,
    status: "active",
    parametric_control_enabled: false,
    metadata: {},
    created_at: "2026-01-01T00:00:00.000Z",
    updated_at: "2026-01-01T00:00:00.000Z"
  },
  {
    id: "project-read-only",
    name: "Proyecto solo lectura",
    description: null,
    status: "active",
    parametric_control_enabled: true,
    metadata: {},
    created_at: "2026-01-01T00:00:00.000Z",
    updated_at: "2026-01-01T00:00:00.000Z"
  }
];

function createService() {
  return new ControlAccessService({
    projectRepo: {
      findAll: vi.fn().mockResolvedValue(projects)
    } as unknown as IProjectRepository
  });
}

function actor(projectRoles: ControlActor["project_roles"]): ControlActor {
  return {
    actor_id: "actor-1",
    user_id: "actor-1",
    display_name: null,
    role: "admin",
    project_ids: projects.map((project) => project.id),
    project_roles: projectRoles,
    all_projects: false,
    auth_source: "oauth_session"
  };
}

describe("ControlAccessService", () => {
  it("exposes project-level management only where the persisted role permits it", async () => {
    const snapshot = await createService().getSnapshot(actor({
      "project-admin": "admin",
      "project-read-only": "viewer"
    }));

    expect(snapshot.allowed_projects.map((project) => project.id)).toEqual([
      "project-admin",
      "project-read-only"
    ]);
    expect(snapshot.manageable_parametric_control_project_ids).toEqual(["project-admin"]);
  });

  it.each(["viewer", "operator"] as const)("does not expose a mutation capability for a %s membership", async (role) => {
    const snapshot = await createService().getSnapshot(actor({
      "project-admin": role,
      "project-read-only": role
    }));

    expect(snapshot.manageable_parametric_control_project_ids).toEqual([]);
  });
});
