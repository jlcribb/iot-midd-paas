import type {
  CapabilityScope,
  CapabilityState,
  ClaimState,
  RevalidationTriggerType,
} from "./capability-contracts";
import { CapabilityClaimError } from "./capability-diagnostics";
import type { StrengthAxis, StrengthState } from "./evidence-contracts";

type Axis = { axis: StrengthAxis; state: StrengthState; evidence?: unknown };
type CapabilityFacts = {
  requestedAction: "REGISTER_SCOPE" | "EVALUATE";
  completeness: string;
  axes: Axis[];
  conflictCount: number;
  invalidatingCount: number;
  negativeFindingTypes: string[];
};

const axisState = (axes: Axis[], axis: StrengthAxis) =>
  axes.find((item) => item.axis === axis)?.state ?? "UNKNOWN";

export function deriveCapabilityState(facts: CapabilityFacts): {
  state: CapabilityState;
  rationaleCode: string;
  axisExplanation: Axis[];
} {
  if (facts.requestedAction === "REGISTER_SCOPE")
    return {
      state: "NOT_EVALUATED",
      rationaleCode: "SCOPE_REGISTERED_WITHOUT_EVALUATION",
      axisExplanation: facts.axes,
    };
  if (facts.completeness !== "COMPLETE")
    return {
      state: "INSUFFICIENT_EVIDENCE",
      rationaleCode: "EVIDENCE_SET_NOT_COMPLETE",
      axisExplanation: facts.axes,
    };
  if (facts.conflictCount > 0)
    return {
      state: "CONFLICTING_EVIDENCE",
      rationaleCode: "MATERIAL_CONFLICT_RETAINED",
      axisExplanation: facts.axes,
    };
  const failureTypes = new Set([
    "MODEL_UNDERPERFORMS_BASELINE",
    "HIGH_BIAS",
    "LOW_COVERAGE",
    "OUTSIDE_VALIDITY_DOMAIN",
  ]);
  if (
    facts.invalidatingCount > 0 ||
    facts.negativeFindingTypes.some((value) => failureTypes.has(value))
  )
    return {
      state: "EVIDENCE_OF_FAILURE",
      rationaleCode: "GOVERNED_FAILURE_EVIDENCE_PRESENT",
      axisExplanation: facts.axes,
    };
  const critical: StrengthAxis[] = [
    "INDEPENDENCE",
    "TEMPORALITY",
    "DOMAIN_COVERAGE",
    "UNCERTAINTY_COMPLETENESS",
  ];
  if (
    critical.some((axis) =>
      ["UNKNOWN", "INSUFFICIENT"].includes(axisState(facts.axes, axis)),
    )
  )
    return {
      state: "INSUFFICIENT_EVIDENCE",
      rationaleCode: "CRITICAL_EVIDENCE_AXIS_INSUFFICIENT",
      axisExplanation: facts.axes,
    };
  if (
    facts.axes.some((item) =>
      ["UNKNOWN", "INSUFFICIENT", "LIMITED"].includes(item.state),
    ) ||
    facts.negativeFindingTypes.length > 0
  )
    return {
      state: "EVIDENCE_OF_LIMITED_CAPABILITY",
      rationaleCode: "POSITIVE_EVIDENCE_WITH_EXPLICIT_LIMITATIONS",
      axisExplanation: facts.axes,
    };
  return {
    state: "EVIDENCE_OF_CAPABILITY",
    rationaleCode: "ALL_PREDECLARED_MINIMUM_REQUIREMENTS_SATISFIED",
    axisExplanation: facts.axes,
  };
}

const setSubset = <T>(inner: T[], outer: T[]) =>
  inner.every((value) => outer.includes(value));

function constraintSubset(
  claim: CapabilityScope["domainConstraints"][number],
  capability: CapabilityScope["domainConstraints"][number],
) {
  if (
    claim.variableKey !== capability.variableKey ||
    claim.kind !== capability.kind
  )
    return false;
  if (claim.kind === "NUMERIC_RANGE" && capability.kind === "NUMERIC_RANGE") {
    if (
      claim.unit.key !== capability.unit.key ||
      claim.unit.revision !== capability.unit.revision
    )
      return false;
    const lowerInside =
        claim.lowerBound > capability.lowerBound ||
        (claim.lowerBound === capability.lowerBound &&
          (!claim.lowerInclusive || capability.lowerInclusive)),
      upperInside =
        claim.upperBound < capability.upperBound ||
        (claim.upperBound === capability.upperBound &&
          (!claim.upperInclusive || capability.upperInclusive));
    return lowerInside && upperInside;
  }
  if (
    claim.kind === "TEMPORAL_RANGE" &&
    capability.kind === "TEMPORAL_RANGE"
  )
    return (
      BigInt(claim.startEpochMicros) >=
        BigInt(capability.startEpochMicros) &&
      BigInt(claim.endEpochMicros) <= BigInt(capability.endEpochMicros)
    );
  if (
    claim.kind === "CATEGORICAL_SET" &&
    capability.kind === "CATEGORICAL_SET"
  )
    return setSubset(claim.values, capability.values);
  if (claim.kind === "BOOLEAN_SET" && capability.kind === "BOOLEAN_SET")
    return setSubset(claim.values, capability.values);
  return false;
}

export function isScopeSubset(
  claim: CapabilityScope,
  capability: CapabilityScope,
) {
  if (
    claim.modelVersionId !== capability.modelVersionId ||
    claim.modelContentHash !== capability.modelContentHash ||
    claim.targetKey !== capability.targetKey ||
    claim.horizonKey !== capability.horizonKey ||
    claim.validityDomainVersionId !== capability.validityDomainVersionId ||
    claim.protocolFamily !== capability.protocolFamily ||
    claim.metricProfile.length !== capability.metricProfile.length ||
    !setSubset(claim.metricProfile, capability.metricProfile) ||
    claim.baselineProfile.length !== capability.baselineProfile.length ||
    !setSubset(claim.baselineProfile, capability.baselineProfile) ||
    claim.uncertaintyProfile.length !== capability.uncertaintyProfile.length ||
    !setSubset(claim.uncertaintyProfile, capability.uncertaintyProfile) ||
    BigInt(claim.evidencePeriod.startEpochMicros) <
      BigInt(capability.evidencePeriod.startEpochMicros) ||
    BigInt(claim.evidencePeriod.endEpochMicros) >
      BigInt(capability.evidencePeriod.endEpochMicros) ||
    claim.domainConstraints.length !== capability.domainConstraints.length
  )
    return false;
  return claim.domainConstraints.every((item) => {
    const parent = capability.domainConstraints.find(
      (candidate) => candidate.variableKey === item.variableKey,
    );
    return parent ? constraintSubset(item, parent) : false;
  });
}

export function assertScopeSubset(
  claim: CapabilityScope,
  capability: CapabilityScope,
) {
  if (!isScopeSubset(claim, capability))
    throw new CapabilityClaimError("CLAIM_SCOPE_EXCEEDS_CAPABILITY");
}

export function renderPredictiveClaim(input: {
  state: CapabilityState;
  scope: CapabilityScope;
  evidenceSetHash: string;
  limitations: unknown[];
  negativeEvidence: unknown[];
  conflicts: unknown[];
  uncertaintySummary: unknown[];
}) {
  const { scope } = input;
  return [
    `For ModelVersion ${scope.modelVersionId}, target ${scope.targetKey} and exact horizon ${scope.horizonKey},`,
    `within ValidityDomain ${scope.validityDomainVersionId}, PredictiveEvidenceSet ${input.evidenceSetHash} supports`,
    `${input.state} for evidence period ${scope.evidencePeriod.startEpochMicros}..${scope.evidencePeriod.endEpochMicros},`,
    `under metric profile [${scope.metricProfile.join(", ")}], baseline profile [${scope.baselineProfile.join(", ")}],`,
    `uncertainty profile [${scope.uncertaintyProfile.join(", ")}], with ${input.limitations.length} limitation(s),`,
    `${input.negativeEvidence.length} negative finding(s) and ${input.conflicts.length} material conflict(s).`,
  ].join(" ");
}

export function triggerInitialState(type: RevalidationTriggerType) {
  return type === "DRIFT_DETECTED"
    ? ("REVIEW_REQUIRED" as const)
    : ("REVALIDATION_REQUIRED" as const);
}

export function projectClaimCurrentness(
  status: ClaimState,
  validThroughEpochMicros: string | null,
  hasUnresolvedTrigger: boolean,
  nowEpochMicros: bigint,
) {
  if (status === "REVOKED") return "REVOKED" as const;
  if (status === "SUPERSEDED") return "SUPERSEDED" as const;
  if (status === "REJECTED") return "REJECTED" as const;
  if (status !== "AUTHORIZED") return "NOT_AUTHORIZED" as const;
  if (hasUnresolvedTrigger) return "HUMAN_REVIEW_REQUIRED" as const;
  if (
    validThroughEpochMicros !== null &&
    nowEpochMicros > BigInt(validThroughEpochMicros)
  )
    return "AUTHORIZED_EXPIRED_REVIEW_REQUIRED" as const;
  return "AUTHORIZED_CURRENT" as const;
}
