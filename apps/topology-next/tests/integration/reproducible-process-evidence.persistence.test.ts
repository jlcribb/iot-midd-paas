import { afterEach, describe, expect, it } from "vitest";
import type { PoolClient } from "pg";
import { pool } from "@/lib/db/pool";
import { compareExperimentEvaluations, computeParetoFront } from "@/lib/comparison/experiment-comparison-engine";
import { evaluateExperiment } from "@/lib/evaluation/experiment-evaluator";
import { EvaluationProfileRepository } from "@/lib/repositories/evaluation-profile.repository";
import { ExperimentComparisonRepository } from "@/lib/repositories/experiment-comparison.repository";
import { ExperimentEvaluationRepository } from "@/lib/repositories/experiment-evaluation.repository";

const enabled = process.env.M63A_E2E_DB === "1";
const projectId = "00000000-0000-0000-0000-000000000001";
let client: PoolClient | undefined;
afterEach(async () => { if (client) { await client.query("ROLLBACK"); client.release(); client = undefined; } });

describe.runIf(enabled)("M6.3A persisted multidimensional evidence", () => {
  it("chains trace -> five KPIs -> evaluations -> TRADE_OFF -> Pareto inside one rollback", async () => {
    client = await pool.connect(); await client.query("BEGIN");
    const ids = { profile: "c4000000-0000-4000-8000-000000000001", session: "c1000000-0000-4000-8000-000000000001" };
    const metricRows = await client.query("SELECT id, code FROM public.control_evaluation_metrics WHERE code = ANY($1::text[]) AND version=1", [["tracking_error", "overshoot", "settling_time", "control_effort", "actuation_count"]]);
    await client.query("INSERT INTO public.control_simulation_sessions (id,project_id,execution_context,status,created_by) VALUES ($1::uuid,$2::uuid,'SIMULATION','DRAFT','m6.3a-e2e')", [ids.session, projectId]);
    await client.query("INSERT INTO public.control_evaluation_profiles (id,project_id,code,version,name,status,schema_version,metadata,created_by) VALUES ($1::uuid,$2::uuid,'m6_3a_multidimensional',1,'M6.3A multidimensional','ACTIVE',1,'{}'::jsonb,'m6.3a-e2e')", [ids.profile, projectId]);
    for (const metric of metricRows.rows) await client.query("INSERT INTO public.control_evaluation_profile_metrics (profile_id,metric_id,weight,required) VALUES ($1::uuid,$2::uuid,0.2,TRUE)", [ids.profile, metric.id]);
    const scenarios = [
      { key: "a", traceHash: "3d71d65a7dca63eb37d5c9d651f6483a467ffdca5be94416133ca9f49cde4094", values: [8, 9, 10, 10], controls: [3, 2, 1, 0] },
      { key: "b", traceHash: "9edcfd8bf72ed5ab4df51161c356a68d3bc4b87b7e19ce7e6b17460cd62a5aa6", values: [9, 9, 9, 9], controls: [0.5, 0.5, 0.5, 0.5] },
      { key: "c", traceHash: "5f4fb5467ca0032f6ab1e959c382ab3a3b397bbc48247ad7995a54b0d2d7a6ed", values: [10, 10, 10, 10], controls: [4, 4, 4, 4] }
    ];
    for (let index = 0; index < scenarios.length; index += 1) {
      const scenario = scenarios[index]; const suffix = String(index + 1).padStart(2, "0");
      const run = `c2000000-0000-4000-8000-0000000000${suffix}`; const result = `c3000000-0000-4000-8000-0000000000${suffix}`; const trace = `c5000000-0000-4000-8000-0000000000${suffix}`;
      await client.query("INSERT INTO public.control_simulation_runs (id,project_id,session_id,status,created_by,engine_version,replay_engine_version,clock_model_version,physical_effects_allowed,started_at,completed_at) VALUES ($1::uuid,$2::uuid,$3::uuid,'COMPLETED','m6.3a-e2e','control-engine:v1','simulation-replay:v1','simulation-clock:v1',FALSE,NOW(),NOW())", [run, projectId, ids.session]);
      await client.query("INSERT INTO public.control_simulation_results (id,project_id,session_id,run_id,experiment_fingerprint,result_fingerprint,processed_events,evaluation_count,recommendation_count,actionable_recommendation_count,recommendation_only_count,failed_domain_event_count,canonical_result_schema_version) VALUES ($1::uuid,$2::uuid,$3::uuid,$4::uuid,$5,$6,4,4,4,3,0,0,2)", [result, projectId, ids.session, run, `${scenario.key}`.repeat(64), `${scenario.key}`.repeat(64)]);
      await client.query("INSERT INTO public.control_simulation_traces (id,project_id,simulation_run_id,simulation_result_id,trace_schema_version,time_representation,trace_hash,point_count,simulation_duration_seconds,physical_effects_allowed) VALUES ($1::uuid,$2::uuid,$3::uuid,$4::uuid,1,'elapsed_seconds_from_first_virtual_timestamp:v1',$5,4,3,FALSE)", [trace, projectId, run, result, scenario.traceHash]);
      for (let point = 0; point < 4; point += 1) await client.query("INSERT INTO public.control_simulation_trace_points (trace_id,sequence_number,simulation_time_seconds,process_value,setpoint,control_output,actuator_state,metadata) VALUES ($1::uuid,$2,$3,$4,10,$5,$6,'{}'::jsonb)", [trace, point + 1, point, scenario.values[point], scenario.controls[point], scenario.controls[point] === 0 ? "HOLD" : "INCREASE"]);
    }
    const transaction = async <T>(work: (tx: PoolClient) => Promise<T>): Promise<T> => work(client as PoolClient);
    const profiles = new EvaluationProfileRepository(client, transaction); const evaluations = new ExperimentEvaluationRepository(client, transaction); const comparisons = new ExperimentComparisonRepository(client, transaction);
    const profile = await profiles.findByProjectAndId(projectId, ids.profile); expect(profile).not.toBeNull();
    const evaluated = [];
    for (const index of [1, 2, 3]) { const resultId = `c3000000-0000-4000-8000-0000000000${String(index).padStart(2, "0")}`; const result = await evaluations.findSimulationResult(projectId, resultId); expect(result?.trace?.point_count).toBe(4); expect(result?.trace?.trace_hash).toBe(scenarios[index - 1].traceHash); const evaluation = await evaluations.createOrGet(projectId, "m6.3a-e2e", { result: result!, profile: profile! }, evaluateExperiment({ result: result!, profile: profile! })); expect(evaluation.metrics.filter((metric) => metric.availability_status === "AVAILABLE")).toHaveLength(5); evaluated.push(evaluation); }
    const computation = compareExperimentEvaluations(evaluated[0], evaluated[1]);
    expect(computation.relation).toBe("TRADE_OFF");
    const comparison = await comparisons.createOrGet(projectId, "m6.3a-e2e", evaluated[0].id, evaluated[1].id, computation);
    expect(comparison.metrics).toHaveLength(5);
    const front = computeParetoFront(evaluated);
    expect(front.pareto_evaluation_ids.length).toBeGreaterThan(1);
    expect(front.excluded_evaluation_ids).toEqual([]);
    if (process.env.M63A_E2E_REPORT === "1") console.info(JSON.stringify({
      result_ids: evaluated.map((evaluation) => evaluation.simulation_result_id), trace_hashes: scenarios.map((scenario) => scenario.traceHash),
      evaluation_hashes: evaluated.map((evaluation) => evaluation.evaluation_hash), comparison_hash: comparison.comparison_hash,
      relation: comparison.relation, pareto_evaluation_ids: front.pareto_evaluation_ids
    }));
  });
});
