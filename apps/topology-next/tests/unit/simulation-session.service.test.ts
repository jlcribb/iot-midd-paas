import { describe, expect, it, vi } from "vitest";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { ForbiddenError, NotFoundError } from "@/lib/errors/domain-errors";
import { SimulationSessionService } from "@/lib/services/simulation-session.service";

const PROJECT_A = "11111111-1111-4111-8111-111111111111";
const PROJECT_B = "22222222-2222-4222-8222-222222222222";

function actor(role: ControlActor["role"], projectIds = [PROJECT_A]): ControlActor {
  return {
    actor_id: `${role}-actor`, user_id: `${role}-actor`, display_name: role, role,
    all_projects: false, project_ids: projectIds,
    project_roles: Object.fromEntries(projectIds.map((id) => [id, role])), auth_source: "oauth_session"
  };
}

function session(projectId = PROJECT_A) {
  return {
    id: "33333333-3333-4333-8333-333333333333", project_id: projectId,
    execution_context: "SIMULATION" as const, status: "DRAFT" as const, created_by: "operator-actor",
    snapshot_refs: {}, metadata: {}, created_at: "2026-08-21T00:00:00.000Z", started_at: null, completed_at: null
  };
}

function subject() {
  const sessionRepo = {
    create: vi.fn().mockResolvedValue(session()),
    findByProjectAndId: vi.fn().mockResolvedValue(session()),
    listByProject: vi.fn().mockResolvedValue([session()])
  };
  const projectRepo = { findById: vi.fn().mockResolvedValue({ id: PROJECT_A, name: "Project A", parametric_control_enabled: true }) };
  return { service: new SimulationSessionService({ sessionRepo, projectRepo }), sessionRepo, projectRepo };
}

describe("SimulationSessionService", () => {
  it("creates a DRAFT simulation session only inside an operator project scope", async () => {
    const { service, sessionRepo } = subject();
    const created = await service.create(actor("operator"), PROJECT_A, { metadata: { purpose: "future replay" } });

    expect(created.execution_context).toBe("SIMULATION");
    expect(created.status).toBe("DRAFT");
    expect(sessionRepo.create).toHaveBeenCalledWith(PROJECT_A, "operator-actor", { metadata: { purpose: "future replay" } });
  });

  it("fails closed before accessing a session in another project", async () => {
    const { service, sessionRepo } = subject();
    await expect(service.get(actor("viewer", [PROJECT_A]), PROJECT_B, session().id)).rejects.toBeInstanceOf(ForbiddenError);
    expect(sessionRepo.findByProjectAndId).not.toHaveBeenCalled();
  });

  it("does not give an authenticated actor without membership implicit simulation access", async () => {
    const { service, sessionRepo } = subject();
    await expect(service.list(actor("viewer", []), PROJECT_A)).rejects.toBeInstanceOf(ForbiddenError);
    expect(sessionRepo.listByProject).not.toHaveBeenCalled();
  });

  it("requires a real project after scope authorization", async () => {
    const { service, projectRepo, sessionRepo } = subject();
    projectRepo.findById.mockResolvedValue(null);
    await expect(service.create(actor("operator"), PROJECT_A, {})).rejects.toBeInstanceOf(NotFoundError);
    expect(sessionRepo.create).not.toHaveBeenCalled();
  });
});
