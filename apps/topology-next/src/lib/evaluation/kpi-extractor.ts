import type { SimulationResultEvidence } from "@/lib/dto/experiment-evaluation.dto";

export type KpiAvailability = "AVAILABLE" | "MISSING" | "NOT_APPLICABLE" | "INVALID" | "NOT_AVAILABLE";
export interface RawKpi { status: KpiAvailability; value: number | null; reason: string | null; }

/**
 * M5 persists aggregate replay evidence, not process-value/setpoint/control
 * vectors.  Therefore only actuation_count is presently derivable without
 * inventing a proxy.  This extractor deliberately keeps the distinction.
 */
export function extractKpis(result: SimulationResultEvidence): ReadonlyMap<string, RawKpi> {
  const known = new Map<string, RawKpi>();
  known.set("actuation_count", { status: "AVAILABLE", value: result.actionable_recommendation_count, reason: null });
  return known;
}

export function kpiForMetric(result: SimulationResultEvidence, metricCode: string): RawKpi {
  return extractKpis(result).get(metricCode) ?? {
    status: "NOT_AVAILABLE", value: null,
    reason: "M5 result evidence does not contain the inputs needed to derive this KPI rigorously"
  };
}
