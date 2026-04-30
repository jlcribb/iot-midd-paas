import type { ControlAccessSnapshot, ControlActor } from "@/lib/dto/control-access.dto";
import type { IProjectRepository } from "@/lib/repositories/contracts";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import { filterProjectsByScope, getControlPermissions } from "@/lib/auth/control-access";

interface ControlAccessServiceDeps {
  projectRepo?: IProjectRepository;
}

export class ControlAccessService {
  private readonly projectRepo: IProjectRepository;

  constructor(deps: ControlAccessServiceDeps = {}) {
    this.projectRepo = deps.projectRepo ?? new ProjectRepository();
  }

  async getSnapshot(actor: ControlActor): Promise<ControlAccessSnapshot> {
    const projects = await this.projectRepo.findAll();
    return {
      actor,
      permissions: getControlPermissions(actor.role),
      allowed_projects: filterProjectsByScope(actor, projects)
    };
  }
}
