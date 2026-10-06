export const OBSERVATION_FAILURE_CODES = [
  "INVALID_DATASET", "UNSUPPORTED_SOURCE_TYPE", "SOURCE_HASH_MISMATCH",
  "SOURCE_EPISTEMIC_ORIGIN_MISMATCH", "UNKNOWN_QUANTITY_MAPPING",
  "AMBIGUOUS_QUANTITY_MAPPING", "DIMENSION_MISMATCH", "TEMPORAL_ORIGIN_MISSING",
  "TEMPORAL_COORDINATE_OUT_OF_RANGE", "TEMPORAL_ALIGNMENT_FAILURE",
  "DUPLICATE_MEASUREMENT_COORDINATE", "INSUFFICIENT_OBSERVATIONS",
  "INVALID_UNCERTAINTY", "ARTIFACT_RECONCILIATION_FAILURE", "LEAKAGE_DETECTED",
  "IDENTITY_MISMATCH", "RESOURCE_LIMIT_EXCEEDED",
] as const;
export type ObservationFailureCode = typeof OBSERVATION_FAILURE_CODES[number];
export class ObservationContractError extends Error {
  constructor(readonly code: ObservationFailureCode, message: string) { super(message); this.name = "ObservationContractError"; }
}
export function observationFail(code: ObservationFailureCode, message: string): never { throw new ObservationContractError(code, message); }
