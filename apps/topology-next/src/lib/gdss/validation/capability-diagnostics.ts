import { AppError } from "@/lib/errors/app-error";

export type CapabilityClaimErrorCode =
  | "INSUFFICIENT_EVIDENCE"
  | "CONFLICTING_EVIDENCE"
  | "CAPABILITY_SCOPE_INVALID"
  | "CAPABILITY_ASSESSMENT_IMMUTABLE"
  | "CLAIM_SCOPE_EXCEEDS_EVIDENCE"
  | "CLAIM_SCOPE_EXCEEDS_CAPABILITY"
  | "CLAIM_NOT_DRAFT"
  | "CLAIM_NOT_REVIEWABLE"
  | "CLAIM_NOT_AUTHORIZABLE"
  | "CLAIM_ALREADY_TERMINAL"
  | "CLAIM_IMMUTABLE"
  | "CLAIM_AUTHORIZATION_FORBIDDEN"
  | "CLAIM_SOD_VIOLATION"
  | "STALE_AUTHORIZATION_REPLAY"
  | "CLAIM_ALREADY_REVOKED"
  | "CLAIM_REVOCATION_FORBIDDEN"
  | "REVALIDATION_REQUIRED"
  | "EVIDENCE_TRANSFER_FORBIDDEN"
  | "MODEL_VERSION_TRANSFER_REQUIRES_REVALIDATION"
  | "AI_AUTHORITY_FORBIDDEN"
  | "PHYSICAL_AUTHORITY_FORBIDDEN"
  | "UNAUTHORIZED_CAPABILITY_ACTION";

export class CapabilityClaimError extends AppError {
  constructor(
    code: CapabilityClaimErrorCode,
    message: string = code,
    status = 409,
    details?: unknown,
  ) {
    super(status, code, message, details);
    this.name = "CapabilityClaimError";
  }
}
