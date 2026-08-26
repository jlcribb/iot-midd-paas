import { beforeEach, describe, expect, it, vi } from "vitest";

const projectId = "11111111-1111-4111-8111-111111111111";
const actor = { actor_id: "oauth@example.test", user_id: "oauth@example.test", display_name: "OAuth Test", role: "operator",
  all_projects: false, project_ids: [projectId], project_roles: { [projectId]: "operator" }, auth_source: "oauth_session" as const };
const service = { listMetrics: vi.fn(), listProfiles: vi.fn(), createProfile: vi.fn() };

vi.mock("@/lib/auth/control-auth-session", () => ({ resolveAuthenticatedControlActor: vi.fn(async () => actor) }));
vi.mock("@/lib/services/evaluation-profile.service", () => ({
  EvaluationProfileService: class { listMetrics = service.listMetrics; listProfiles = service.listProfiles; createProfile = service.createProfile; }
}));

describe("M6.1 evaluation profile routes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    service.listMetrics.mockResolvedValue([]);
    service.listProfiles.mockResolvedValue([]);
    service.createProfile.mockResolvedValue({ id: "33333333-3333-4333-8333-333333333333", project_id: projectId, version: 1 });
  });

  it("uses the authenticated actor and governed project scope for metric/profile reads and creation", async () => {
    const metricsRoute = await import("@/app/api/control/evaluation/metrics/route");
    const profilesRoute = await import("@/app/api/control/evaluation/projects/[projectId]/profiles/route");
    expect((await metricsRoute.GET(new Request("http://localhost"))).status).toBe(200);
    expect((await profilesRoute.GET(new Request("http://localhost"), { params: Promise.resolve({ projectId }) })).status).toBe(200);
    const response = await profilesRoute.POST(new Request("http://localhost", { method: "POST", body: JSON.stringify({
      code: "water_level_control_v1", name: "Water level", metrics: [{ metric_id: "44444444-4444-4444-8444-444444444444", weight: 1 }
      ] }) }), { params: Promise.resolve({ projectId }) });
    expect(response.status).toBe(201);
    expect(service.listMetrics).toHaveBeenCalledWith(actor);
    expect(service.listProfiles).toHaveBeenCalledWith(actor, projectId);
    expect(service.createProfile).toHaveBeenCalledWith(actor, projectId, expect.objectContaining({ code: "water_level_control_v1" }));
  });
});
