import type { DecisionProblemState } from "./contracts";
import { DecisionError } from "./diagnostics";

const transitions: Readonly<Record<DecisionProblemState, readonly DecisionProblemState[]>> = {
  DRAFT: ["REVIEW_REQUIRED", "INVALIDATED"],
  REVIEW_REQUIRED: ["SEALED", "INVALIDATED"],
  SEALED: ["EVALUATING", "INVALIDATED", "SUPERSEDED"],
  EVALUATING: ["EVALUATED"],
  EVALUATED: ["SUPERSEDED"],
  INVALIDATED: [],
  SUPERSEDED: [],
};

export function assertDecisionTransition(from: DecisionProblemState, to: DecisionProblemState, phase: "007A" | "FUTURE" = "007A") {
  if (!transitions[from].includes(to) || (phase === "007A" && ["EVALUATING", "EVALUATED", "SUPERSEDED"].includes(to)))
    throw new DecisionError("INVALID_DECISION_LIFECYCLE");
}

export function assertDraftMutable(state: DecisionProblemState) {
  if (state !== "DRAFT") throw new DecisionError("DECISION_PROBLEM_FROZEN");
}

export function hardConstraintResult(inputKnown: boolean, predicateSatisfied: boolean) {
  return inputKnown && predicateSatisfied ? "ADMISSIBLE" as const : "INADMISSIBLE" as const;
}
