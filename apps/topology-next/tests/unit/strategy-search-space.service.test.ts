import { describe, expect, it, vi } from "vitest";
import { ForbiddenError, NotFoundError } from "@/lib/errors/domain-errors";
import { StrategySearchSpaceService } from "@/lib/services/strategy-search-space.service";

const projectA = "11111111-1111-4111-8111-111111111111";
const projectB = "22222222-2222-4222-8222-222222222222";
const spaceId = "33333333-3333-4333-8333-333333333333";
const actor = { actor_id: "operator@example.test", user_id: "operator@example.test", display_name: "Operator", role: "operator" as const, all_projects: false, project_ids: [projectA], project_roles: { [projectA]: "operator" as const }, auth_source: "oauth_session" as const };
function subject() {
  const repository = { createOrGet: vi.fn().mockResolvedValue({ id: spaceId, project_id: projectA, status: "GENERATED" }), listByProject: vi.fn().mockResolvedValue([]), findByProjectAndId: vi.fn().mockResolvedValue({ id: spaceId, project_id: projectA }), listCandidates: vi.fn().mockResolvedValue([]) };
  const projectRepository = { findById: vi.fn().mockResolvedValue({ id: projectA }) };
  return { service: new StrategySearchSpaceService({ repository, projectRepository }), repository, projectRepository };
}
describe("StrategySearchSpaceService", () => {
  it("creates Grid candidates only within OAuth project scope", async () => {
    const { service, repository } = subject();
    await service.create(actor, projectA, { name: "Proportional", strategy_type: "proportional", generation_method: "GRID", parameters: { gain: { values: [0.1, 0.2] }, setpoint_value: { values: [50] } } });
    expect(repository.createOrGet).toHaveBeenCalledOnce();
  });
  it("fails closed before repository work outside membership", async () => {
    const { service, repository } = subject();
    await expect(service.create(actor, projectB, { name: "Denied", strategy_type: "proportional", generation_method: "GRID", parameters: { gain: { values: [1] }, setpoint_value: { values: [50] } } })).rejects.toBeInstanceOf(ForbiddenError);
    expect(repository.createOrGet).not.toHaveBeenCalled();
  });
  it("does not disclose an absent search space or project", async () => {
    const { service, repository, projectRepository } = subject();
    repository.findByProjectAndId.mockResolvedValue(null);
    await expect(service.get(actor, projectA, spaceId)).rejects.toBeInstanceOf(NotFoundError);
    projectRepository.findById.mockResolvedValue(null);
    await expect(service.list(actor, projectA)).rejects.toBeInstanceOf(NotFoundError);
  });
});
