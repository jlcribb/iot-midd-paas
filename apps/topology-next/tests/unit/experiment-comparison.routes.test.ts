import { beforeEach, describe, expect, it, vi } from "vitest";

const projectId = "11111111-1111-4111-8111-111111111111";
const baseline = "22222222-2222-4222-8222-222222222222";
const candidate = "33333333-3333-4333-8333-333333333333";
const comparison = "44444444-4444-4444-8444-444444444444";
const actor = { actor_id: "oauth@example.test", user_id: "oauth@example.test", display_name: "OAuth Test", role: "operator", all_projects: false, project_ids: [projectId], project_roles: { [projectId]: "operator" }, auth_source: "oauth_session" as const };
const service = { list: vi.fn(), compare: vi.fn(), get: vi.fn() };
vi.mock("@/lib/auth/control-auth-session", () => ({ resolveAuthenticatedControlActor: vi.fn(async () => actor) }));
vi.mock("@/lib/services/experiment-comparison.service", () => ({ ExperimentComparisonService: class { list = service.list; compare = service.compare; get = service.get; } }));
describe("M6.3 experiment comparison routes", () => {
  beforeEach(() => { vi.clearAllMocks(); service.list.mockResolvedValue([]); service.compare.mockResolvedValue({ id: comparison, relation: "BETTER" }); service.get.mockResolvedValue({ id: comparison, relation: "BETTER" }); });
  it("uses the authenticated actor for scoped list, creation and detail reads", async () => {
    const collection = await import("@/app/api/control/evaluation/projects/[projectId]/comparisons/route");
    const detail = await import("@/app/api/control/evaluation/projects/[projectId]/comparisons/[comparisonId]/route");
    const collectionParams = { params: Promise.resolve({ projectId }) };
    expect((await collection.GET(new Request("http://localhost"), collectionParams)).status).toBe(200);
    expect((await collection.POST(new Request("http://localhost", { method: "POST", body: JSON.stringify({ baselineEvaluationId: baseline, candidateEvaluationId: candidate }) }), collectionParams)).status).toBe(201);
    expect((await detail.GET(new Request("http://localhost"), { params: Promise.resolve({ projectId, comparisonId: comparison }) })).status).toBe(200);
    expect(service.list).toHaveBeenCalledWith(actor, projectId);
    expect(service.compare).toHaveBeenCalledWith(actor, projectId, baseline, candidate);
    expect(service.get).toHaveBeenCalledWith(actor, projectId, comparison);
  });
});
