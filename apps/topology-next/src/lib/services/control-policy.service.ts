import { isDeepStrictEqual } from "node:util";
import { NotFoundError } from "@/lib/errors/domain-errors";
import type { ControlPolicy } from "@/lib/dto/control-policy.dto";
import type { IControlPolicyRepository, IProjectRepository } from "@/lib/repositories/contracts";
import { ControlPolicyRepository } from "@/lib/repositories/control-policy.repository";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import type { CreateControlPolicyInput, UpdateControlPolicyInput } from "@/lib/validators/control-policy.schemas";
import { validatePolicyParams } from "@/lib/validators/control-policy.schemas";

interface ControlPolicyServiceDeps {
  controlPolicyRepo?: IControlPolicyRepository;
  projectRepo?: IProjectRepository;
}

export class ControlPolicyService {
  private readonly controlPolicyRepo: IControlPolicyRepository;
  private readonly projectRepo: IProjectRepository;

  constructor(deps: ControlPolicyServiceDeps = {}) {
    this.controlPolicyRepo = deps.controlPolicyRepo ?? new ControlPolicyRepository();
    this.projectRepo = deps.projectRepo ?? new ProjectRepository();
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
    return this.controlPolicyRepo.create(input);
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

    if (input.params !== undefined) {
      validatePolicyParams(existing.policy_type, input.params);
    }

    if (this.isNoopUpdate(existing, input)) {
      return existing;
    }

    const updated = await this.controlPolicyRepo.update(id, {
      ...input,
      version: existing.version + 1
    });

    if (!updated) {
      throw new NotFoundError("Control policy not found");
    }

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

    return updated;
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
}
