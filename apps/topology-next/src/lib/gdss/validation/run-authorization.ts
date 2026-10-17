import type { ControlActor } from "@/lib/dto/control-access.dto";
import { ValidationRunError } from "./run-diagnostics";
export type ValidationRunCapability = "RUN_VALIDATION" | "READ_VALIDATION_RUN";
export function assertValidationRunAccess(
  actor: ControlActor,
  projectId: string,
  capability: ValidationRunCapability,
) {
  if (
    actor.auth_source === "dev_fallback" ||
    (!actor.all_projects && !actor.project_ids.includes(projectId))
  )
    throw new ValidationRunError(
      "VALIDATION_RUN_BINDING_INVALID",
      "Project-scoped OAuth authorization required",
      403,
    );
  const role = actor.project_roles?.[projectId] ?? actor.role;
  if (
    capability === "RUN_VALIDATION"
      ? !["operator", "admin"].includes(role)
      : !["viewer", "operator", "admin"].includes(role)
  )
    throw new ValidationRunError(
      "VALIDATION_RUN_BINDING_INVALID",
      "RUN_VALIDATION denied",
      403,
    );
}
