import { describe, expect, it, vi } from "vitest";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { ForbiddenError, NotFoundError, ValidationError } from "@/lib/errors/domain-errors";
import { SimulationSessionService } from "@/lib/services/simulation-session.service";

const PROJECT_A = "11111111-1111-4111-8111-111111111111";
const PROJECT_B = "22222222-2222-4222-8222-222222222222";

function actor(role: ControlActor["role"], projectIds = [PROJECT_A]): ControlActor {
  return {
    actor_id: `${role}-actor`, user_id: `${role}-actor`, display_name: role, role,
    all_projects: false, project_ids: projectIds,
    project_roles: Object.fromEntries(projectIds.map((id) => [id, role])), auth_source: "oauth_session"
  };
}

function session(projectId = PROJECT_A) {
  return {
    id: "33333333-3333-4333-8333-333333333333", project_id: projectId,
    execution_context: "SIMULATION" as const, status: "DRAFT" as const, created_by: "operator-actor",
    snapshot_refs: {}, metadata: {}, created_at: "2026-08-21T00:00:00.000Z", started_at: null, completed_at: null,
    prepared_at: null, policy_snapshot: null, topology_snapshot: null, dataset_snapshot: null,
    configuration_snapshot: null, policy_snapshot_hash: null, topology_snapshot_hash: null,
    dataset_snapshot_hash: null, configuration_snapshot_hash: null, experiment_fingerprint: null, snapshot_schema_version: null
  };
}

function subject() {
  const sessionRepo = {
    create: vi.fn().mockResolvedValue(session()),
    findByProjectAndId: vi.fn().mockResolvedValue(session()),
    listByProject: vi.fn().mockResolvedValue([session()]),
    prepare: vi.fn().mockImplementation(async (_projectId, _sessionId, _policyId, _preparedBy, builder) => {
      const material = builder({
        policy_id: "44444444-4444-4444-8444-444444444444", project_id: PROJECT_A, variable: "temperature",
        context_selector: {}, policy_type: "threshold", params: { high: 30, low: 10 }, priority: 1, enabled: true,
        policy_version: 2, source_asset_id: "55555555-5555-4555-8555-555555555555", source_asset_type: "sensor",
        source_asset_status: "online", source_asset_metadata: {}, binding_id: null, binding_enabled: null,
        binding_version: null, target_asset_id: null, target_asset_type: null, target_asset_status: null,
        target_asset_metadata: {}, control_point: null, operation: null
      });
      return { ...session(), status: "READY", prepared_at: "2026-08-21T01:00:00.000Z", ...material };
    })
  };
  const projectRepo = { findById: vi.fn().mockResolvedValue({ id: PROJECT_A, name: "Project A", parametric_control_enabled: true }) };
  return { service: new SimulationSessionService({ sessionRepo, projectRepo }), sessionRepo, projectRepo };
}

describe("SimulationSessionService", () => {
  it("creates a DRAFT simulation session only inside an operator project scope", async () => {
    const { service, sessionRepo } = subject();
    const created = await service.create(actor("operator"), PROJECT_A, { metadata: { purpose: "future replay" } });

    expect(created.execution_context).toBe("SIMULATION");
    expect(created.status).toBe("DRAFT");
    expect(sessionRepo.create).toHaveBeenCalledWith(PROJECT_A, "operator-actor", { metadata: { purpose: "future replay" } });
  });

  it("fails closed before accessing a session in another project", async () => {
    const { service, sessionRepo } = subject();
    await expect(service.get(actor("viewer", [PROJECT_A]), PROJECT_B, session().id)).rejects.toBeInstanceOf(ForbiddenError);
    expect(sessionRepo.findByProjectAndId).not.toHaveBeenCalled();
  });

  it("does not give an authenticated actor without membership implicit simulation access", async () => {
    const { service, sessionRepo } = subject();
    await expect(service.list(actor("viewer", []), PROJECT_A)).rejects.toBeInstanceOf(ForbiddenError);
    expect(sessionRepo.listByProject).not.toHaveBeenCalled();
  });

  it("requires a real project after scope authorization", async () => {
    const { service, projectRepo, sessionRepo } = subject();
    projectRepo.findById.mockResolvedValue(null);
    await expect(service.create(actor("operator"), PROJECT_A, {})).rejects.toBeInstanceOf(NotFoundError);
    expect(sessionRepo.create).not.toHaveBeenCalled();
  });

  it("prepares an immutable READY snapshot with deterministic component hashes", async () => {
    const { service, sessionRepo } = subject();
    const prepared = await service.prepare(actor("operator"), PROJECT_A, session().id, {
      policy_id: "44444444-4444-4444-8444-444444444444",
      dataset: { source_kind: "synthetic", records: [{
        event_id: "66666666-6666-4666-8666-666666666666", project_id: PROJECT_A, variable: "temperature",
        value: 24, timestamp: "2026-08-21T00:00:00+00:00", context: {}, metadata: {}, quality: "raw",
        source: "test", event_kind: "telemetry.observed"
      }] },
      configuration: { random_seed: 17, evaluation_options: { include_trace: true } }
    });
    expect(prepared.status).toBe("READY");
    expect(prepared.experiment_fingerprint).toMatch(/^[0-9a-f]{64}$/);
    expect(prepared.configuration_snapshot).toMatchObject({ operational_side_effects: { outbox: false, transport: false, physical_effects: false } });
    expect(sessionRepo.prepare).toHaveBeenCalledTimes(1);
  });

  it("rejects cross-project telemetry before preparation reaches the repository", async () => {
    const { service, sessionRepo } = subject();
    await expect(service.prepare(actor("operator"), PROJECT_A, session().id, {
      policy_id: "44444444-4444-4444-8444-444444444444",
      dataset: { source_kind: "historical", records: [{
        event_id: "66666666-6666-4666-8666-666666666666", project_id: PROJECT_B, variable: "temperature",
        value: 24, timestamp: "2026-08-21T00:00:00.000Z", context: {}, metadata: {}, quality: "raw", source: "test", event_kind: "telemetry.observed"
      }] }, configuration: {}
    })).rejects.toBeInstanceOf(ValidationError);
    expect(sessionRepo.prepare).not.toHaveBeenCalled();
  });
});
