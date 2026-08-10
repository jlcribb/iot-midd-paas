import { describe, expect, it, vi } from "vitest";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import type { SqlExecutor } from "@/lib/db/tx";
import { ProjectControlGovernanceService } from "@/lib/services/project-control-governance.service";

const project = {
  id: "project-1",
  name: "Proyecto Demo",
  description: null,
  status: "active" as const,
  parametric_control_enabled: false,
  metadata: {},
  created_at: "2026-01-01T00:00:00.000Z",
  updated_at: "2026-01-01T00:00:00.000Z"
};

function makeActor(role: ControlActor["role"], projectRoles: Record<string, ControlActor["role"]> = { "project-1": role }): ControlActor {
  return {
    actor_id: `${role}-1`,
    user_id: `${role}-1`,
    display_name: role,
    email: `${role}@example.com`,
    auth_source: "oauth_session",
    role,
    project_ids: Object.keys(projectRoles),
    project_roles: projectRoles,
    all_projects: false
  };
}

function makeService() {
  const projectRepo = {
    create: vi.fn(),
    findById: vi.fn().mockResolvedValue(project),
    findAll: vi.fn(),
    update: vi.fn()
  };
  const transactionalProjectRepo = {
    ...projectRepo,
    update: vi.fn().mockResolvedValue({ ...project, parametric_control_enabled: true })
  };
  const recordParametricControlChange = vi.fn().mockResolvedValue(undefined);
  const transactionRunner = vi.fn(async (fn) => fn({ query: vi.fn() } as unknown as SqlExecutor));
  const service = new ProjectControlGovernanceService({
    projectRepo,
    transactionRunner,
    projectRepositoryFactory: () => transactionalProjectRepo,
    auditRepositoryFactory: () => ({ recordParametricControlChange })
  });
  return { service, projectRepo, transactionalProjectRepo, recordParametricControlChange, transactionRunner };
}

describe("ProjectControlGovernanceService", () => {
  it("rejects unauthenticated feature-flag mutation without writing", async () => {
    const { service, projectRepo } = makeService();

    await expect(service.updateProjectWithParametricControl(null, "project-1", { parametric_control_enabled: true }))
      .rejects.toMatchObject({ status: 401 });
    expect(projectRepo.update).not.toHaveBeenCalled();
  });

  it.each(["viewer", "operator"] as const)("rejects %s feature-flag mutation", async (role) => {
    const { service, transactionalProjectRepo } = makeService();

    await expect(service.updateProjectWithParametricControl(makeActor(role), "project-1", { parametric_control_enabled: true }))
      .rejects.toMatchObject({ status: 403 });
    expect(transactionalProjectRepo.update).not.toHaveBeenCalled();
  });

  it("rejects an admin outside the project scope", async () => {
    const { service, transactionalProjectRepo } = makeService();

    await expect(service.updateProjectWithParametricControl(
      makeActor("admin", { "project-2": "admin" }),
      "project-1",
      { parametric_control_enabled: true }
    )).rejects.toMatchObject({ status: 403 });
    expect(transactionalProjectRepo.update).not.toHaveBeenCalled();
  });

  it("updates and audits an in-scope admin mutation atomically", async () => {
    const { service, transactionalProjectRepo, recordParametricControlChange, transactionRunner } = makeService();
    const actor = makeActor("admin");

    const result = await service.updateProjectWithParametricControl(
      actor,
      "project-1",
      { name: "Proyecto Renombrado", parametric_control_enabled: true },
      "request-1"
    );

    expect(result.parametric_control_enabled).toBe(true);
    expect(transactionRunner).toHaveBeenCalledTimes(1);
    expect(transactionalProjectRepo.update).toHaveBeenCalledWith("project-1", {
      name: "Proyecto Renombrado",
      parametric_control_enabled: true
    });
    expect(recordParametricControlChange).toHaveBeenCalledWith(expect.objectContaining({
      projectId: "project-1",
      actor,
      before: false,
      after: true,
      correlationId: "request-1"
    }));
  });

  it("does not create a false audit entry when the flag is unchanged", async () => {
    const { service, projectRepo, recordParametricControlChange, transactionRunner } = makeService();
    projectRepo.update.mockResolvedValue({ ...project, name: "Proyecto Renombrado" });

    await service.updateProjectWithParametricControl(makeActor("admin"), "project-1", {
      name: "Proyecto Renombrado",
      parametric_control_enabled: false
    });

    expect(transactionRunner).not.toHaveBeenCalled();
    expect(recordParametricControlChange).not.toHaveBeenCalled();
    expect(projectRepo.update).toHaveBeenCalledTimes(1);
  });

  it("does not allow a combined payload to bypass feature-flag authorization", async () => {
    const { service, projectRepo } = makeService();

    await expect(service.updateProjectWithParametricControl(makeActor("viewer"), "project-1", {
      name: "Intento combinado",
      parametric_control_enabled: true
    })).rejects.toMatchObject({ status: 403 });
    expect(projectRepo.update).not.toHaveBeenCalled();
  });

  it("returns not found without writing when the project does not exist", async () => {
    const { service, projectRepo } = makeService();
    projectRepo.findById.mockResolvedValue(null);

    await expect(service.updateProjectWithParametricControl(makeActor("admin"), "project-404", {
      parametric_control_enabled: true
    })).rejects.toMatchObject({ status: 404 });
    expect(projectRepo.update).not.toHaveBeenCalled();
  });
});
