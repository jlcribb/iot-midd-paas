import { canAccessProject, getControlRoleForProject } from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { isAiAuthority } from "@/lib/gdss/validation";
import { DecisionError } from "./diagnostics";

export type DecisionPermission = "AUTHOR_DECISION_PROBLEM" | "SEAL_DECISION_PROBLEM" | "AUDIT_DECISION_SUPPORT" | "DEFINE_DECISION_ALTERNATIVE" | "ADMIT_DECISION_ALTERNATIVE" | "RUN_SCENARIO_EVALUATION" | "INVALIDATE_SCENARIO_EVALUATION" | "AUTHOR_DECISION_CRITERION" | "SEAL_DECISION_CRITERION" | "ASSEMBLE_DECISION_COMPARISON" | "ASSESS_DECISION_ROBUSTNESS" | "ASSESS_DECISION_RISK" | "AUTHOR_RECOMMENDATION" | "REVIEW_RECOMMENDATION" | "AUTHORIZE_RECOMMENDATION" | "REVOKE_RECOMMENDATION" | "RECORD_HUMAN_DECISION";
const roles: Record<DecisionPermission, readonly string[]> = {
  AUTHOR_DECISION_PROBLEM: ["operator", "admin"],
  SEAL_DECISION_PROBLEM: ["admin"],
  AUDIT_DECISION_SUPPORT: ["viewer", "operator", "admin"],
  DEFINE_DECISION_ALTERNATIVE: ["operator", "admin"],
  ADMIT_DECISION_ALTERNATIVE: ["admin"],
  RUN_SCENARIO_EVALUATION: ["operator", "admin"],
  INVALIDATE_SCENARIO_EVALUATION: ["admin"],
  AUTHOR_DECISION_CRITERION: ["operator", "admin"],
  SEAL_DECISION_CRITERION: ["admin"],
  ASSEMBLE_DECISION_COMPARISON: ["operator", "admin"],
  ASSESS_DECISION_ROBUSTNESS: ["operator", "admin"],
  ASSESS_DECISION_RISK: ["operator", "admin"],
  AUTHOR_RECOMMENDATION: ["operator", "admin"],
  REVIEW_RECOMMENDATION: ["admin"],
  AUTHORIZE_RECOMMENDATION: ["admin"],
  REVOKE_RECOMMENDATION: ["admin"],
  RECORD_HUMAN_DECISION: ["admin"],
};

export function assertDecisionAccess(actor: ControlActor, projectId: string, permission: DecisionPermission) {
  if ((permission === "SEAL_DECISION_PROBLEM" || permission === "ADMIT_DECISION_ALTERNATIVE" || permission === "RUN_SCENARIO_EVALUATION" || permission === "INVALIDATE_SCENARIO_EVALUATION" || permission === "SEAL_DECISION_CRITERION" || permission === "ASSEMBLE_DECISION_COMPARISON" || permission === "ASSESS_DECISION_ROBUSTNESS" || permission === "ASSESS_DECISION_RISK" || permission === "REVIEW_RECOMMENDATION" || permission === "AUTHORIZE_RECOMMENDATION" || permission === "REVOKE_RECOMMENDATION" || permission === "RECORD_HUMAN_DECISION") && isAiAuthority(actor))
    throw new DecisionError("AI_AUTHORITY_FORBIDDEN", undefined, 403);
  if (
    actor.auth_source !== "oauth_session" || !actor.user_id || !canAccessProject(actor, projectId) ||
    !roles[permission].includes(getControlRoleForProject(actor, projectId))
  ) throw new DecisionError("UNAUTHORIZED_DECISION_ACTION", `${permission} denied`, 403);
}

export const DECISION_AUTHORITY_BOUNDARY = {
  PolicyAuthority: "NONE",
  ControlAuthority: "NONE",
  PhysicalAuthority: "NONE",
  aiMayDraft: true,
  aiMaySeal: false,
  aiMayApprovePreferences: false,
  aiMayApproveRisk: false,
  aiMayAdmitAlternative: false,
  aiMayAdmitScenario: false,
  RecommendationAuthority: "NONE",
  aiMayFabricateOutcome: false,
  aiMayInvalidateEvaluation: false,
  aiMaySealCriterion: false,
  aiMayAssembleComparison: false,
  aiMayAlterWeights: false,
  aiMayMaterializeSensitivity: false,
  aiMayMaterializeRobustness: false,
  aiMayReclassifyRisk: false,
  aiMayDraftRecommendationNarrative: true,
  aiMayReviewRecommendationAsAuthority: false,
  aiMayAuthorizeRecommendation: false,
  aiMayRevokeRecommendation: false,
  aiMayRecordHumanDecision: false,
  aiMayUseSodException: false,
} as const;

export const GDSS_007F_AUTHORITY_BOUNDARY = {
  RecommendationAuthority: "HUMAN_GOVERNED_DECISION_SUPPORT_ONLY",
  PolicyAuthority: "NONE",
  ControlAuthority: "NONE",
  PhysicalAuthority: "NONE",
  aiMayDraftRecommendationNarrative: true,
  aiMayReviewRecommendationAsAuthority: false,
  aiMayAuthorizeRecommendation: false,
  aiMayRevokeRecommendation: false,
  aiMayRecordHumanDecision: false,
  aiMayUseSodException: false,
} as const;
