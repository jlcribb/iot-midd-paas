import { assertControlPermission } from "@/lib/auth/control-access";
import { compareExperimentEvaluations } from "@/lib/comparison/experiment-comparison-engine";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import type { ExperimentComparison } from "@/lib/dto/experiment-comparison.dto";
import { NotFoundError } from "@/lib/errors/domain-errors";
import { ExperimentComparisonRepository } from "@/lib/repositories/experiment-comparison.repository";
import { ExperimentEvaluationRepository } from "@/lib/repositories/experiment-evaluation.repository";
import { ProjectRepository } from "@/lib/repositories/project.repository";

interface Deps {
  comparisonRepository?: Pick<ExperimentComparisonRepository, "createOrGet" | "listByProject" | "findByProjectAndId">;
  evaluationRepository?: Pick<ExperimentEvaluationRepository, "findByProjectAndId">;
  projectRepository?: Pick<ProjectRepository, "findById">;
}
export class ExperimentComparisonService {
  private readonly comparisons: Pick<ExperimentComparisonRepository, "createOrGet" | "listByProject" | "findByProjectAndId">;
  private readonly evaluations: Pick<ExperimentEvaluationRepository, "findByProjectAndId">;
  private readonly projects: Pick<ProjectRepository, "findById">;
  constructor(deps: Deps = {}) { this.comparisons = deps.comparisonRepository ?? new ExperimentComparisonRepository(); this.evaluations = deps.evaluationRepository ?? new ExperimentEvaluationRepository(); this.projects = deps.projectRepository ?? new ProjectRepository(); }
  async compare(actor: ControlActor, projectId: string, baselineEvaluationId: string, candidateEvaluationId: string): Promise<ExperimentComparison> {
    await this.authorize(actor, projectId, "edit_policies");
    const [baseline, candidate] = await Promise.all([this.evaluations.findByProjectAndId(projectId, baselineEvaluationId), this.evaluations.findByProjectAndId(projectId, candidateEvaluationId)]);
    if (!baseline || !candidate) throw new NotFoundError("Experiment evaluation not found in project scope");
    return this.comparisons.createOrGet(projectId, actor.actor_id ?? actor.user_id, baseline.id, candidate.id, compareExperimentEvaluations(baseline, candidate));
  }
  async list(actor: ControlActor, projectId: string): Promise<ExperimentComparison[]> { await this.authorize(actor, projectId, "view_dashboard"); return this.comparisons.listByProject(projectId); }
  async get(actor: ControlActor, projectId: string, id: string): Promise<ExperimentComparison> { await this.authorize(actor, projectId, "view_dashboard"); const comparison = await this.comparisons.findByProjectAndId(projectId, id); if (!comparison) throw new NotFoundError("Experiment comparison not found in project scope"); return comparison; }
  private async authorize(actor: ControlActor, projectId: string, permission: "view_dashboard" | "edit_policies"): Promise<void> { assertControlPermission(actor, permission, projectId); if (!await this.projects.findById(projectId)) throw new NotFoundError("Project not found"); }
}
