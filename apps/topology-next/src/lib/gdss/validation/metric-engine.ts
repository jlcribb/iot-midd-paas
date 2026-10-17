import { MetricFoundationError } from "./metric-diagnostics";
import {
  metricKeys,
  type ComparisonRule,
  type MetricDefinitionContent,
  type MetricKey,
  type UncertaintyKnowledgeState,
} from "./metric-contracts";
export type MetricPoint = {
  prediction: number;
  observation: number;
  predictionTime?: number;
  observationTime?: number;
  lower?: number;
  upper?: number;
};
export const FLOATING_POINT_POLICY = {
  representation: "IEEE_754_BINARY64",
  nan: "REJECT",
  infinity: "REJECT",
  negativeZero: "NORMALIZE_TO_POSITIVE_ZERO",
  rounding: "PRESENTATION_ONLY",
} as const;
const finite = (n: number) => {
  if (!Number.isFinite(n))
    throw new MetricFoundationError("METRIC_INPUT_INVALID");
  return Object.is(n, -0) ? 0 : n;
};
export function assertMetricDefinition(v: MetricDefinitionContent) {
  if (!metricKeys.includes(v.metricKey))
    throw new MetricFoundationError("METRIC_NOT_ALLOWED");
  const category: Record<MetricKey, MetricDefinitionContent["category"]> = {
    MAE_V1: "POINT_ERROR",
    RMSE_V1: "POINT_ERROR",
    BIAS_V1: "POINT_ERROR",
    SMAPE_V1: "RELATIVE_ERROR",
    TRAJECTORY_RMSE_V1: "TRAJECTORY",
    PEAK_MAGNITUDE_ERROR_V1: "DYNAMIC_RESPONSE",
    PEAK_TIMING_ERROR_V1: "DYNAMIC_RESPONSE",
    STEADY_STATE_DEVIATION_V1: "DYNAMIC_RESPONSE",
    INTERVAL_COVERAGE_V1: "INTERVAL",
    MEAN_INTERVAL_WIDTH_V1: "INTERVAL",
  };
  if (v.category !== category[v.metricKey])
    throw new MetricFoundationError(
      "METRIC_INPUT_INVALID",
      "Metric category does not match allowlist contract",
    );
}
export function computeMetric(
  key: MetricKey,
  points: MetricPoint[],
  definition: MetricDefinitionContent,
): number {
  assertMetricDefinition(definition);
  if (!points.length) throw new MetricFoundationError("METRIC_INPUT_INVALID");
  for (const p of points) {
    finite(p.prediction);
    finite(p.observation);
  }
  let result: number;
  switch (key) {
    case "MAE_V1":
      result =
        points.reduce((s, p) => s + Math.abs(p.prediction - p.observation), 0) /
        points.length;
      break;
    case "RMSE_V1":
    case "TRAJECTORY_RMSE_V1":
      result = Math.sqrt(
        points.reduce((s, p) => s + (p.prediction - p.observation) ** 2, 0) /
          points.length,
      );
      break;
    case "BIAS_V1":
      result =
        points.reduce((s, p) => s + (p.prediction - p.observation), 0) /
        points.length;
      break;
    case "SMAPE_V1": {
      const floor = definition.smapeDenominatorFloor!;
      result =
        points.reduce((s, p) => {
          if (p.prediction === 0 && p.observation === 0) return s;
          return (
            s +
            (2 * Math.abs(p.prediction - p.observation)) /
              Math.max(Math.abs(p.prediction) + Math.abs(p.observation), floor)
          );
        }, 0) / points.length;
      break;
    }
    case "PEAK_MAGNITUDE_ERROR_V1":
      result = Math.abs(
        Math.max(...points.map((p) => p.prediction)) -
          Math.max(...points.map((p) => p.observation)),
      );
      break;
    case "PEAK_TIMING_ERROR_V1": {
      const pp = points.reduce((a, p) => (p.prediction > a.prediction ? p : a)),
        op = points.reduce((a, p) => (p.observation > a.observation ? p : a)),
        delta =
          ((pp.predictionTime ?? NaN) - (op.observationTime ?? NaN)) / 1000;
      result = definition.peakTimingSigned ? delta : Math.abs(delta);
      break;
    }
    case "STEADY_STATE_DEVIATION_V1": {
      const n = definition.steadyStateWindowCount!,
        tail = points.slice(-n);
      if (tail.length < n)
        throw new MetricFoundationError("METRIC_INPUT_INVALID");
      if (
        Math.max(...tail.map((p) => p.observation)) -
          Math.min(...tail.map((p) => p.observation)) >
        definition.steadyStateTolerance!
      )
        throw new MetricFoundationError(
          "METRIC_INPUT_INVALID",
          "Declared steady-state tolerance not satisfied",
        );
      result = tail.reduce((s, p) => s + (p.prediction - p.observation), 0) / n;
      break;
    }
    case "INTERVAL_COVERAGE_V1":
      if (points.some((p) => p.lower === undefined || p.upper === undefined))
        throw new MetricFoundationError("METRIC_INPUT_INVALID");
      result =
        points.filter(
          (p) => p.observation >= p.lower! && p.observation <= p.upper!,
        ).length / points.length;
      break;
    case "MEAN_INTERVAL_WIDTH_V1":
      if (points.some((p) => p.lower === undefined || p.upper === undefined))
        throw new MetricFoundationError("METRIC_INPUT_INVALID");
      result =
        points.reduce((s, p) => s + p.upper! - p.lower!, 0) / points.length;
      break;
  }
  return finite(result);
}
export function compareMetric(
  model: number,
  baseline: number,
  rule: ComparisonRule,
) {
  if (!Number.isFinite(model) || !Number.isFinite(baseline))
    return "INCONCLUSIVE" as const;
  const raw =
    rule.directionality === "HIGHER_IS_BETTER"
      ? model - baseline
      : rule.directionality === "CLOSER_TO_ZERO_IS_BETTER"
        ? Math.abs(baseline) - Math.abs(model)
        : baseline - model;
  if (Math.abs(raw) <= rule.tolerance)
    return "MODEL_EQUIVALENT_TO_BASELINE" as const;
  return raw > 0
    ? ("MODEL_OUTPERFORMS_BASELINE" as const)
    : ("MODEL_UNDERPERFORMS_BASELINE" as const);
}
export function uncertaintyCompleteness(states: UncertaintyKnowledgeState[]) {
  if (!states.length || states.every((x) => x === "UNKNOWN"))
    return "UNKNOWN" as const;
  if (states.some((x) => x === "UNKNOWN")) return "INSUFFICIENT" as const;
  if (states.some((x) => x === "KNOWN_UNQUANTIFIED")) return "PARTIAL" as const;
  return "COMPLETE_FOR_DECLARED_SCOPE" as const;
}
