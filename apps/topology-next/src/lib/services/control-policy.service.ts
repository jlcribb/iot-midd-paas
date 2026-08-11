import type { ControlActor } from "@/lib/dto/control-access.dto";
import { assertControlPermission, getScopedProjectIds } from "@/lib/auth/control-access";
import { isDeepStrictEqual } from "node:util";
import { ConflictError, NotFoundError } from "@/lib/errors/domain-errors";
import type { ControlPolicy, ControlPolicyPreviewResponse } from "@/lib/dto/control-policy.dto";
import type {
  IAssetRepository,
  IControlPolicyAuditRepository,
  IControlPolicyRepository,
  IProjectRepository
} from "@/lib/repositories/contracts";
import { ControlPolicyAuditRepository } from "@/lib/repositories/control-policy-audit.repository";
import { ControlPolicyRepository } from "@/lib/repositories/control-policy.repository";
import { AssetRepository } from "@/lib/repositories/asset.repository";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import type { CreateControlPolicyInput, UpdateControlPolicyInput } from "@/lib/validators/control-policy.schemas";
import { validatePolicyParams } from "@/lib/validators/control-policy.schemas";
import { buildPreviewResponse, detectPolicyConflicts } from "@/lib/utils/control-policy-governance";

interface ControlPolicyServiceDeps {
  assetRepo?: IAssetRepository;
  controlPolicyRepo?: IControlPolicyRepository;
  projectRepo?: IProjectRepository;
  controlPolicyAuditRepo?: IControlPolicyAuditRepository;
}

export class ControlPolicyService {
  private readonly controlPolicyRepo: IControlPolicyRepository;
  private readonly assetRepo: IAssetRepository;
  private readonly projectRepo: IProjectRepository;
  private readonly controlPolicyAuditRepo: IControlPolicyAuditRepository;

  constructor(deps: ControlPolicyServiceDeps = {}) {
    this.controlPolicyRepo = deps.controlPolicyRepo ?? new ControlPolicyRepository();
    this.assetRepo = deps.assetRepo ?? new AssetRepository();
    this.projectRepo = deps.projectRepo ?? new ProjectRepository();
    this.controlPolicyAuditRepo = deps.controlPolicyAuditRepo ?? new ControlPolicyAuditRepository();
  }

  async list(actor: ControlActor, filters?: { projectId?: string; variable?: string; enabled?: boolean }) {
    assertControlPermission(actor, "view_policies", filters?.projectId);
    return this.controlPolicyRepo.findAll({
      ...filters,
      projectIds: getScopedProjectIds(actor, filters?.projectId)
    });
  }

  async create(actor: ControlActor, input: CreateControlPolicyInput) {
    assertControlPermission(actor, "edit_policies", input.project_id);
    const project = await this.projectRepo.findById(input.project_id);
    if (!project) {
      throw new NotFoundError("Project not found");
    }
    await this.assertBindingBelongsToProject(input.project_id, input.binding.asset_id);

    validatePolicyParams(input.policy_type, input.params);
    await this.assertNoBlockingConflicts({
      project_id: input.project_id,
      variable: input.variable,
      binding: input.binding,
      policy_type: input.policy_type,
      context_selector: input.context_selector,
      params: input.params,
      priority: input.priority,
      enabled: input.enabled,
      version: 1
    });

    const created = await this.controlPolicyRepo.create(input);
    await this.controlPolicyAuditRepo.recordChange({
      entityId: created.id,
      action: "CONTROL_POLICY_CREATED",
      before: null,
      after: created,
      context: {
        actor,
        project_id: created.project_id,
        variable: created.variable
      }
    });
    return created;
  }

  async getById(actor: ControlActor, id: string) {
    assertControlPermission(actor, "view_policies");
    const policy = await this.controlPolicyRepo.findById(id);
    if (!policy) {
      throw new NotFoundError("Control policy not found");
    }
    assertControlPermission(actor, "view_policies", policy.project_id);
    return policy;
  }

  async update(actor: ControlActor, id: string, input: UpdateControlPolicyInput) {
    const existing = await this.getById(actor, id);
    assertControlPermission(actor, "edit_policies", existing.project_id);
    if (input.enabled !== undefined && input.enabled !== existing.enabled) {
      assertControlPermission(actor, "toggle_policies", existing.project_id);
    }
    const nextState = {
      ...existing,
      binding: input.binding ?? existing.binding,
      context_selector: input.context_selector ?? existing.context_selector,
      params: input.params ?? existing.params,
      priority: input.priority ?? existing.priority,
      enabled: input.enabled ?? existing.enabled,
      version: existing.version + 1
    };

    if (input.params !== undefined) {
      validatePolicyParams(existing.policy_type, input.params);
    }
    if (input.binding !== undefined) {
      await this.assertBindingBelongsToProject(existing.project_id, input.binding.asset_id);
    }

    if (this.isNoopUpdate(existing, input)) {
      return existing;
    }

    await this.assertNoBlockingConflicts({
      id: existing.id,
      project_id: existing.project_id,
      variable: existing.variable,
      binding: nextState.binding,
      policy_type: existing.policy_type,
      context_selector: nextState.context_selector,
      params: nextState.params,
      priority: nextState.priority,
      enabled: nextState.enabled,
      version: nextState.version
    });

    const updated = await this.controlPolicyRepo.update(id, {
      ...input,
      version: existing.version + 1
    });

    if (!updated) {
      throw new NotFoundError("Control policy not found");
    }

    await this.controlPolicyAuditRepo.recordChange({
      entityId: updated.id,
      action: "CONTROL_POLICY_UPDATED",
      before: existing,
      after: updated,
      context: {
        actor,
        project_id: updated.project_id,
        variable: updated.variable
      }
    });

    return updated;
  }

  async disable(actor: ControlActor, id: string) {
    const existing = await this.getById(actor, id);
    assertControlPermission(actor, "toggle_policies", existing.project_id);
    if (!existing.enabled) {
      return existing;
    }

    const updated = await this.controlPolicyRepo.update(id, {
      enabled: false,
      version: existing.version + 1
    });

    if (!updated) {
      throw new NotFoundError("Control policy not found");
    }

    await this.controlPolicyAuditRepo.recordChange({
      entityId: updated.id,
      action: "CONTROL_POLICY_DISABLED",
      before: existing,
      after: updated,
      context: {
        actor,
        project_id: updated.project_id,
        variable: updated.variable
      }
    });

    return updated;
  }

  async previewSelection(actor: ControlActor, input: {
    projectId: string;
    variable: string;
    assetId?: string;
    context: Record<string, unknown>;
    candidatePolicy?: {
      id?: string;
      project_id: string;
      variable: string;
      policy_type: ControlPolicy["policy_type"];
      context_selector: Record<string, unknown>;
      params: Record<string, unknown>;
      priority: number;
      enabled: boolean;
      version?: number;
      binding?: ControlPolicy["binding"];
    };
  }): Promise<ControlPolicyPreviewResponse> {
    assertControlPermission(actor, "view_policies", input.projectId);
    if (input.assetId) {
      await this.assertBindingBelongsToProject(input.projectId, input.assetId);
    }
    if (input.candidatePolicy?.binding) {
      await this.assertBindingBelongsToProject(input.projectId, input.candidatePolicy.binding.asset_id);
    }
    const existingPolicies = (await this.controlPolicyRepo.findAll({
      projectId: input.projectId,
      projectIds: getScopedProjectIds(actor, input.projectId),
      variable: input.variable
    })) ?? [];

    return buildPreviewResponse({
      project_id: input.projectId,
      variable: input.variable,
      context: input.context,
      asset_id: input.assetId ?? input.candidatePolicy?.binding?.asset_id,
      existingPolicies,
      candidate: input.candidatePolicy
    });
  }

  private isNoopUpdate(existing: ControlPolicy, input: UpdateControlPolicyInput) {
    if (input.priority !== undefined && input.priority !== existing.priority) {
      return false;
    }
    if (input.enabled !== undefined && input.enabled !== existing.enabled) {
      return false;
    }
    if (input.context_selector !== undefined && !isDeepStrictEqual(input.context_selector, existing.context_selector)) {
      return false;
    }
    if (input.params !== undefined && !isDeepStrictEqual(input.params, existing.params)) {
      return false;
    }
    if (input.binding !== undefined && !isDeepStrictEqual(input.binding, existing.binding)) {
      return false;
    }
    return true;
  }

  private async assertNoBlockingConflicts(candidate: {
    id?: string;
    project_id: string;
    variable: string;
    binding: ControlPolicy["binding"];
    policy_type: ControlPolicy["policy_type"];
    context_selector: Record<string, unknown>;
    params: Record<string, unknown>;
    priority: number;
    enabled: boolean;
    version: number;
  }) {
    const existingPolicies = (await this.controlPolicyRepo.findAll({
      projectId: candidate.project_id,
      variable: candidate.variable
    })) ?? [];
    const conflicts = detectPolicyConflicts(candidate, existingPolicies);
    const blockingTie = conflicts.find((conflict) => conflict.type === "selection_tie");
    if (blockingTie) {
      throw new ConflictError(blockingTie.message, {
        conflicting_policy_ids: blockingTie.conflicting_policy_ids
      });
    }
  }

  private async assertBindingBelongsToProject(projectId: string, assetId: string) {
    const asset = await this.assetRepo.findById(assetId);
    if (!asset) {
      throw new NotFoundError("Binding asset not found");
    }
    if (asset.project_id !== projectId) {
      throw new ConflictError("Binding asset belongs to a different project");
    }
  }
}
