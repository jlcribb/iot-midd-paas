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
import { ControlPolicyActuationBindingRepository, type ActuationBindingInput } from "@/lib/repositories/control-policy-actuation-binding.repository";
import { AssetRepository } from "@/lib/repositories/asset.repository";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import type { CreateControlPolicyInput, UpdateControlPolicyInput } from "@/lib/validators/control-policy.schemas";
import { validatePolicyParams } from "@/lib/validators/control-policy.schemas";
import { buildPreviewResponse, detectPolicyConflicts } from "@/lib/utils/control-policy-governance";

interface IControlPolicyActuationBindingRepository {
  upsert(args: { policyId: string; projectId: string; sourceAssetId: string; input: ActuationBindingInput }): Promise<unknown>;
  remove(policyId: string): Promise<unknown>;
}

interface ControlPolicyServiceDeps {
  assetRepo?: IAssetRepository;
  controlPolicyRepo?: IControlPolicyRepository;
  projectRepo?: IProjectRepository;
  controlPolicyAuditRepo?: IControlPolicyAuditRepository;
  actuationBindingRepo?: IControlPolicyActuationBindingRepository;
}

export class ControlPolicyService {
  private readonly controlPolicyRepo: IControlPolicyRepository;
  private readonly assetRepo: IAssetRepository;
  private readonly projectRepo: IProjectRepository;
  private readonly controlPolicyAuditRepo: IControlPolicyAuditRepository;
  private readonly actuationBindingRepo: IControlPolicyActuationBindingRepository;

  constructor(deps: ControlPolicyServiceDeps = {}) {
    this.controlPolicyRepo = deps.controlPolicyRepo ?? new ControlPolicyRepository();
    this.assetRepo = deps.assetRepo ?? new AssetRepository();
    this.projectRepo = deps.projectRepo ?? new ProjectRepository();
    this.controlPolicyAuditRepo = deps.controlPolicyAuditRepo ?? new ControlPolicyAuditRepository();
    this.actuationBindingRepo = deps.actuationBindingRepo ?? new ControlPolicyActuationBindingRepository();
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
    if (input.actuation_binding) {
      // Validate before creating the policy so an invalid target cannot leave a
      // partially persisted recommendation policy behind.
      await this.assertActuationBinding(input.project_id, input.binding.asset_id, input.actuation_binding);
    }

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
    if (input.actuation_binding) {
      await this.actuationBindingRepo.upsert({
        policyId: created.id, projectId: created.project_id, sourceAssetId: input.binding.asset_id,
        input: input.actuation_binding
      });
    }
    const persisted = input.actuation_binding
      ? await this.controlPolicyRepo.findById(created.id) ?? created
      : created;
    await this.controlPolicyAuditRepo.recordChange({
      entityId: created.id,
      action: "CONTROL_POLICY_CREATED",
      before: null,
      after: persisted,
      context: {
        actor,
        project_id: persisted.project_id,
        variable: persisted.variable
      }
    });
    if (input.actuation_binding) {
      await this.controlPolicyAuditRepo.recordChange({
        entityId: persisted.id, action: "CONTROL_POLICY_ACTUATION_BINDING_CREATED",
        before: null, after: persisted.actuation_binding,
        context: { actor, project_id: persisted.project_id, source_asset_id: input.binding.asset_id }
      });
    }
    return persisted;
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
    if (existing.actuation_binding && input.binding && input.binding.asset_id !== existing.binding?.asset_id && input.actuation_binding === undefined) {
      throw new ConflictError("Changing the source binding requires updating or removing the actuation binding");
    }
    if (input.actuation_binding) {
      await this.assertActuationBinding(existing.project_id, nextState.binding?.asset_id ?? "", input.actuation_binding);
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

    let actuationBefore = existing.actuation_binding;
    if (input.actuation_binding === null) {
      await this.actuationBindingRepo.remove(updated.id);
    } else if (input.actuation_binding) {
      await this.actuationBindingRepo.upsert({
        policyId: updated.id, projectId: updated.project_id, sourceAssetId: nextState.binding?.asset_id ?? "",
        input: input.actuation_binding
      });
    }
    const persisted = input.actuation_binding !== undefined
      ? await this.controlPolicyRepo.findById(updated.id) ?? updated
      : updated;
    await this.controlPolicyAuditRepo.recordChange({
      entityId: updated.id,
      action: "CONTROL_POLICY_UPDATED",
      before: existing,
      after: persisted,
      context: {
        actor,
        project_id: updated.project_id,
        variable: updated.variable
      }
    });

    if (input.actuation_binding !== undefined) {
      await this.controlPolicyAuditRepo.recordChange({
        entityId: persisted.id,
        action: input.actuation_binding === null ? "CONTROL_POLICY_ACTUATION_BINDING_REMOVED" : "CONTROL_POLICY_ACTUATION_BINDING_UPDATED",
        before: actuationBefore,
        after: persisted.actuation_binding,
        context: { actor, project_id: persisted.project_id, source_asset_id: nextState.binding?.asset_id }
      });
    }
    return persisted;
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
    if (input.actuation_binding !== undefined && !isDeepStrictEqual(input.actuation_binding, existing.actuation_binding ?? null)) {
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

  private async assertActuationBinding(projectId: string, sourceAssetId: string, input: ActuationBindingInput) {
    if (!sourceAssetId) throw new ConflictError("Actuation binding requires a source asset policy binding");
    const [source, target] = await Promise.all([
      this.assetRepo.findById(sourceAssetId), this.assetRepo.findById(input.target_asset_id)
    ]);
    if (!source || source.project_id !== projectId) throw new ConflictError("Source asset belongs to a different project or does not exist");
    if (!target) throw new NotFoundError("Actuation target asset not found");
    if (target.project_id !== projectId) throw new ConflictError("Actuation target asset belongs to a different project");
    if (!["actuator", "relay_module", "programmable_node"].includes(target.asset_type)) {
      throw new ConflictError("Asset type is not eligible as an actuation target");
    }
    if (source.id === target.id && target.asset_type !== "programmable_node") {
      throw new ConflictError("Self target binding is only allowed for programmable_node assets");
    }
    const capabilities = target.metadata.control_capabilities;
    const capability = Array.isArray(capabilities)
      ? capabilities.find((item) => item && typeof item === "object" && (item as Record<string, unknown>).key === input.control_point)
      : null;
    const operations = capability && Array.isArray((capability as Record<string, unknown>).operations)
      ? (capability as Record<string, unknown>).operations as unknown[]
      : [];
    if (!capability || !operations.some((operation) => operation === input.operation)) {
      throw new ConflictError("Target control point does not support the requested operation");
    }
  }
}
