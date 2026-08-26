import { assertControlPermission } from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import type { ExperimentEvaluation } from "@/lib/dto/experiment-evaluation.dto";
import { evaluateExperiment } from "@/lib/evaluation/experiment-evaluator";
import { NotFoundError } from "@/lib/errors/domain-errors";
import { EvaluationProfileRepository } from "@/lib/repositories/evaluation-profile.repository";
import { ExperimentEvaluationRepository } from "@/lib/repositories/experiment-evaluation.repository";
import { ProjectRepository } from "@/lib/repositories/project.repository";

interface ExperimentEvaluationServiceDeps {
  evaluationRepository?: Pick<ExperimentEvaluationRepository, "findSimulationResult" | "createOrGet" | "listByProject" | "findByProjectAndId">;
  profileRepository?: Pick<EvaluationProfileRepository, "findByProjectAndId">;
  projectRepository?: Pick<ProjectRepository, "findById">;
}

export class ExperimentEvaluationService {
  private readonly evaluations: Pick<ExperimentEvaluationRepository, "findSimulationResult" | "createOrGet" | "listByProject" | "findByProjectAndId">;
  private readonly profiles: Pick<EvaluationProfileRepository, "findByProjectAndId">;
  private readonly projects: Pick<ProjectRepository, "findById">;

  constructor(deps: ExperimentEvaluationServiceDeps = {}) {
    this.evaluations = deps.evaluationRepository ?? new ExperimentEvaluationRepository();
    this.profiles = deps.profileRepository ?? new EvaluationProfileRepository();
    this.projects = deps.projectRepository ?? new ProjectRepository();
  }

  async evaluate(actor: ControlActor, projectId: string, simulationResultId: string, evaluationProfileId: string): Promise<ExperimentEvaluation> {
    await this.authorize(actor, projectId, "edit_policies");
    const [result, profile] = await Promise.all([
      this.evaluations.findSimulationResult(projectId, simulationResultId), this.profiles.findByProjectAndId(projectId, evaluationProfileId)
    ]);
    if (!result) throw new NotFoundError("Simulation result not found in project scope");
    if (!profile) throw new NotFoundError("Evaluation profile not found in project scope");
    return this.evaluations.createOrGet(projectId, actor.actor_id ?? actor.user_id, { result, profile }, evaluateExperiment({ result, profile }));
  }

  async list(actor: ControlActor, projectId: string): Promise<ExperimentEvaluation[]> {
    await this.authorize(actor, projectId, "view_dashboard");
    return this.evaluations.listByProject(projectId);
  }

  async get(actor: ControlActor, projectId: string, evaluationId: string): Promise<ExperimentEvaluation> {
    await this.authorize(actor, projectId, "view_dashboard");
    const evaluation = await this.evaluations.findByProjectAndId(projectId, evaluationId);
    if (!evaluation) throw new NotFoundError("Experiment evaluation not found in project scope");
    return evaluation;
  }

  private async authorize(actor: ControlActor, projectId: string, permission: "view_dashboard" | "edit_policies"): Promise<void> {
    assertControlPermission(actor, permission, projectId);
    if (!await this.projects.findById(projectId)) throw new NotFoundError("Project not found");
  }
}
