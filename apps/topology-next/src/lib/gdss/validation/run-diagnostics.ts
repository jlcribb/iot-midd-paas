export type ValidationRunErrorCode =
  | "VALIDATION_RUN_NOT_READY"
  | "VALIDATION_RUN_BINDING_INVALID"
  | "VALIDATION_RUN_INDEPENDENCE_NOT_ELIGIBLE"
  | "VALIDATION_RUN_ALREADY_STARTED"
  | "MODEL_VERSION_MISMATCH"
  | "PREDICTION_NOT_COMMITTED"
  | "PREDICTION_ALREADY_COMMITTED"
  | "PREDICTION_COMMITMENT_TAMPERED"
  | "PREDICTION_IMMUTABLE"
  | "OBSERVATION_REFERENCE_INVALID"
  | "OBSERVATION_AVAILABILITY_UNKNOWN"
  | "PREDICTION_AFTER_OBSERVATION"
  | "TEMPORAL_INTEGRITY_UNKNOWN"
  | "TARGET_MISMATCH"
  | "HORIZON_MISMATCH"
  | "UNIT_MISMATCH"
  | "PAIRING_RULE_VIOLATION"
  | "PAIR_IMMUTABLE"
  | "PAIR_SET_IMMUTABLE"
  | "CROSS_PROJECT_PAIRING";
export class ValidationRunError extends AppError {
  constructor(
    code: ValidationRunErrorCode,
    message: string = code,
    status = 409,
  ) {
    super(status, code, message);
    this.name = "ValidationRunError";
  }
}
import { AppError } from "@/lib/errors/app-error";
