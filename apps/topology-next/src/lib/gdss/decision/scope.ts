import { isScopeSubset, type CapabilityScope } from "@/lib/gdss/validation";
import { DecisionError } from "./diagnostics";

export type DecisionEvidenceFacts = {
  evidenceScope: CapabilityScope;
  capabilityScope: CapabilityScope;
  claimScope: CapabilityScope;
  decisionScope: CapabilityScope;
  capabilityState: string;
  claimCurrentness: string;
};

export function reconcileDecisionEvidence(facts: DecisionEvidenceFacts) {
  if (facts.claimCurrentness !== "AUTHORIZED_CURRENT") throw new DecisionError("CLAIM_NOT_CURRENT");
  if (!isScopeSubset(facts.decisionScope, facts.claimScope) || !isScopeSubset(facts.claimScope, facts.capabilityScope) || !isScopeSubset(facts.capabilityScope, facts.evidenceScope))
    throw new DecisionError("DECISION_INPUT_NOT_CURRENT");
  if (facts.capabilityState === "EVIDENCE_OF_CAPABILITY")
    return { eligibility: "AUTHORIZED_RECOMMENDATION_V1_ELIGIBLE" as const, reviewRequired: false };
  if (facts.capabilityState === "EVIDENCE_OF_LIMITED_CAPABILITY")
    return { eligibility: "CANNOT_SUPPORT_AUTHORIZED_RECOMMENDATION_V1" as const, reviewRequired: true, marker: "DECISION_SUPPORT_REVIEW_REQUIRED" as const };
  throw new DecisionError(facts.capabilityState === "CONFLICTING_EVIDENCE" ? "UNCERTAINTY_INSUFFICIENT" : "DECISION_INPUT_NOT_CURRENT");
}
