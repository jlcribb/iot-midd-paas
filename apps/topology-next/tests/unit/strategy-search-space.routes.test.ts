import { beforeEach, describe, expect, it, vi } from "vitest";

const projectId = "11111111-1111-4111-8111-111111111111";
const searchSpaceId = "22222222-2222-4222-8222-222222222222";
const actor = { actor_id: "oauth@example.test", user_id: "oauth@example.test", display_name: "OAuth", role: "operator", all_projects: false, project_ids: [projectId], project_roles: { [projectId]: "operator" }, auth_source: "oauth_session" as const };
const service = { list: vi.fn(), create: vi.fn(), get: vi.fn(), candidates: vi.fn() };
vi.mock("@/lib/auth/control-auth-session", () => ({ resolveAuthenticatedControlActor: vi.fn(async () => actor) }));
vi.mock("@/lib/services/strategy-search-space.service", () => ({ StrategySearchSpaceService: class { list = service.list; create = service.create; get = service.get; candidates = service.candidates; } }));
describe("M6.4 strategy search-space routes", () => {
  beforeEach(() => { vi.clearAllMocks(); service.list.mockResolvedValue([]); service.create.mockResolvedValue({ id: searchSpaceId }); service.get.mockResolvedValue({ id: searchSpaceId }); service.candidates.mockResolvedValue([]); });
  it("uses the authenticated actor for collection, detail and candidate reads", async () => {
    const collection = await import("@/app/api/control/experiments/projects/[projectId]/search-spaces/route");
    const detail = await import("@/app/api/control/experiments/projects/[projectId]/search-spaces/[searchSpaceId]/route");
    const candidates = await import("@/app/api/control/experiments/projects/[projectId]/search-spaces/[searchSpaceId]/candidates/route");
    const collectionParams = { params: Promise.resolve({ projectId }) }; const detailParams = { params: Promise.resolve({ projectId, searchSpaceId }) };
    expect((await collection.GET(new Request("http://localhost"), collectionParams)).status).toBe(200);
    expect((await collection.POST(new Request("http://localhost", { method: "POST", body: JSON.stringify({ name: "Grid", strategy_type: "proportional", generation_method: "GRID", parameters: { gain: { values: [1] }, setpoint_value: { values: [50] } } }) }), collectionParams)).status).toBe(201);
    expect((await detail.GET(new Request("http://localhost"), detailParams)).status).toBe(200);
    expect((await candidates.GET(new Request("http://localhost"), detailParams)).status).toBe(200);
    expect(service.create).toHaveBeenCalledWith(actor, projectId, expect.objectContaining({ generation_method: "GRID" }));
  });
});
