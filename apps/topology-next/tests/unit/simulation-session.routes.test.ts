import { beforeEach, describe, expect, it, vi } from "vitest";

const projectId = "11111111-1111-4111-8111-111111111111";
const sessionId = "22222222-2222-4222-8222-222222222222";
const actor = {
  actor_id: "oauth@example.test", user_id: "oauth@example.test", display_name: "OAuth Test",
  email: "oauth@example.test", role: "operator", all_projects: false, project_ids: [projectId],
  project_roles: { [projectId]: "operator" }, auth_source: "oauth_session" as const
};

const service = {
  create: vi.fn(), prepare: vi.fn(), get: vi.fn(), list: vi.fn()
};

vi.mock("@/lib/auth/control-auth-session", () => ({
  resolveAuthenticatedControlActor: vi.fn(async () => actor)
}));
vi.mock("@/lib/services/simulation-session.service", () => ({
  SimulationSessionService: class { create = service.create; prepare = service.prepare; get = service.get; list = service.list; }
}));

const params = { params: Promise.resolve({ projectId, sessionId }) };
const projectParams = { params: Promise.resolve({ projectId }) };

describe("M5.2 simulation session routes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    service.create.mockResolvedValue({ id: sessionId, project_id: projectId, status: "DRAFT" });
    service.prepare.mockResolvedValue({ id: sessionId, project_id: projectId, status: "READY",
      experiment_fingerprint: "a".repeat(64), policy_snapshot_hash: "b".repeat(64),
      topology_snapshot_hash: "c".repeat(64), dataset_snapshot_hash: "d".repeat(64),
      configuration_snapshot_hash: "e".repeat(64) });
    service.get.mockImplementation(async (_actor, scopedProject, scopedSession) => ({
      id: scopedSession, project_id: scopedProject, status: "READY", experiment_fingerprint: "a".repeat(64),
      policy_snapshot_hash: "b".repeat(64), topology_snapshot_hash: "c".repeat(64),
      dataset_snapshot_hash: "d".repeat(64), configuration_snapshot_hash: "e".repeat(64)
    }));
  });

  it("delegates OAuth project-scoped create DRAFT, prepare READY, and GET metadata through the route layer", async () => {
    const sessionsRoute = await import("@/app/api/control/simulations/projects/[projectId]/sessions/route");
    const prepareRoute = await import("@/app/api/control/simulations/projects/[projectId]/sessions/[sessionId]/prepare/route");
    const sessionRoute = await import("@/app/api/control/simulations/projects/[projectId]/sessions/[sessionId]/route");
    const created = await sessionsRoute.POST(new Request("http://localhost", { method: "POST", body: JSON.stringify({ metadata: { purpose: "test" } }) }), projectParams);
    expect(created.status).toBe(201);
    expect(service.create).toHaveBeenCalledWith(actor, projectId, { metadata: { purpose: "test" }, snapshot_refs: {} });
    const prepared = await prepareRoute.POST(new Request("http://localhost", { method: "POST", body: JSON.stringify({
      policy_id: "33333333-3333-4333-8333-333333333333", dataset: { source_kind: "synthetic", records: [{
        event_id: "44444444-4444-4444-8444-444444444444", project_id: projectId, variable: "temperature", value: 20,
        timestamp: "2026-08-21T00:00:00+00:00"
      }] }, configuration: {} }) }), params);
    expect(prepared.status).toBe(200);
    expect(service.prepare).toHaveBeenCalledWith(actor, projectId, sessionId, expect.objectContaining({ policy_id: expect.any(String) }));
    const ready = await sessionRoute.GET(new Request("http://localhost"), params);
    const body = await ready.json();
    expect(body.data.status).toBe("READY");
    expect(body.data.experiment_fingerprint).toMatch(/^[0-9a-f]{64}$/);
    expect(body.data.policy_snapshot_hash).toMatch(/^[0-9a-f]{64}$/);
  });
});
