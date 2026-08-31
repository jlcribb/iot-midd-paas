import { assertControlPermission } from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import type { ControlStrategyCandidate, CreateStrategySearchSpaceInput, StrategySearchSpace } from "@/lib/dto/strategy-candidate.dto";
import { NotFoundError } from "@/lib/errors/domain-errors";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import { StrategySearchSpaceRepository } from "@/lib/repositories/strategy-search-space.repository";
import { generateGridSearch } from "@/lib/strategy/candidate-generator";

interface Deps { repository?: Pick<StrategySearchSpaceRepository, "createOrGet" | "listByProject" | "findByProjectAndId" | "listCandidates">; projectRepository?: Pick<ProjectRepository, "findById">; }
export class StrategySearchSpaceService {
  private readonly repository: NonNullable<Deps["repository"]>; private readonly projects: NonNullable<Deps["projectRepository"]>;
  constructor(deps: Deps = {}) { this.repository = deps.repository ?? new StrategySearchSpaceRepository(); this.projects = deps.projectRepository ?? new ProjectRepository(); }
  async create(actor: ControlActor, projectId: string, input: CreateStrategySearchSpaceInput): Promise<StrategySearchSpace> { await this.authorize(actor, projectId, "edit_policies"); return this.repository.createOrGet(projectId, actor.actor_id ?? actor.user_id, input, generateGridSearch(input.strategy_type, input.parameters)); }
  async list(actor: ControlActor, projectId: string): Promise<StrategySearchSpace[]> { await this.authorize(actor, projectId, "view_dashboard"); return this.repository.listByProject(projectId); }
  async get(actor: ControlActor, projectId: string, id: string): Promise<StrategySearchSpace> { await this.authorize(actor, projectId, "view_dashboard"); const item = await this.repository.findByProjectAndId(projectId, id); if (!item) throw new NotFoundError("Strategy search space not found in project scope"); return item; }
  async candidates(actor: ControlActor, projectId: string, id: string): Promise<ControlStrategyCandidate[]> { await this.get(actor, projectId, id); return this.repository.listCandidates(projectId, id); }
  private async authorize(actor: ControlActor, projectId: string, permission: "view_dashboard" | "edit_policies"): Promise<void> { assertControlPermission(actor, permission, projectId); if (!await this.projects.findById(projectId)) throw new NotFoundError("Project not found"); }
}
