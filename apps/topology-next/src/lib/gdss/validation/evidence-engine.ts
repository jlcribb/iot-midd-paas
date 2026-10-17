import type { DomainPredicate } from "./contracts";
import type {
  DomainContextSnapshot,
  StrengthAxis,
  StrengthState,
  SupportDimension,
} from "./evidence-contracts";
import { PredictiveEvidenceError } from "./evidence-diagnostics";

export type PredicateAssessment = {
  predicateKey: string;
  result: "PASS" | "BOUNDARY" | "FAIL" | "UNKNOWN";
  reason: string;
};

export function evaluateDomain(
  predicates: DomainPredicate[],
  context: DomainContextSnapshot,
) {
  const byKey = new Map(
    context.values.map((value) => [value.variableKey, value]),
  );
  const assessments: PredicateAssessment[] = predicates.map((predicate) => {
    const value = byKey.get(predicate.variableKey);
    if (!value)
      return {
        predicateKey: predicate.predicateKey,
        result: "UNKNOWN" as const,
        reason: "CONTEXT_VALUE_MISSING",
      };
    try {
      if (
        predicate.predicateType === "NUMERIC_RANGE" ||
        predicate.predicateType === "PARAMETER_RANGE"
      ) {
        if (
          value.kind !== "NUMERIC" ||
          !predicate.unit ||
          value.unit.key !== predicate.unit.key ||
          value.unit.revision !== predicate.unit.revision
        )
          return {
            predicateKey: predicate.predicateKey,
            result: "UNKNOWN",
            reason: "TYPE_OR_UNIT_MISMATCH",
          };
        const lowerPass = predicate.lowerInclusive
          ? value.value >= predicate.lowerBound
          : value.value > predicate.lowerBound;
        const upperPass = predicate.upperInclusive
          ? value.value <= predicate.upperBound
          : value.value < predicate.upperBound;
        if (!lowerPass || !upperPass)
          return {
            predicateKey: predicate.predicateKey,
            result: "FAIL",
            reason: "OUTSIDE_RANGE",
          };
        const boundary =
          (predicate.lowerInclusive && value.value === predicate.lowerBound) ||
          (predicate.upperInclusive && value.value === predicate.upperBound);
        return {
          predicateKey: predicate.predicateKey,
          result: boundary ? "BOUNDARY" : "PASS",
          reason: boundary ? "EXACT_DECLARED_BOUNDARY" : "WITHIN_RANGE",
        };
      }
      if (predicate.predicateType === "TEMPORAL_RANGE") {
        if (value.kind !== "TEMPORAL")
          return {
            predicateKey: predicate.predicateKey,
            result: "UNKNOWN",
            reason: "TYPE_MISMATCH",
          };
        const point = BigInt(value.epochMicros),
          start = BigInt(predicate.startEpochMicros),
          end = BigInt(predicate.endEpochMicros);
        if (point < start || point > end)
          return {
            predicateKey: predicate.predicateKey,
            result: "FAIL",
            reason: "OUTSIDE_TEMPORAL_RANGE",
          };
        return {
          predicateKey: predicate.predicateKey,
          result: point === start || point === end ? "BOUNDARY" : "PASS",
          reason:
            point === start || point === end
              ? "EXACT_DECLARED_BOUNDARY"
              : "WITHIN_TEMPORAL_RANGE",
        };
      }
      if (predicate.predicateType === "CATEGORICAL_MEMBERSHIP") {
        if (value.kind !== "CATEGORICAL")
          return {
            predicateKey: predicate.predicateKey,
            result: "UNKNOWN",
            reason: "TYPE_MISMATCH",
          };
        return {
          predicateKey: predicate.predicateKey,
          result: predicate.allowedValues.includes(value.value)
            ? "PASS"
            : "FAIL",
          reason: predicate.allowedValues.includes(value.value)
            ? "EXACT_MEMBER"
            : "NOT_MEMBER",
        };
      }
      if (value.kind !== "BOOLEAN")
        return {
          predicateKey: predicate.predicateKey,
          result: "UNKNOWN",
          reason: "TYPE_MISMATCH",
        };
      return {
        predicateKey: predicate.predicateKey,
        result: value.value === predicate.expected ? "PASS" : "FAIL",
        reason:
          value.value === predicate.expected
            ? "BOOLEAN_MATCH"
            : "BOOLEAN_MISMATCH",
      };
    } catch {
      throw new PredictiveEvidenceError("DOMAIN_PREDICATE_EVALUATION_FAILED");
    }
  });
  const result = assessments.some((item) => item.result === "UNKNOWN")
    ? "DOMAIN_UNKNOWN"
    : assessments.some((item) => item.result === "FAIL")
      ? "OUTSIDE_VALIDITY_DOMAIN"
      : assessments.some((item) => item.result === "BOUNDARY")
        ? "NEAR_DOMAIN_BOUNDARY"
        : "WITHIN_VALIDITY_DOMAIN";
  return { result, assessments } as const;
}

export function assessPosition(
  domainResult: string,
  context: DomainContextSnapshot,
  support: SupportDimension[],
) {
  if (domainResult === "DOMAIN_UNKNOWN") return "UNKNOWN_POSITION" as const;
  if (domainResult === "OUTSIDE_VALIDITY_DOMAIN")
    return "EXTRAPOLATION" as const;
  const byKey = new Map(
    context.values.map((value) => [value.variableKey, value]),
  );
  let boundary = domainResult === "NEAR_DOMAIN_BOUNDARY";
  for (const dimension of support) {
    const value = byKey.get(dimension.variableKey);
    if (!value) return "UNKNOWN_POSITION" as const;
    if (dimension.kind === "NUMERIC_RANGE") {
      if (
        value.kind !== "NUMERIC" ||
        value.unit.key !== dimension.unit.key ||
        value.unit.revision !== dimension.unit.revision
      )
        return "UNKNOWN_POSITION" as const;
      if (
        value.value < dimension.lowerBound ||
        value.value > dimension.upperBound
      )
        return "EXTRAPOLATION" as const;
      boundary ||=
        value.value === dimension.lowerBound ||
        value.value === dimension.upperBound;
    } else if (dimension.kind === "TEMPORAL_RANGE") {
      if (value.kind !== "TEMPORAL") return "UNKNOWN_POSITION" as const;
      const point = BigInt(value.epochMicros),
        start = BigInt(dimension.startEpochMicros),
        end = BigInt(dimension.endEpochMicros);
      if (point < start || point > end) return "EXTRAPOLATION" as const;
      boundary ||= point === start || point === end;
    } else if (dimension.kind === "CATEGORICAL_SET") {
      if (value.kind !== "CATEGORICAL") return "UNKNOWN_POSITION" as const;
      if (!dimension.values.includes(value.value))
        return "EXTRAPOLATION" as const;
    } else {
      if (value.kind !== "BOOLEAN") return "UNKNOWN_POSITION" as const;
      if (!dimension.values.includes(value.value))
        return "EXTRAPOLATION" as const;
    }
  }
  return boundary
    ? ("BOUNDARY_PREDICTION" as const)
    : ("INTERPOLATION" as const);
}

export function validateStrengthAxes<
  T extends { axis: StrengthAxis; state: StrengthState },
>(axes: T[]): T[] {
  const required: StrengthAxis[] = [
    "INDEPENDENCE",
    "TEMPORALITY",
    "DOMAIN_COVERAGE",
    "UNCERTAINTY_COMPLETENESS",
    "BASELINE_STRENGTH",
    "REPLICATION",
    "DATA_QUALITY",
  ];
  if (
    axes.length !== required.length ||
    new Set(axes.map((item) => item.axis)).size !== required.length ||
    required.some((axis) => !axes.some((item) => item.axis === axis))
  )
    throw new PredictiveEvidenceError("EVIDENCE_STRENGTH_AXIS_INVALID");
  return [...axes].sort((a, b) => a.axis.localeCompare(b.axis));
}
