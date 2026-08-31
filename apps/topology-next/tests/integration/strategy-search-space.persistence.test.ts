import { afterEach, describe, expect, it } from "vitest";
import type { PoolClient } from "pg";
import { pool } from "@/lib/db/pool";
import { StrategySearchSpaceRepository } from "@/lib/repositories/strategy-search-space.repository";
import { generateGridSearch } from "@/lib/strategy/candidate-generator";

const enabled = process.env.M64_E2E_DB === "1";
const projectId = "00000000-0000-0000-0000-000000000001";
let client: PoolClient | undefined;
afterEach(async () => { if (client) { await client.query("ROLLBACK"); client.release(); client = undefined; } });

function repository(): StrategySearchSpaceRepository {
  const transaction = async <T>(work: (tx: PoolClient) => Promise<T>): Promise<T> => work(client as PoolClient);
  return new StrategySearchSpaceRepository(client as PoolClient, transaction);
}

describe.runIf(enabled)("M6.4 transactional Grid search-space persistence", () => {
  it("persists proportional, threshold and invalid-summary evidence idempotently", async () => {
    client = await pool.connect(); await client.query("BEGIN");
    const repo = repository();
    const proportional = { name: "M64 proportional", strategy_type: "proportional" as const, generation_method: "GRID" as const, parameters: { gain: { values: [0.1, 0.2, 0.3] }, setpoint_value: { values: [50, 60] } } };
    const first = await repo.createOrGet(projectId, "m64-e2e", proportional, generateGridSearch(proportional.strategy_type, proportional.parameters));
    const repeated = await repo.createOrGet(projectId, "m64-e2e", { ...proportional, name: "Different display name" }, generateGridSearch(proportional.strategy_type, proportional.parameters));
    expect(first.id).toBe(repeated.id); expect(first.candidate_count).toBe(6);
    const candidates = await repo.listCandidates(projectId, first.id);
    expect(candidates.map((item) => item.candidate_index)).toEqual([1, 2, 3, 4, 5, 6]);
    await client.query("SAVEPOINT m64_after_immutable");
    await expect(client.query("UPDATE public.control_strategy_search_spaces SET name='mutated' WHERE id=$1::uuid", [first.id])).rejects.toThrow(/immutable/);
    await client.query("ROLLBACK TO SAVEPOINT m64_after_immutable");
    const threshold = { name: "M64 threshold", strategy_type: "threshold" as const, generation_method: "GRID" as const, parameters: { tolerance: { values: [0, 0.5] }, increase_step: { values: [1] }, decrease_step: { values: [1, 2] } } };
    expect((await repo.createOrGet(projectId, "m64-e2e", threshold, generateGridSearch(threshold.strategy_type, threshold.parameters))).candidate_count).toBe(4);
    const constrained = { name: "M64 bounded", strategy_type: "proportional" as const, generation_method: "GRID" as const, parameters: { gain: { values: [1] }, setpoint_value: { values: [50] }, min_action: { values: [1, 3] }, max_action: { values: [2, 4] } } };
    const constrainedSpace = await repo.createOrGet(projectId, "m64-e2e", constrained, generateGridSearch(constrained.strategy_type, constrained.parameters));
    expect(constrainedSpace).toMatchObject({ raw_combination_count: 4, candidate_count: 3, invalid_combination_count: 1 });
    const audit = await client.query("SELECT count(*)::int AS count FROM iot_schema.auditoria WHERE entidad='control_strategy_search_spaces' AND entidad_id=$1::uuid", [first.id]);
    expect(audit.rows[0].count).toBe(1);
    if (process.env.M64_E2E_REPORT === "1") console.info(`M64_E2E=PASS proportional_candidates=${first.candidate_count} threshold_candidates=4 constrained_valid=3 constrained_invalid=1 search_space_hash=${first.search_space_hash} candidate_hash=${candidates[0].candidate_hash}`);
  });

  it("rolls back the parent when candidate persistence fails", async () => {
    client = await pool.connect(); await client.query("BEGIN");
    await client.query("CREATE FUNCTION pg_temp.m64_reject_candidate() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'm64 injected candidate failure'; END; $$ LANGUAGE plpgsql");
    await client.query("CREATE TRIGGER m64_reject_candidate BEFORE INSERT ON public.control_strategy_candidates FOR EACH ROW EXECUTE FUNCTION pg_temp.m64_reject_candidate()");
    const input = { name: "M64 rollback", strategy_type: "proportional" as const, generation_method: "GRID" as const, parameters: { gain: { values: [1] }, setpoint_value: { values: [50] } } };
    const generated = generateGridSearch(input.strategy_type, input.parameters);
    const transaction = async <T>(work: (tx: PoolClient) => Promise<T>): Promise<T> => { await client!.query("SAVEPOINT m64_atomic"); try { const value = await work(client!); await client!.query("RELEASE SAVEPOINT m64_atomic"); return value; } catch (error) { await client!.query("ROLLBACK TO SAVEPOINT m64_atomic"); throw error; } };
    const repo = new StrategySearchSpaceRepository(client, transaction);
    await expect(repo.createOrGet(projectId, "m64-e2e", input, generated)).rejects.toThrow("m64 injected candidate failure");
    const searchSpaces = await client.query("SELECT count(*)::int AS count FROM public.control_strategy_search_spaces WHERE project_id=$1::uuid AND search_space_hash=$2", [projectId, generated.search_space_hash]);
    expect(searchSpaces.rows[0].count).toBe(0);
  });
});
