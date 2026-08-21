import { assertControlPermission } from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import type { CreateSimulationSessionInput, SimulationSession } from "@/lib/dto/simulation-session.dto";
import { NotFoundError } from "@/lib/errors/domain-errors";
import type { IProjectRepository } from "@/lib/repositories/contracts";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import { SimulationSessionRepository } from "@/lib/repositories/simulation-session.repository";

interface SimulationSessionServiceDeps {
  sessionRepo?: Pick<SimulationSessionRepository, "create" | "findByProjectAndId" | "listByProject">;
  projectRepo?: Pick<IProjectRepository, "findById">;
}

export class SimulationSessionService {
  private readonly sessionRepo: Pick<SimulationSessionRepository, "create" | "findByProjectAndId" | "listByProject">;
  private readonly projectRepo: Pick<IProjectRepository, "findById">;

  constructor(deps: SimulationSessionServiceDeps = {}) {
    this.sessionRepo = deps.sessionRepo ?? new SimulationSessionRepository();
    this.projectRepo = deps.projectRepo ?? new ProjectRepository();
  }

  async create(actor: ControlActor, projectId: string, input: CreateSimulationSessionInput): Promise<SimulationSession> {
    await this.authorize(actor, projectId, "edit_policies");
    return this.sessionRepo.create(projectId, actor.actor_id ?? actor.user_id, input);
  }

  async get(actor: ControlActor, projectId: string, sessionId: string): Promise<SimulationSession> {
    await this.authorize(actor, projectId, "view_dashboard");
    const session = await this.sessionRepo.findByProjectAndId(projectId, sessionId);
    if (!session) throw new NotFoundError("Simulation session not found");
    return session;
  }

  async list(actor: ControlActor, projectId: string): Promise<SimulationSession[]> {
    await this.authorize(actor, projectId, "view_dashboard");
    return this.sessionRepo.listByProject(projectId);
  }

  private async authorize(actor: ControlActor, projectId: string, permission: "edit_policies" | "view_dashboard") {
    assertControlPermission(actor, permission, projectId);
    if (!await this.projectRepo.findById(projectId)) throw new NotFoundError("Project not found");
  }
}
