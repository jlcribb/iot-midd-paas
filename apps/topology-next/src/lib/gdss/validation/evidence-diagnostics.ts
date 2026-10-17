import { AppError } from "@/lib/errors/app-error";

export type PredictiveEvidenceErrorCode =
  | "DOMAIN_CONTEXT_INCOMPLETE"
  | "DOMAIN_UNKNOWN"
  | "DOMAIN_PREDICATE_EVALUATION_FAILED"
  | "PREDICTIVE_POSITION_UNKNOWN"
  | "EVIDENCE_SET_INCOMPLETE"
  | "EVIDENCE_SET_IMMUTABLE"
  | "EVIDENCE_REFERENCE_INVALID"
  | "EVIDENCE_REFERENCE_INVALIDATED"
  | "MODEL_VERSION_EVIDENCE_MISMATCH"
  | "TARGET_EVIDENCE_MISMATCH"
  | "HORIZON_EVIDENCE_MISMATCH"
  | "DOMAIN_EVIDENCE_MISMATCH"
  | "NEGATIVE_EVIDENCE_OMITTED"
  | "CONFLICTING_EVIDENCE_PRESENT"
  | "EVIDENCE_STRENGTH_AXIS_INVALID"
  | "AI_AUTHORITY_FORBIDDEN"
  | "UNAUTHORIZED_PREDICTIVE_EVIDENCE_ACTION";

export class PredictiveEvidenceError extends AppError {
  constructor(
    code: PredictiveEvidenceErrorCode,
    message: string = code,
    status = 409,
    details?: unknown,
  ) {
    super(status, code, message, details);
    this.name = "PredictiveEvidenceError";
  }
}
