import type { EvaluationMetric } from "@/lib/dto/evaluation-profile.dto";

export const NORMALIZATION_ENGINE_VERSION = "evaluation-engine:v2";
export const EVALUATION_SCHEMA_VERSION = 1;
export const HASH_DECIMAL_PLACES = 9;

export function canonicalNumber(value: number): number {
  if (!Number.isFinite(value)) throw new TypeError("Evaluation values must be finite numbers");
  const rounded = Number(value.toFixed(HASH_DECIMAL_PLACES));
  return Object.is(rounded, -0) ? 0 : rounded;
}

function configNumber(config: Record<string, unknown>, key: string): number {
  const value = config[key];
  if (typeof value !== "number" || !Number.isFinite(value)) throw new TypeError(`Normalization config requires finite ${key}`);
  return value;
}

function clip(value: number): number { return Math.max(0, Math.min(1, value)); }

/** Pure, versioned normalization.  One means best observed compliance. */
export function normalizeMetric(metric: Pick<EvaluationMetric, "direction" | "normalization_method" | "normalization_config">, rawValue: number): number {
  if (!Number.isFinite(rawValue)) throw new TypeError("Raw KPI value must be finite");
  const config = metric.normalization_config;
  if (config.schema_version !== 1) throw new TypeError("Unsupported normalization config schema");

  if (metric.normalization_method === "MIN_MAX") {
    const best = configNumber(config, "best");
    const worst = configNumber(config, "worst");
    if (metric.direction === "MINIMIZE" && !(best < worst)) throw new TypeError("MINIMIZE normalization requires best < worst");
    if (metric.direction === "MAXIMIZE" && !(best > worst)) throw new TypeError("MAXIMIZE normalization requires best > worst");
    if (metric.direction !== "MINIMIZE" && metric.direction !== "MAXIMIZE") throw new TypeError("MIN_MAX requires MINIMIZE or MAXIMIZE direction");
    return canonicalNumber(clip((rawValue - worst) / (best - worst)));
  }

  if (metric.normalization_method === "TARGET_DISTANCE" && metric.direction === "TARGET") {
    const target = configNumber(config, "target");
    const tolerance = configNumber(config, "tolerance");
    const worstDistance = configNumber(config, "worst_distance");
    if (tolerance < 0 || worstDistance <= tolerance) throw new TypeError("TARGET normalization requires 0 <= tolerance < worst_distance");
    const distance = Math.abs(rawValue - target);
    return canonicalNumber(distance <= tolerance ? 1 : clip(1 - ((distance - tolerance) / (worstDistance - tolerance))));
  }

  if (metric.normalization_method === "RANGE_DISTANCE" && metric.direction === "RANGE") {
    const min = configNumber(config, "min");
    const max = configNumber(config, "max");
    const softMargin = configNumber(config, "soft_margin");
    if (!(min <= max) || softMargin <= 0) throw new TypeError("RANGE normalization requires min <= max and positive soft_margin");
    const distance = rawValue < min ? min - rawValue : rawValue > max ? rawValue - max : 0;
    return canonicalNumber(clip(1 - (distance / softMargin)));
  }

  throw new TypeError("Normalization method and metric direction are incompatible");
}
