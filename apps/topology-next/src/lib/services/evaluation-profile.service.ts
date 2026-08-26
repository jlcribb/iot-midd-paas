import { assertControlPermission } from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import type { CreateEvaluationProfileInput, EvaluationMetric, EvaluationProfile } from "@/lib/dto/evaluation-profile.dto";
import { NotFoundError, ValidationError } from "@/lib/errors/domain-errors";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import { EvaluationProfileRepository } from "@/lib/repositories/evaluation-profile.repository";

interface EvaluationProfileServiceDeps {
  repository?: Pick<EvaluationProfileRepository, "listMetrics" | "listByProject" | "create">;
  projectRepository?: Pick<ProjectRepository, "findById">;
}

export class EvaluationProfileService {
  private readonly repository: Pick<EvaluationProfileRepository, "listMetrics" | "listByProject" | "create">;
  private readonly projectRepository: Pick<ProjectRepository, "findById">;

  constructor(deps: EvaluationProfileServiceDeps = {}) {
    this.repository = deps.repository ?? new EvaluationProfileRepository();
    this.projectRepository = deps.projectRepository ?? new ProjectRepository();
  }

  async listMetrics(actor: ControlActor): Promise<EvaluationMetric[]> {
    assertControlPermission(actor, "view_dashboard");
    return this.repository.listMetrics();
  }

  async listProfiles(actor: ControlActor, projectId: string): Promise<EvaluationProfile[]> {
    await this.authorizeProject(actor, projectId, "view_dashboard");
    return this.repository.listByProject(projectId);
  }

  async createProfile(actor: ControlActor, projectId: string, input: CreateEvaluationProfileInput): Promise<EvaluationProfile> {
    await this.authorizeProject(actor, projectId, "edit_policies");
    this.assertMetricWeights(input);
    return this.repository.create(projectId, actor.actor_id ?? actor.user_id, input);
  }

  /**
   * The HTTP schema is the first validation boundary. Keep these invariants at
   * the service boundary as well, so future internal callers cannot create an
   * ambiguous objective profile by bypassing the route validator.
   */
  private assertMetricWeights(input: CreateEvaluationProfileInput): void {
    if (input.metrics.length === 0) throw new ValidationError("An evaluation profile requires at least one metric");

    const metricIds = new Set<string>();
    let totalWeight = 0;
    for (const metric of input.metrics) {
      if (metricIds.has(metric.metric_id)) throw new ValidationError("Each metric can appear only once in an evaluation profile");
      if (!Number.isFinite(metric.weight) || metric.weight <= 0 || metric.weight > 1) {
        throw new ValidationError("Metric weights must be finite values greater than zero and at most one");
      }
      metricIds.add(metric.metric_id);
      totalWeight += metric.weight;
    }

    if (Math.abs(totalWeight - 1) > 1e-9) throw new ValidationError("Evaluation profile metric weights must sum to one");
    const constrainedMetricIds = new Set<string>();
    for (const constraint of input.constraints ?? []) {
      const lowerBound = constraint.lower_bound;
      const upperBound = constraint.upper_bound;
      if (!metricIds.has(constraint.metric_id)) throw new ValidationError("Evaluation profile constraints must reference a profile metric");
      if (constrainedMetricIds.has(constraint.metric_id)) throw new ValidationError("Only one evaluation profile constraint is permitted per metric");
      constrainedMetricIds.add(constraint.metric_id);
      if (constraint.kind === "MINIMUM" && !Number.isFinite(lowerBound)) throw new ValidationError("MINIMUM constraints require a finite lower bound");
      if (constraint.kind === "MAXIMUM" && !Number.isFinite(upperBound)) throw new ValidationError("MAXIMUM constraints require a finite upper bound");
      if (constraint.kind === "RANGE" && (!Number.isFinite(lowerBound) || !Number.isFinite(upperBound) || (lowerBound as number) > (upperBound as number))) {
        throw new ValidationError("RANGE constraints require finite ordered bounds");
      }
    }
  }

  private async authorizeProject(actor: ControlActor, projectId: string, permission: "view_dashboard" | "edit_policies") {
    assertControlPermission(actor, permission, projectId);
    if (!await this.projectRepository.findById(projectId)) throw new NotFoundError("Project not found");
  }
}
