import { assertControlPermission } from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { ForbiddenError, NotFoundError } from "@/lib/errors/domain-errors";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import { GovernedDeploymentExecutionRepository } from "@/lib/repositories/governed-deployment-execution.repository";

export class GovernedDeploymentExecutionService {
  constructor(private repo = new GovernedDeploymentExecutionRepository(), private projects = new ProjectRepository()) {}

  private async authorize(actor: ControlActor, projectId: string, permission: "view_dashboard" | "edit_policies") {
    if (process.env.NODE_ENV !== "production" && process.env.CONTROL_RBAC_ALLOW_DEV_FALLBACK?.trim().toLowerCase() === "true") {
      throw new ForbiddenError("CONTROL_RBAC_ALLOW_DEV_FALLBACK must remain disabled for governed deployment execution");
    }
    assertControlPermission(actor, permission, projectId);
    if (!await this.projects.findById(projectId)) throw new NotFoundError("Project not found");
  }

  async execute(actor: ControlActor, projectId: string, candidateId: string, intentId: string) {
    await this.authorize(actor, projectId, "edit_policies");
    return this.repo.execute(projectId, candidateId, intentId, actor.actor_id ?? actor.user_id);
  }

  async list(actor: ControlActor, projectId: string, candidateId: string, intentId: string) {
    await this.authorize(actor, projectId, "view_dashboard");
    return this.repo.list(projectId, candidateId, intentId);
  }

  async get(actor: ControlActor, projectId: string, candidateId: string, intentId: string, executionId: string) {
    await this.authorize(actor, projectId, "view_dashboard");
    return this.repo.get(projectId, candidateId, intentId, executionId);
  }
}
