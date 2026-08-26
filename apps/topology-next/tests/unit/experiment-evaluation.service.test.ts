import { describe, expect, it, vi } from "vitest";
import { ForbiddenError, NotFoundError } from "@/lib/errors/domain-errors";
import { ExperimentEvaluationService } from "@/lib/services/experiment-evaluation.service";

const projectA = "11111111-1111-4111-8111-111111111111";
const projectB = "22222222-2222-4222-8222-222222222222";
const resultId = "33333333-3333-4333-8333-333333333333";
const profileId = "44444444-4444-4444-8444-444444444444";
const actor = { actor_id: "operator@example.test", user_id: "operator@example.test", display_name: "Operator", role: "operator" as const,
  all_projects: false, project_ids: [projectA], project_roles: { [projectA]: "operator" as const }, auth_source: "oauth_session" as const };

function subject() {
  const evaluationRepository = {
    findSimulationResult: vi.fn().mockResolvedValue({ id: resultId, project_id: projectA, session_id: "55555555-5555-4555-8555-555555555555", run_id: "66666666-6666-4666-8666-666666666666", result_fingerprint: "a".repeat(64), processed_events: 1, actionable_recommendation_count: 10, failed_domain_event_count: 0 }),
    createOrGet: vi.fn().mockResolvedValue({ id: "77777777-7777-4777-8777-777777777777", project_id: projectA, status: "COMPLETED" }), listByProject: vi.fn().mockResolvedValue([]), findByProjectAndId: vi.fn().mockResolvedValue(null)
  };
  const profileRepository = { findByProjectAndId: vi.fn().mockResolvedValue({ id: profileId, project_id: projectA, code: "actuation_profile", version: 1, name: "Profile", description: "", status: "ACTIVE", schema_version: 1, metadata: {}, created_by: actor.actor_id, created_at: "2026-08-26T00:00:00.000Z", constraints: [], metrics: [{ metric: { id: "88888888-8888-4888-8888-888888888888", code: "actuation_count", version: 1, name: "Actuation count", description: "", unit: "count", direction: "MINIMIZE", normalization_method: "MIN_MAX", normalization_config: { schema_version: 1, best: 0, worst: 100 }, weightable: true, active: true, created_at: "2026-08-26T00:00:00.000Z" }, weight: 1, required: true }] }) };
  const projectRepository = { findById: vi.fn().mockResolvedValue({ id: projectA }) };
  return { service: new ExperimentEvaluationService({ evaluationRepository, profileRepository, projectRepository }), evaluationRepository, profileRepository, projectRepository };
}

describe("ExperimentEvaluationService", () => {
  it("evaluates only with OAuth operator project scope and delegates idempotent persistence", async () => {
    const { service, evaluationRepository } = subject();
    const evaluation = await service.evaluate(actor, projectA, resultId, profileId);
    expect(evaluation.status).toBe("COMPLETED");
    expect(evaluationRepository.createOrGet).toHaveBeenCalledOnce();
  });

  it("fails closed before data lookup for a project outside membership", async () => {
    const { service, evaluationRepository } = subject();
    await expect(service.evaluate(actor, projectB, resultId, profileId)).rejects.toBeInstanceOf(ForbiddenError);
    expect(evaluationRepository.findSimulationResult).not.toHaveBeenCalled();
  });

  it("does not disclose a cross-project simulation result", async () => {
    const { service, evaluationRepository } = subject();
    evaluationRepository.findSimulationResult.mockResolvedValue(null);
    await expect(service.evaluate(actor, projectA, resultId, profileId)).rejects.toBeInstanceOf(NotFoundError);
  });
});
