import { beforeEach, describe, expect, it, vi } from "vitest";

const projectId = "11111111-1111-4111-8111-111111111111";
const resultId = "22222222-2222-4222-8222-222222222222";
const profileId = "33333333-3333-4333-8333-333333333333";
const evaluationId = "44444444-4444-4444-8444-444444444444";
const actor = { actor_id: "oauth@example.test", user_id: "oauth@example.test", display_name: "OAuth Test", role: "operator", all_projects: false, project_ids: [projectId], project_roles: { [projectId]: "operator" }, auth_source: "oauth_session" as const };
const service = { list: vi.fn(), evaluate: vi.fn(), get: vi.fn() };

vi.mock("@/lib/auth/control-auth-session", () => ({ resolveAuthenticatedControlActor: vi.fn(async () => actor) }));
vi.mock("@/lib/services/experiment-evaluation.service", () => ({ ExperimentEvaluationService: class { list = service.list; evaluate = service.evaluate; get = service.get; } }));

describe("M6.2 experiment evaluation routes", () => {
  beforeEach(() => { vi.clearAllMocks(); service.list.mockResolvedValue([]); service.evaluate.mockResolvedValue({ id: evaluationId, status: "COMPLETED" }); service.get.mockResolvedValue({ id: evaluationId, status: "COMPLETED" }); });

  it("uses the authenticated actor for scoped list, creation and detail reads", async () => {
    const collection = await import("@/app/api/control/evaluation/projects/[projectId]/evaluations/route");
    const detail = await import("@/app/api/control/evaluation/projects/[projectId]/evaluations/[evaluationId]/route");
    const collectionParams = { params: Promise.resolve({ projectId }) };
    const detailParams = { params: Promise.resolve({ projectId, evaluationId }) };
    expect((await collection.GET(new Request("http://localhost"), collectionParams)).status).toBe(200);
    expect((await collection.POST(new Request("http://localhost", { method: "POST", body: JSON.stringify({ simulationResultId: resultId, evaluationProfileId: profileId }) }), collectionParams)).status).toBe(201);
    expect((await detail.GET(new Request("http://localhost"), detailParams)).status).toBe(200);
    expect(service.list).toHaveBeenCalledWith(actor, projectId);
    expect(service.evaluate).toHaveBeenCalledWith(actor, projectId, resultId, profileId);
    expect(service.get).toHaveBeenCalledWith(actor, projectId, evaluationId);
  });
});
