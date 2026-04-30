import { isDeepStrictEqual } from "node:util";
import { ConflictError, NotFoundError } from "@/lib/errors/domain-errors";
import type { ControlPolicy, ControlPolicyPreviewResponse } from "@/lib/dto/control-policy.dto";
import type {
  IControlPolicyAuditRepository,
  IControlPolicyRepository,
  IProjectRepository
} from "@/lib/repositories/contracts";
import { ControlPolicyAuditRepository } from "@/lib/repositories/control-policy-audit.repository";
import { ControlPolicyRepository } from "@/lib/repositories/control-policy.repository";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import type { CreateControlPolicyInput, UpdateControlPolicyInput } from "@/lib/validators/control-policy.schemas";
import { validatePolicyParams } from "@/lib/validators/control-policy.schemas";
import { buildPreviewResponse, detectPolicyConflicts } from "@/lib/utils/control-policy-governance";

interface ControlPolicyServiceDeps {
  controlPolicyRepo?: IControlPolicyRepository;
  projectRepo?: IProjectRepository;
  controlPolicyAuditRepo?: IControlPolicyAuditRepository;
}

export class ControlPolicyService {
  private readonly controlPolicyRepo: IControlPolicyRepository;
  private readonly projectRepo: IProjectRepository;
  private readonly controlPolicyAuditRepo: IControlPolicyAuditRepository;

  constructor(deps: ControlPolicyServiceDeps = {}) {
    this.controlPolicyRepo = deps.controlPolicyRepo ?? new ControlPolicyRepository();
    this.projectRepo = deps.projectRepo ?? new ProjectRepository();
    this.controlPolicyAuditRepo = deps.controlPolicyAuditRepo ?? new ControlPolicyAuditRepository();
  }

  async list(filters?: { projectId?: string; variable?: string; enabled?: boolean }) {
    return this.controlPolicyRepo.findAll(filters);
  }

  async create(input: CreateControlPolicyInput) {
    const project = await this.projectRepo.findById(input.project_id);
    if (!project) {
      throw new NotFoundError("Project not found");
    }

    validatePolicyParams(input.policy_type, input.params);
    await this.assertNoBlockingConflicts({
      project_id: input.project_id,
      variable: input.variable,
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
        project_id: created.project_id,
        variable: created.variable
      }
    });
    return created;
  }

  async getById(id: string) {
    const policy = await this.controlPolicyRepo.findById(id);
    if (!policy) {
      throw new NotFoundError("Control policy not found");
    }
    return policy;
  }

  async update(id: string, input: UpdateControlPolicyInput) {
    const existing = await this.getById(id);
    const nextState = {
      ...existing,
      context_selector: input.context_selector ?? existing.context_selector,
      params: input.params ?? existing.params,
      priority: input.priority ?? existing.priority,
      enabled: input.enabled ?? existing.enabled,
      version: existing.version + 1
    };

    if (input.params !== undefined) {
      validatePolicyParams(existing.policy_type, input.params);
    }

    if (this.isNoopUpdate(existing, input)) {
      return existing;
    }

    await this.assertNoBlockingConflicts({
      id: existing.id,
      project_id: existing.project_id,
      variable: existing.variable,
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
        project_id: updated.project_id,
        variable: updated.variable
      }
    });

    return updated;
  }

  async disable(id: string) {
    const existing = await this.getById(id);
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
        project_id: updated.project_id,
        variable: updated.variable
      }
    });

    return updated;
  }

  async previewSelection(input: {
    projectId: string;
    variable: string;
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
    };
  }): Promise<ControlPolicyPreviewResponse> {
    const existingPolicies = (await this.controlPolicyRepo.findAll({
      projectId: input.projectId,
      variable: input.variable
    })) ?? [];

    return buildPreviewResponse({
      project_id: input.projectId,
      variable: input.variable,
      context: input.context,
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
    return true;
  }

  private async assertNoBlockingConflicts(candidate: {
    id?: string;
    project_id: string;
    variable: string;
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
}
