import type {
  ObservationReferenceContent,
  PairIntegrityState,
  PairingContract,
  PredictionContent,
} from "./run-contracts";
export function assessPairIntegrity(
  prediction: PredictionContent,
  observation: ObservationReferenceContent,
  contract: PairingContract,
  committedAt: string,
): PairIntegrityState {
  if (
    prediction.targetKey !== observation.targetKey ||
    contract.targetKey !== prediction.targetKey
  )
    return "TARGET_MISMATCH";
  if (contract.horizonKey !== prediction.horizonKey) return "HORIZON_MISMATCH";
  if (
    (prediction.predictedUnit.key !== observation.unit.key ||
      prediction.predictedUnit.revision !== observation.unit.revision) &&
    !contract.conversionIdentity
  )
    return "UNIT_MISMATCH";
  if (!observation.availabilityTime) return "TEMPORAL_INTEGRITY_UNKNOWN";
  if (Date.parse(committedAt) >= Date.parse(observation.availabilityTime))
    return "PREDICTION_AFTER_OBSERVATION";
  const factors: Record<string, number> = {
      second: 1_000,
      minute: 60_000,
      hour: 3_600_000,
      day: 86_400_000,
    },
    expected =
      Date.parse(prediction.forecastOrigin) +
      prediction.horizonDuration * (factors[prediction.horizonUnit.key] ?? NaN),
    measured = observation.measurementTime
      ? Date.parse(observation.measurementTime)
      : NaN;
  if (contract.pairingRule === "EXACT_TIMESTAMP" && measured !== expected)
    return "PAIRING_RULE_VIOLATION";
  if (
    contract.pairingRule === "EXACT_EVENT_ID" &&
    contract.eventIdentity !== observation.observationIdentity
  )
    return "PAIRING_RULE_VIOLATION";
  if (contract.tolerance !== undefined && contract.toleranceUnit) {
    const maximum =
        contract.tolerance * (factors[contract.toleranceUnit.key] ?? NaN),
      delta = measured - expected;
    if (
      !Number.isFinite(maximum) ||
      !Number.isFinite(delta) ||
      Math.abs(delta) > maximum ||
      (contract.directionality === "BEFORE_ONLY" && delta > 0) ||
      (contract.directionality === "AFTER_ONLY" && delta < 0)
    )
      return "PAIRING_RULE_VIOLATION";
  }
  return "PASS";
}
