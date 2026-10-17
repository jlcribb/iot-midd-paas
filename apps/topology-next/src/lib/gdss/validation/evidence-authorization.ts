import {
  canAccessProject,
  getControlRoleForProject,
} from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { PredictiveEvidenceError } from "./evidence-diagnostics";
import { isAiAuthority } from "./authority-boundary";

export type PredictiveEvidenceCapability =
  "ASSEMBLE_PREDICTIVE_EVIDENCE" | "READ_PREDICTIVE_EVIDENCE";

export function assertPredictiveEvidenceAccess(
  actor: ControlActor,
  projectId: string,
  capability: PredictiveEvidenceCapability,
) {
  if (
    capability === "ASSEMBLE_PREDICTIVE_EVIDENCE" &&
    isAiAuthority(actor)
  )
    throw new PredictiveEvidenceError(
      "AI_AUTHORITY_FORBIDDEN",
      undefined,
      403,
    );
  if (
    actor.auth_source !== "oauth_session" ||
    !actor.user_id ||
    !canAccessProject(actor, projectId)
  )
    throw new PredictiveEvidenceError(
      "UNAUTHORIZED_PREDICTIVE_EVIDENCE_ACTION",
      "Project-scoped OAuth authorization required",
      403,
    );
  const role = getControlRoleForProject(actor, projectId);
  const allowed =
    capability === "ASSEMBLE_PREDICTIVE_EVIDENCE"
      ? ["operator", "admin"]
      : ["viewer", "operator", "admin"];
  if (!allowed.includes(role))
    throw new PredictiveEvidenceError(
      "UNAUTHORIZED_PREDICTIVE_EVIDENCE_ACTION",
      `${capability} denied`,
      403,
    );
}
