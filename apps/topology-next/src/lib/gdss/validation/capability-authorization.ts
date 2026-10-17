import {
  canAccessProject,
  getControlRoleForProject,
} from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { CapabilityClaimError } from "./capability-diagnostics";
import { isAiAuthority } from "./authority-boundary";

export type CapabilityGovernancePermission =
  | "ASSESS_PREDICTIVE_CAPABILITY"
  | "AUTHOR_PREDICTIVE_CLAIM"
  | "REVIEW_CAPABILITY_ASSESSMENT"
  | "AUTHORIZE_PREDICTIVE_CLAIM"
  | "REVOKE_PREDICTIVE_CLAIM"
  | "AUDIT_PREDICTIVE_EVIDENCE";

const roles: Record<CapabilityGovernancePermission, readonly string[]> = {
  ASSESS_PREDICTIVE_CAPABILITY: ["operator", "admin"],
  AUTHOR_PREDICTIVE_CLAIM: ["operator", "admin"],
  REVIEW_CAPABILITY_ASSESSMENT: ["operator", "admin"],
  AUTHORIZE_PREDICTIVE_CLAIM: ["admin"],
  REVOKE_PREDICTIVE_CLAIM: ["admin"],
  AUDIT_PREDICTIVE_EVIDENCE: ["viewer", "operator", "admin"],
};

export function assertCapabilityGovernanceAccess(
  actor: ControlActor,
  projectId: string,
  permission: CapabilityGovernancePermission,
) {
  if (
    permission !== "AUDIT_PREDICTIVE_EVIDENCE" &&
    isAiAuthority(actor)
  )
    throw new CapabilityClaimError("AI_AUTHORITY_FORBIDDEN", undefined, 403);
  if (
    actor.auth_source !== "oauth_session" ||
    !actor.user_id ||
    !canAccessProject(actor, projectId) ||
    !roles[permission].includes(getControlRoleForProject(actor, projectId))
  )
    throw new CapabilityClaimError(
      "UNAUTHORIZED_CAPABILITY_ACTION",
      `UNAUTHORIZED_CAPABILITY_ACTION: ${permission}`,
      403,
    );
}

export const CAPABILITY_PHYSICAL_AUTHORITY = "NONE" as const;
export const CAPABILITY_CONTROL_AUTHORITY = "NONE" as const;
export const CAPABILITY_AI_BOUNDARY = {
  maySummarize: true,
  mayDraft: true,
  mayFlagInconsistencies: true,
  mayReviewAsAuthority: false,
  mayAuthorize: false,
  mayRevoke: false,
  mayUpgradeCapability: false,
  mayChangeAuthorizedScope: false,
} as const;
