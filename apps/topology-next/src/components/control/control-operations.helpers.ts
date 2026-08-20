import type { ControlOperationalStatus } from "@/lib/dto/control-operations.dto";
import { ControlOperationsApiError } from "@/components/control/control-operations-client";

export function getOperationalStatusBadgeClass(status: ControlOperationalStatus | "RECOMMENDED") {
  if (["HEALTHY", "ACKNOWLEDGED", "PUBLISHED", "RECOMMENDED"].includes(status)) return "status-badge status-active";
  if (["FAILED", "MISCONFIGURED", "EXPIRED"].includes(status)) return "status-badge status-fault";
  if (["PENDING", "RETRYING"].includes(status)) return "status-badge status-maintenance";
  return "status-badge status-inactive";
}

export function operationErrorMessage(error: unknown) {
  if (error instanceof ControlOperationsApiError) {
    if (error.status === 401) return "Your session is no longer available. Sign in again to view control operations.";
    if (error.status === 403) return "You do not have permission to view control operations for this project.";
  }
  return "Control operations could not be loaded. Try refreshing the data.";
}

export function canLoadNextPage(itemCount: number, limit: number) {
  return itemCount === limit;
}
