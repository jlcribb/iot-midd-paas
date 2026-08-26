import { afterEach, describe, expect, it } from "vitest";
import type { PoolClient } from "pg";
import { pool } from "@/lib/db/pool";
import { evaluateExperiment } from "@/lib/evaluation/experiment-evaluator";
import { EvaluationProfileRepository } from "@/lib/repositories/evaluation-profile.repository";
import { ExperimentEvaluationRepository } from "@/lib/repositories/experiment-evaluation.repository";

const enabled = process.env.M6_E2E_DB === "1";
const projectId = "00000000-0000-0000-0000-000000000001";
const sessionId = "a1000000-0000-4000-8000-000000000001";
const runId = "a2000000-0000-4000-8000-000000000001";
const resultId = "a3000000-0000-4000-8000-000000000001";
const profileId = "a4000000-0000-4000-8000-000000000001";

let client: PoolClient | undefined;
afterEach(async () => { if (client) { await client.query("ROLLBACK"); client.release(); client = undefined; } });

describe.runIf(enabled)("M6.2 persisted evaluation against an M5 result", () => {
  it("derives, persists and idempotently reuses deterministic simulation evidence", async () => {
    client = await pool.connect();
    await client.query("BEGIN");
    const fingerprint = "a".repeat(64);
    const metric = await client.query("SELECT id FROM public.control_evaluation_metrics WHERE code='actuation_count' AND version=1");
    const metricId = String(metric.rows[0].id);
    await client.query(`INSERT INTO public.control_simulation_sessions (id, project_id, execution_context, status, created_by)
      VALUES ($1::uuid, $2::uuid, 'SIMULATION', 'DRAFT', 'm6-e2e')`, [sessionId, projectId]);
    await client.query(`INSERT INTO public.control_simulation_runs
      (id, project_id, session_id, status, created_by, engine_version, replay_engine_version, clock_model_version, physical_effects_allowed, started_at, completed_at)
      VALUES ($1::uuid, $2::uuid, $3::uuid, 'COMPLETED', 'm6-e2e', 'control-engine:v1', 'simulation-replay:v1', 'simulation-clock:v1', FALSE, NOW(), NOW())`, [runId, projectId, sessionId]);
    await client.query(`INSERT INTO public.control_simulation_results
      (id, project_id, session_id, run_id, experiment_fingerprint, result_fingerprint, processed_events, evaluation_count,
       recommendation_count, actionable_recommendation_count, recommendation_only_count, failed_domain_event_count, canonical_result_schema_version)
      VALUES ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5, $5, 10, 10, 10, 10, 0, 0, 1)`, [resultId, projectId, sessionId, runId, fingerprint]);
    await client.query(`INSERT INTO public.control_evaluation_profiles
      (id, project_id, code, version, name, status, schema_version, metadata, created_by)
      VALUES ($1::uuid, $2::uuid, 'm6_e2e_actuation', 1, 'M6 E2E actuation profile', 'ACTIVE', 1, '{}'::jsonb, 'm6-e2e')`, [profileId, projectId]);
    await client.query(`INSERT INTO public.control_evaluation_profile_metrics (profile_id, metric_id, weight, required)
      VALUES ($1::uuid, $2::uuid, 1, TRUE)`, [profileId, metricId]);

    const transaction = async <T>(work: (tx: PoolClient) => Promise<T>): Promise<T> => work(client as PoolClient);
    const profileRepository = new EvaluationProfileRepository(client, transaction);
    const evaluationRepository = new ExperimentEvaluationRepository(client, transaction);
    const [result, profile] = await Promise.all([
      evaluationRepository.findSimulationResult(projectId, resultId), profileRepository.findByProjectAndId(projectId, profileId)
    ]);
    expect(result).not.toBeNull();
    expect(profile).not.toBeNull();
    const computation = evaluateExperiment({ result: result!, profile: profile! });
    expect(computation).toMatchObject({ status: "COMPLETED", score: 0.9, constraint_violated_count: 0 });
    const first = await evaluationRepository.createOrGet(projectId, "m6-e2e", { result: result!, profile: profile! }, computation);
    const repeated = await evaluationRepository.createOrGet(projectId, "m6-e2e", { result: result!, profile: profile! }, evaluateExperiment({ result: result!, profile: profile! }));
    expect(repeated.id).toBe(first.id);
    expect(repeated.evaluation_hash).toBe(first.evaluation_hash);
    expect(repeated.metrics).toHaveLength(1);
    const audit = await client.query("SELECT count(*)::int AS count FROM iot_schema.auditoria WHERE entidad='control_experiment_evaluations' AND entidad_id=$1::uuid", [first.id]);
    expect(audit.rows[0].count).toBe(1);
  });
});
