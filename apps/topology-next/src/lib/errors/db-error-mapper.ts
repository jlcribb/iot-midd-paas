import type { DatabaseError } from "pg";
import { AppError } from "@/lib/errors/app-error";
import {
  ConflictError,
  InternalError,
  ValidationError,
} from "@/lib/errors/domain-errors";
import {
  ValidationFoundationError,
  type ValidationFoundationErrorCode,
} from "@/lib/gdss/validation/diagnostics";
import {
  EvidenceCustodyError,
  type EvidenceCustodyErrorCode,
} from "@/lib/gdss/validation/partition-diagnostics";
import {
  ValidationRunError,
  type ValidationRunErrorCode,
} from "@/lib/gdss/validation/run-diagnostics";
import {
  MetricFoundationError,
  type MetricFoundationErrorCode,
} from "@/lib/gdss/validation/metric-diagnostics";
import {
  PredictiveEvidenceError,
  type PredictiveEvidenceErrorCode,
} from "@/lib/gdss/validation/evidence-diagnostics";
import {
  CapabilityClaimError,
  type CapabilityClaimErrorCode,
} from "@/lib/gdss/validation/capability-diagnostics";

const validationFoundationCodes: readonly ValidationFoundationErrorCode[] = [
  "VALIDATION_PROTOCOL_NOT_DRAFT",
  "VALIDATION_PROTOCOL_NOT_APPROVABLE",
  "VALIDATION_PROTOCOL_NOT_SEALABLE",
  "VALIDATION_PROTOCOL_ALREADY_SEALED",
  "VALIDATION_PROTOCOL_IMMUTABLE",
  "VALIDITY_DOMAIN_NOT_DRAFT",
  "VALIDITY_DOMAIN_NOT_APPROVABLE",
  "VALIDITY_DOMAIN_NOT_SEALABLE",
  "VALIDITY_DOMAIN_IMMUTABLE",
  "MODEL_VERSION_NOT_FOUND",
  "VALIDITY_DOMAIN_VERSION_MISMATCH",
  "INVALID_DOMAIN_PREDICATE",
  "INVALID_HORIZON",
  "INVALID_ACCEPTANCE_CRITERION",
  "RESOURCE_LIMIT_EXCEEDED",
  "SOD_VIOLATION",
  "UNAUTHORIZED_VALIDATION_PROTOCOL_ACTION",
];
const evidenceCustodyCodes: readonly EvidenceCustodyErrorCode[] = [
  "EVIDENCE_PARTITION_OVERLAP",
  "TRANSITIVE_LINEAGE_OVERLAP",
  "DEPENDENT_GROUP_SPLIT",
  "TEMPORAL_LEAKAGE_DETECTED",
  "DUPLICATE_EVIDENCE_DETECTED",
  "PARTITION_PLAN_NOT_DRAFT",
  "PARTITION_PLAN_IMMUTABLE",
  "HOLDOUT_NOT_SEALED",
  "HOLDOUT_ALREADY_OPEN",
  "HOLDOUT_ALREADY_CONSUMED",
  "HOLDOUT_REUSE_FORBIDDEN",
  "HOLDOUT_INDEPENDENCE_COMPROMISED",
  "CROSS_PROJECT_EVIDENCE_REFERENCE",
  "INVALID_EVIDENCE_LINEAGE",
  "EVIDENCE_LINEAGE_CYCLE",
  "LINEAGE_DEPTH_LIMIT_EXCEEDED",
  "INDEPENDENCE_UNKNOWN",
  "AI_AUTHORITY_FORBIDDEN",
  "UNAUTHORIZED_EVIDENCE_CUSTODY_ACTION",
];
const validationRunCodes: readonly ValidationRunErrorCode[] = [
  "VALIDATION_RUN_NOT_READY",
  "VALIDATION_RUN_BINDING_INVALID",
  "VALIDATION_RUN_INDEPENDENCE_NOT_ELIGIBLE",
  "VALIDATION_RUN_ALREADY_STARTED",
  "MODEL_VERSION_MISMATCH",
  "PREDICTION_NOT_COMMITTED",
  "PREDICTION_ALREADY_COMMITTED",
  "PREDICTION_COMMITMENT_TAMPERED",
  "PREDICTION_IMMUTABLE",
  "OBSERVATION_REFERENCE_INVALID",
  "OBSERVATION_AVAILABILITY_UNKNOWN",
  "PREDICTION_AFTER_OBSERVATION",
  "TEMPORAL_INTEGRITY_UNKNOWN",
  "TARGET_MISMATCH",
  "HORIZON_MISMATCH",
  "UNIT_MISMATCH",
  "PAIRING_RULE_VIOLATION",
  "PAIR_IMMUTABLE",
  "PAIR_SET_IMMUTABLE",
  "CROSS_PROJECT_PAIRING",
];
const metricFoundationCodes: readonly MetricFoundationErrorCode[] = [
  "METRIC_NOT_ALLOWED",
  "METRIC_INPUT_INVALID",
  "METRIC_PAIRSET_INVALID",
  "METRIC_UNIT_MISMATCH",
  "METRIC_RESULT_IMMUTABLE",
  "BASELINE_NOT_ALLOWED",
  "BASELINE_PAIRSET_MISMATCH",
  "BASELINE_FUTURE_LEAKAGE",
  "BASELINE_MODEL_VERSION_INVALID",
  "UNCERTAINTY_SOURCE_INVALID",
  "UNCERTAINTY_METHOD_NOT_ALLOWED",
  "UNCERTAINTY_STATE_INVALID",
  "PREDICTION_INTERVAL_INVALID",
  "INTERVAL_AFTER_OBSERVATION",
];
const predictiveEvidenceCodes: readonly PredictiveEvidenceErrorCode[] = [
  "DOMAIN_CONTEXT_INCOMPLETE",
  "DOMAIN_UNKNOWN",
  "DOMAIN_PREDICATE_EVALUATION_FAILED",
  "PREDICTIVE_POSITION_UNKNOWN",
  "EVIDENCE_SET_INCOMPLETE",
  "EVIDENCE_SET_IMMUTABLE",
  "EVIDENCE_REFERENCE_INVALID",
  "EVIDENCE_REFERENCE_INVALIDATED",
  "MODEL_VERSION_EVIDENCE_MISMATCH",
  "TARGET_EVIDENCE_MISMATCH",
  "HORIZON_EVIDENCE_MISMATCH",
  "DOMAIN_EVIDENCE_MISMATCH",
  "NEGATIVE_EVIDENCE_OMITTED",
  "CONFLICTING_EVIDENCE_PRESENT",
  "EVIDENCE_STRENGTH_AXIS_INVALID",
  "AI_AUTHORITY_FORBIDDEN",
  "UNAUTHORIZED_PREDICTIVE_EVIDENCE_ACTION",
];
const capabilityClaimCodes: readonly CapabilityClaimErrorCode[] = [
  "INSUFFICIENT_EVIDENCE",
  "CONFLICTING_EVIDENCE",
  "CAPABILITY_SCOPE_INVALID",
  "CAPABILITY_ASSESSMENT_IMMUTABLE",
  "CLAIM_SCOPE_EXCEEDS_EVIDENCE",
  "CLAIM_SCOPE_EXCEEDS_CAPABILITY",
  "CLAIM_NOT_DRAFT",
  "CLAIM_NOT_REVIEWABLE",
  "CLAIM_NOT_AUTHORIZABLE",
  "CLAIM_ALREADY_TERMINAL",
  "CLAIM_IMMUTABLE",
  "CLAIM_AUTHORIZATION_FORBIDDEN",
  "CLAIM_SOD_VIOLATION",
  "STALE_AUTHORIZATION_REPLAY",
  "CLAIM_ALREADY_REVOKED",
  "CLAIM_REVOCATION_FORBIDDEN",
  "REVALIDATION_REQUIRED",
  "EVIDENCE_TRANSFER_FORBIDDEN",
  "MODEL_VERSION_TRANSFER_REQUIRES_REVALIDATION",
  "AI_AUTHORITY_FORBIDDEN",
  "PHYSICAL_AUTHORITY_FORBIDDEN",
  "UNAUTHORIZED_CAPABILITY_ACTION",
];

function getPgErrorCode(error: unknown): string | undefined {
  if (typeof error !== "object" || error === null) {
    return undefined;
  }
  return (error as DatabaseError).code;
}

function getPgMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected database error";
}

export function mapDatabaseError(error: unknown): AppError {
  if (error instanceof AppError) {
    return error;
  }

  const code = getPgErrorCode(error);
  const message = getPgMessage(error);
  const foundationCode = validationFoundationCodes.find((value) =>
    message.includes(value),
  );
  if (foundationCode) return new ValidationFoundationError(foundationCode);
  const custodyCode = evidenceCustodyCodes.find((value) =>
    message.includes(value),
  );
  if (custodyCode) return new EvidenceCustodyError(custodyCode);
  const validationRunCode = validationRunCodes.find((value) =>
    message.includes(value),
  );
  if (validationRunCode) return new ValidationRunError(validationRunCode);
  const metricFoundationCode = metricFoundationCodes.find((value) =>
    message.includes(value),
  );
  if (metricFoundationCode)
    return new MetricFoundationError(metricFoundationCode);
  const predictiveEvidenceCode = predictiveEvidenceCodes.find((value) =>
    message.includes(value),
  );
  if (predictiveEvidenceCode)
    return new PredictiveEvidenceError(predictiveEvidenceCode);
  const capabilityClaimCode = capabilityClaimCodes.find((value) =>
    message.includes(value),
  );
  if (capabilityClaimCode)
    return new CapabilityClaimError(capabilityClaimCode);

  switch (code) {
    case "23505":
      return new ConflictError(message);
    case "23503":
      return new ConflictError(message);
    case "23514":
      return new ConflictError(message);
    case "22P02":
      return new ValidationError(message);
    default:
      return new InternalError(message);
  }
}
