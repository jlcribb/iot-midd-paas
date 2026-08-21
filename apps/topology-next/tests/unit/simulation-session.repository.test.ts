import { describe, expect, it, vi } from "vitest";
import { SimulationSessionRepository } from "@/lib/repositories/simulation-session.repository";

const PROJECT = "11111111-1111-4111-8111-111111111111";
const SESSION = "22222222-2222-4222-8222-222222222222";
const POLICY = "33333333-3333-4333-8333-333333333333";

const draftRow = { id: SESSION, project_id: PROJECT, execution_context: "SIMULATION", status: "DRAFT", created_by: "operator", snapshot_refs: {}, metadata: {}, created_at: "2026-08-21T00:00:00.000Z", started_at: null, completed_at: null };
const policyRow = { policy_id: POLICY, project_id: PROJECT, variable: "temperature", context_selector: {}, policy_type: "threshold", params: { high: 30 }, priority: 1, enabled: true, policy_version: 1, source_asset_id: "44444444-4444-4444-8444-444444444444", source_asset_type: "sensor", source_asset_status: "online", source_asset_metadata: {}, binding_id: null, binding_enabled: null, binding_version: null, target_asset_id: null, target_asset_type: null, target_asset_status: null, target_asset_metadata: {}, control_point: null, operation: null };

const material = {
  policy_snapshot: { schema_version: 1 }, topology_snapshot: { schema_version: 1 }, dataset_snapshot: { schema_version: 1 }, configuration_snapshot: { schema_version: 1 },
  policy_snapshot_hash: "a".repeat(64), topology_snapshot_hash: "b".repeat(64), dataset_snapshot_hash: "c".repeat(64), configuration_snapshot_hash: "d".repeat(64), experiment_fingerprint: "e".repeat(64), snapshot_schema_version: 1
};

describe("SimulationSessionRepository.prepare", () => {
  it("locks DRAFT, materializes and audits READY in one SQL transaction", async () => {
    const query = vi.fn()
      .mockResolvedValueOnce({ rows: [draftRow] })
      .mockResolvedValueOnce({ rows: [policyRow] })
      .mockResolvedValueOnce({ rows: [{ ...draftRow, status: "READY", ...material, prepared_at: "2026-08-21T00:01:00.000Z" }] })
      .mockResolvedValueOnce({ rows: [] });
    const repository = new SimulationSessionRepository({} as never, async (work) => work({ query } as never));
    const prepared = await repository.prepare(PROJECT, SESSION, POLICY, "operator", () => material);

    expect(prepared.status).toBe("READY");
    expect(query.mock.calls[0][0]).toContain("FOR UPDATE");
    expect(query.mock.calls[1][0]).toContain("FOR SHARE OF p");
    expect(query.mock.calls[2][0]).toContain("SET status = 'READY'");
    expect(query.mock.calls[3][0]).toContain("SIMULATION_SESSION_PREPARED");
  });

  it("returns an already READY session without reading mutable policy or emitting another audit", async () => {
    const query = vi.fn().mockResolvedValue({ rows: [{ ...draftRow, status: "READY", ...material, prepared_at: "2026-08-21T00:01:00.000Z" }] });
    const repository = new SimulationSessionRepository({} as never, async (work) => work({ query } as never));
    const prepared = await repository.prepare(PROJECT, SESSION, POLICY, "operator", () => { throw new Error("must not rebuild"); });
    expect(prepared.experiment_fingerprint).toBe(material.experiment_fingerprint);
    expect(query).toHaveBeenCalledTimes(1);
  });
});
