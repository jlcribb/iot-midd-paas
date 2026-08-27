import { describe, expect, it } from "vitest";
import { extractKpis } from "@/lib/evaluation/kpi-extractor";
import type { SimulationResultEvidence } from "@/lib/dto/experiment-evaluation.dto";

function evidence(): SimulationResultEvidence { return { id: "11111111-1111-4111-8111-111111111111", project_id: "22222222-2222-4222-8222-222222222222", session_id: "33333333-3333-4333-8333-333333333333", run_id: "44444444-4444-4444-8444-444444444444", result_fingerprint: "a".repeat(64), processed_events: 3, actionable_recommendation_count: 2, failed_domain_event_count: 0, trace: { trace_hash: "b".repeat(64), trace_schema_version: 1, time_representation: "elapsed_seconds_from_first_virtual_timestamp:v1", point_count: 3, simulation_duration_seconds: 2, points: [
  { sequence_number: 1, simulation_time_seconds: 0, process_value: 8, setpoint: 10, control_output: 1, actuator_state: "INCREASE", constraint_state: null },
  { sequence_number: 2, simulation_time_seconds: 1, process_value: 10, setpoint: 10, control_output: 2, actuator_state: "HOLD", constraint_state: null },
  { sequence_number: 3, simulation_time_seconds: 2, process_value: 11, setpoint: 10, control_output: -1, actuator_state: "DECREASE", constraint_state: null }
] } }; }

describe("M6.3A trace-backed KPI extraction", () => {
  it("derives documented independent KPIs from immutable points", () => {
    const values = extractKpis(evidence());
    expect(values.get("tracking_error")).toMatchObject({ status: "AVAILABLE", value: 1 });
    expect(values.get("overshoot")).toMatchObject({ status: "AVAILABLE", value: 1 });
    expect(values.get("undershoot")).toMatchObject({ status: "AVAILABLE", value: 2 });
    expect(values.get("settling_time")).toMatchObject({ status: "AVAILABLE", value: 1 });
    expect(values.get("control_effort")).toMatchObject({ status: "AVAILABLE", value: 3 });
    expect(values.get("actuation_count")).toMatchObject({ status: "AVAILABLE", value: 2 });
  });
  it("does not convert missing trace evidence into zero", () => {
    const result = evidence(); result.trace = null;
    expect(extractKpis(result).get("tracking_error")).toMatchObject({ status: "NOT_AVAILABLE", value: null });
    expect(extractKpis(result).get("actuation_count")).toMatchObject({ status: "AVAILABLE", value: 2 });
  });
});
