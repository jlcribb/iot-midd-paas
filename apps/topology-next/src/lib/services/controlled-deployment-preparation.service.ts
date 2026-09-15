import { assertControlPermission } from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { NotFoundError } from "@/lib/errors/domain-errors";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import { ControlledDeploymentPreparationRepository } from "@/lib/repositories/controlled-deployment-preparation.repository";

export class ControlledDeploymentPreparationService {
  constructor(private repo = new ControlledDeploymentPreparationRepository(), private projects = new ProjectRepository()) {}
  private async authorize(actor: ControlActor, projectId: string, permission: "view_dashboard" | "edit_policies") { assertControlPermission(actor, permission, projectId); if (!await this.projects.findById(projectId)) throw new NotFoundError("Project not found"); }
  async create(actor: ControlActor, projectId: string, candidateId: string, targetAssetId: string) { await this.authorize(actor,projectId,"edit_policies"); return this.repo.createOrGet(projectId,candidateId,targetAssetId,actor.actor_id ?? actor.user_id); }
  async list(actor: ControlActor, projectId: string, candidateId: string) { await this.authorize(actor,projectId,"view_dashboard"); return this.repo.list(projectId,candidateId); }
  async get(actor: ControlActor, projectId: string, candidateId: string, preparationId: string) { await this.authorize(actor,projectId,"view_dashboard"); const preparation = await this.repo.get(projectId,candidateId,preparationId); if (!preparation) throw new NotFoundError("Controlled deployment preparation not found in project scope"); return preparation; }
  async assess(actor: ControlActor, projectId: string, candidateId: string, preparationId: string) { await this.authorize(actor,projectId,"edit_policies"); const developmentFallbackEnabled = process.env.NODE_ENV !== "production" && process.env.CONTROL_RBAC_ALLOW_DEV_FALLBACK?.trim().toLowerCase() === "true"; return this.repo.assess(projectId,candidateId,preparationId,actor.actor_id ?? actor.user_id,developmentFallbackEnabled); }
  async assessments(actor: ControlActor, projectId: string, candidateId: string, preparationId: string) { await this.authorize(actor,projectId,"view_dashboard"); return this.repo.assessments(projectId,candidateId,preparationId); }
  async assessment(actor: ControlActor, projectId: string, candidateId: string, preparationId: string, assessmentId: string) { await this.authorize(actor,projectId,"view_dashboard"); const assessment = await this.repo.assessment(projectId,candidateId,preparationId,assessmentId); if (!assessment) throw new NotFoundError("Operational readiness assessment not found in project scope"); return assessment; }
}
