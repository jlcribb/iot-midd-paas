import { describe, expect, it, vi } from "vitest";
import { ForbiddenError, NotFoundError, ValidationError } from "@/lib/errors/domain-errors";
import { EvaluationProfileService } from "@/lib/services/evaluation-profile.service";

const PROJECT_A = "11111111-1111-4111-8111-111111111111";
const PROJECT_B = "22222222-2222-4222-8222-222222222222";

function actor(projectIds = [PROJECT_A], role: "viewer" | "operator" = "operator") {
  return { actor_id: "oauth@example.test", user_id: "oauth@example.test", display_name: "OAuth Test", role,
    all_projects: false, project_ids: projectIds, project_roles: Object.fromEntries(projectIds.map((id) => [id, role])),
    auth_source: "oauth_session" as const };
}

function profile(projectId = PROJECT_A) {
  return { id: "33333333-3333-4333-8333-333333333333", project_id: projectId, code: "water_level_control_v1",
    version: 1, name: "Water level", description: "", status: "ACTIVE" as const, schema_version: 1 as const,
    metadata: {}, created_by: "oauth@example.test", created_at: "2026-08-26T00:00:00Z", metrics: [], constraints: [] };
}

function subject() {
  const repository = { listMetrics: vi.fn().mockResolvedValue([]), listByProject: vi.fn().mockResolvedValue([]), create: vi.fn().mockResolvedValue(profile()) };
  const projectRepository = { findById: vi.fn().mockResolvedValue({ id: PROJECT_A }) };
  return { service: new EvaluationProfileService({ repository, projectRepository }), repository, projectRepository };
}

describe("EvaluationProfileService", () => {
  it("creates an immutable profile version only for an operator in the project scope", async () => {
    const { service, repository } = subject();
    const input = { code: "water_level_control_v1", name: "Water level", metrics: [{ metric_id: "44444444-4444-4444-8444-444444444444", weight: 1 }] };
    const created = await service.createProfile(actor(), PROJECT_A, input);
    expect(created.project_id).toBe(PROJECT_A);
    expect(repository.create).toHaveBeenCalledWith(PROJECT_A, "oauth@example.test", input);
  });

  it("fails closed for a project outside the OAuth membership before repository access", async () => {
    const { service, repository } = subject();
    await expect(service.listProfiles(actor([PROJECT_A], "viewer"), PROJECT_B)).rejects.toBeInstanceOf(ForbiddenError);
    expect(repository.listByProject).not.toHaveBeenCalled();
  });

  it("does not create a profile for a missing project", async () => {
    const { service, repository, projectRepository } = subject();
    projectRepository.findById.mockResolvedValue(null);
    await expect(service.createProfile(actor(), PROJECT_A, { code: "water_level_control_v1", name: "Water level", metrics: [{ metric_id: "44444444-4444-4444-8444-444444444444", weight: 1 }] })).rejects.toBeInstanceOf(NotFoundError);
    expect(repository.create).not.toHaveBeenCalled();
  });

  it("enforces a unitary, unique metric weighting even for internal callers", async () => {
    const { service, repository } = subject();
    const input = {
      code: "water_level_control_v1",
      name: "Water level",
      metrics: [
        { metric_id: "44444444-4444-4444-8444-444444444444", weight: 0.6 },
        { metric_id: "44444444-4444-4444-8444-444444444444", weight: 0.3 },
      ],
    };

    await expect(service.createProfile(actor(), PROJECT_A, input)).rejects.toBeInstanceOf(ValidationError);
    expect(repository.create).not.toHaveBeenCalled();
  });

  it("does not allow an internal caller to attach a constraint to a metric outside the profile", async () => {
    const { service, repository } = subject();
    await expect(service.createProfile(actor(), PROJECT_A, {
      code: "water_level_control_v1", name: "Water level",
      metrics: [{ metric_id: "44444444-4444-4444-8444-444444444444", weight: 1 }],
      constraints: [{ metric_id: "55555555-5555-4555-8555-555555555555", kind: "MAXIMUM", upper_bound: 1 }]
    })).rejects.toBeInstanceOf(ValidationError);
    expect(repository.create).not.toHaveBeenCalled();
  });
});
