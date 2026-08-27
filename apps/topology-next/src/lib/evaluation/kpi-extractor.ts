import type { SimulationResultEvidence, SimulationTraceEvidence } from "@/lib/dto/experiment-evaluation.dto";

export type KpiAvailability = "AVAILABLE" | "MISSING" | "NOT_APPLICABLE" | "INVALID" | "NOT_AVAILABLE";
export interface RawKpi { status: KpiAvailability; value: number | null; reason: string | null; }
export const KPI_EXTRACTION_ENGINE_VERSION = "kpi-extractor:v2";
export const KPI_DEFINITIONS = {
  tracking_error: { version: "tracking_error:v1", unit: "controlled-unit MAE", requires: ["process_value", "setpoint"] },
  overshoot: { version: "overshoot:v1", unit: "controlled-unit", requires: ["process_value", "setpoint"] },
  undershoot: { version: "undershoot:v1", unit: "controlled-unit", requires: ["process_value", "setpoint"] },
  settling_time: { version: "settling_time:v1", unit: "seconds", requires: ["process_value", "setpoint"], band_absolute: 1 },
  control_effort: { version: "control_effort:v1", unit: "control-unit seconds", requires: ["control_output", "simulation_time_seconds"] },
  actuation_count: { version: "actuation_count:v2", unit: "count", requires: ["actuator_state"] }
} as const;

const unavailable = (reason: string): RawKpi => ({ status: "NOT_AVAILABLE", value: null, reason });
function traceFor(result: SimulationResultEvidence, metric: string): SimulationTraceEvidence | null {
  if (!result.trace) return null;
  if (result.trace.point_count !== result.trace.points.length || result.trace.points.length === 0) return null;
  const points = result.trace.points;
  if (points.some((point, index) => point.sequence_number !== index + 1 || !Number.isFinite(point.simulation_time_seconds) || !Number.isFinite(point.process_value) || !Number.isFinite(point.setpoint) || !Number.isFinite(point.control_output) || (index > 0 && point.simulation_time_seconds < points[index - 1].simulation_time_seconds))) return null;
  return result.trace;
}
function available(value: number): RawKpi { return Number.isFinite(value) ? { status: "AVAILABLE", value: Number(value.toFixed(9)), reason: null } : unavailable("Trace extraction produced a non-finite value"); }
function extraction(result: SimulationResultEvidence, metric: string, fn: (trace: SimulationTraceEvidence) => number): RawKpi {
  const trace = traceFor(result, metric); return trace ? available(fn(trace)) : unavailable(`${metric}:v1 requires complete immutable simulation trace evidence`);
}
function effort(trace: SimulationTraceEvidence): number { return trace.points.reduce((total, point, index) => index === 0 ? total : total + Math.abs(point.control_output) * (point.simulation_time_seconds - trace.points[index - 1].simulation_time_seconds), 0); }
function settling(trace: SimulationTraceEvidence): number {
  const band = KPI_DEFINITIONS.settling_time.band_absolute;
  for (let index = 0; index < trace.points.length; index += 1) {
    if (trace.points.slice(index).every((point) => Math.abs(point.process_value - point.setpoint) <= band)) return trace.points[index].simulation_time_seconds;
  }
  return trace.simulation_duration_seconds;
}

/** Deterministic registry over immutable trace evidence; never interpolates or mutates a result. */
export function extractKpis(result: SimulationResultEvidence): ReadonlyMap<string, RawKpi> {
  const known = new Map<string, RawKpi>();
  known.set("tracking_error", extraction(result, "tracking_error", (trace) => trace.points.reduce((sum, point) => sum + Math.abs(point.setpoint - point.process_value), 0) / trace.points.length));
  known.set("overshoot", extraction(result, "overshoot", (trace) => Math.max(0, ...trace.points.map((point) => point.process_value - point.setpoint))));
  known.set("undershoot", extraction(result, "undershoot", (trace) => Math.max(0, ...trace.points.map((point) => point.setpoint - point.process_value))));
  known.set("settling_time", extraction(result, "settling_time", settling));
  known.set("control_effort", extraction(result, "control_effort", effort));
  const trace = traceFor(result, "actuation_count");
  known.set("actuation_count", trace ? available(trace.points.filter((point) => point.actuator_state !== "HOLD").length) : { status: "AVAILABLE", value: result.actionable_recommendation_count, reason: "M6.2 aggregate fallback for historical results without trace" });
  return known;
}
export function kpiForMetric(result: SimulationResultEvidence, metricCode: string): RawKpi { return extractKpis(result).get(metricCode) ?? unavailable(`${metricCode} has no versioned extractor backed by stored trace evidence`); }
