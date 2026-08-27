import { afterEach, describe, expect, it } from "vitest";
import type { PoolClient } from "pg";
import { pool } from "@/lib/db/pool";
import { compareExperimentEvaluations } from "@/lib/comparison/experiment-comparison-engine";
import { evaluateExperiment } from "@/lib/evaluation/experiment-evaluator";
import { EvaluationProfileRepository } from "@/lib/repositories/evaluation-profile.repository";
import { ExperimentComparisonRepository } from "@/lib/repositories/experiment-comparison.repository";
import { ExperimentEvaluationRepository } from "@/lib/repositories/experiment-evaluation.repository";

const enabled = process.env.M6_E2E_DB === "1";
const projectId = "00000000-0000-0000-0000-000000000001";
let client: PoolClient | undefined;
afterEach(async () => { if (client) { await client.query("ROLLBACK"); client.release(); client = undefined; } });

describe.runIf(enabled)("M6.3 persisted comparison against M6.2 evidence", () => {
  it("persists one directional comparison and immutable evidence without retaining fixtures", async () => {
    client = await pool.connect(); await client.query("BEGIN");
    const ids = { sessionA: "b1000000-0000-4000-8000-000000000001", sessionB: "b1000000-0000-4000-8000-000000000002", runA: "b2000000-0000-4000-8000-000000000001", runB: "b2000000-0000-4000-8000-000000000002", resultA: "b3000000-0000-4000-8000-000000000001", resultB: "b3000000-0000-4000-8000-000000000002", profile: "b4000000-0000-4000-8000-000000000001" };
    const metric = await client.query("SELECT id FROM public.control_evaluation_metrics WHERE code='actuation_count' AND version=1");
    const metricId = String(metric.rows[0].id); const fingerprint = "b".repeat(64);
    for (const [session, run, result, actionable] of [[ids.sessionA, ids.runA, ids.resultA, 20], [ids.sessionB, ids.runB, ids.resultB, 5]] as const) {
      await client.query("INSERT INTO public.control_simulation_sessions (id,project_id,execution_context,status,created_by) VALUES ($1::uuid,$2::uuid,'SIMULATION','DRAFT','m6.3-e2e')", [session, projectId]);
      await client.query("INSERT INTO public.control_simulation_runs (id,project_id,session_id,status,created_by,engine_version,replay_engine_version,clock_model_version,physical_effects_allowed,started_at,completed_at) VALUES ($1::uuid,$2::uuid,$3::uuid,'COMPLETED','m6.3-e2e','control-engine:v1','simulation-replay:v1','simulation-clock:v1',FALSE,NOW(),NOW())", [run, projectId, session]);
      await client.query("INSERT INTO public.control_simulation_results (id,project_id,session_id,run_id,experiment_fingerprint,result_fingerprint,processed_events,evaluation_count,recommendation_count,actionable_recommendation_count,recommendation_only_count,failed_domain_event_count,canonical_result_schema_version) VALUES ($1::uuid,$2::uuid,$3::uuid,$4::uuid,$5,$6,$7,$7,$7,$7,0,0,1)", [result, projectId, session, run, fingerprint, `${actionable}`.padStart(64, "b"), actionable]);
    }
    await client.query("INSERT INTO public.control_evaluation_profiles (id,project_id,code,version,name,status,schema_version,metadata,created_by) VALUES ($1::uuid,$2::uuid,'m6_3_e2e',1,'M6.3 E2E','ACTIVE',1,'{}'::jsonb,'m6.3-e2e')", [ids.profile, projectId]);
    await client.query("INSERT INTO public.control_evaluation_profile_metrics (profile_id,metric_id,weight,required) VALUES ($1::uuid,$2::uuid,1,TRUE)", [ids.profile, metricId]);
    const transaction = async <T>(work: (tx: PoolClient) => Promise<T>): Promise<T> => work(client as PoolClient);
    const profiles = new EvaluationProfileRepository(client, transaction); const evaluations = new ExperimentEvaluationRepository(client, transaction); const comparisons = new ExperimentComparisonRepository(client, transaction);
    const profile = await profiles.findByProjectAndId(projectId, ids.profile); expect(profile).not.toBeNull();
    const makeEvaluation = async (resultId: string) => { const result = await evaluations.findSimulationResult(projectId, resultId); expect(result).not.toBeNull(); return evaluations.createOrGet(projectId, "m6.3-e2e", { result: result!, profile: profile! }, evaluateExperiment({ result: result!, profile: profile! })); };
    const baseline = await makeEvaluation(ids.resultA); const candidate = await makeEvaluation(ids.resultB);
    const computation = compareExperimentEvaluations(baseline, candidate);
    expect(computation).toMatchObject({ relation: "BETTER", candidate_dominates_baseline: true, coverage_ratio: 1 });
    const first = await comparisons.createOrGet(projectId, "m6.3-e2e", baseline.id, candidate.id, computation);
    const repeated = await comparisons.createOrGet(projectId, "m6.3-e2e", baseline.id, candidate.id, compareExperimentEvaluations(baseline, candidate));
    expect(repeated.id).toBe(first.id); expect(first.metrics).toHaveLength(1); expect(first.physical_effects_allowed).toBe(false);
    const audit = await client.query("SELECT count(*)::int AS count FROM iot_schema.auditoria WHERE entidad='control_experiment_comparisons' AND entidad_id=$1::uuid", [first.id]);
    expect(audit.rows[0].count).toBe(1);
  });
});
