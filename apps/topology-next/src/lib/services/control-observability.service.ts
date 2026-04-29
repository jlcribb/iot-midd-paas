import { ValidationError } from "@/lib/errors/domain-errors";
import type { IControlObservabilityRepository } from "@/lib/repositories/contracts";
import { ControlObservabilityRepository } from "@/lib/repositories/control-observability.repository";

interface ControlObservabilityServiceDeps {
  observabilityRepo?: IControlObservabilityRepository;
}

function normalizeLimit(limit?: number): number {
  if (limit === undefined) {
    return 20;
  }
  if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
    throw new ValidationError("limit must be an integer between 1 and 100");
  }
  return limit;
}

export class ControlObservabilityService {
  private readonly observabilityRepo: IControlObservabilityRepository;

  constructor(deps: ControlObservabilityServiceDeps = {}) {
    this.observabilityRepo = deps.observabilityRepo ?? new ControlObservabilityRepository();
  }

  async listRecommendations(filters?: { projectId?: string; limit?: number }) {
    return this.observabilityRepo.findLatestRecommendations({
      projectId: filters?.projectId,
      limit: normalizeLimit(filters?.limit)
    });
  }

  async listAudit(filters?: {
    projectId?: string;
    status?: "processed" | "skipped" | "error";
    limit?: number;
  }) {
    return this.observabilityRepo.findAuditEntries({
      projectId: filters?.projectId,
      status: filters?.status,
      limit: normalizeLimit(filters?.limit ?? 50)
    });
  }

  async getStatus() {
    return this.observabilityRepo.getStatus();
  }
}
