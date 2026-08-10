import type { ControlAccessSnapshot, ControlActor } from "@/lib/dto/control-access.dto";
import type { IProjectRepository } from "@/lib/repositories/contracts";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import {
  filterProjectsByScope,
  getControlPermissions,
  getControlRoleForProject
} from "@/lib/auth/control-access";

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
    const allowedProjects = filterProjectsByScope(actor, projects);
    return {
      actor,
      permissions: getControlPermissions(actor.role),
      allowed_projects: allowedProjects,
      manageable_parametric_control_project_ids: allowedProjects
        .filter((project) => getControlPermissions(getControlRoleForProject(actor, project.id)).manage_parametric_control)
        .map((project) => project.id)
    };
  }
}
