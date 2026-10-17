import { AppError } from "@/lib/errors/app-error";
export type MetricFoundationErrorCode =
  | "METRIC_NOT_ALLOWED"
  | "METRIC_INPUT_INVALID"
  | "METRIC_PAIRSET_INVALID"
  | "METRIC_UNIT_MISMATCH"
  | "METRIC_RESULT_IMMUTABLE"
  | "BASELINE_NOT_ALLOWED"
  | "BASELINE_PAIRSET_MISMATCH"
  | "BASELINE_FUTURE_LEAKAGE"
  | "BASELINE_MODEL_VERSION_INVALID"
  | "UNCERTAINTY_SOURCE_INVALID"
  | "UNCERTAINTY_METHOD_NOT_ALLOWED"
  | "UNCERTAINTY_STATE_INVALID"
  | "PREDICTION_INTERVAL_INVALID"
  | "INTERVAL_AFTER_OBSERVATION";
export class MetricFoundationError extends AppError {
  constructor(
    code: MetricFoundationErrorCode,
    message: string = code,
    status = 409,
    details?: unknown,
  ) {
    super(status, code, message, details);
    this.name = "MetricFoundationError";
  }
}
