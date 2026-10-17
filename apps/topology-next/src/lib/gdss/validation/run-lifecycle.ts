import type { ValidationRunState } from "./run-contracts";
const edges: Record<ValidationRunState, readonly ValidationRunState[]> = {
  CREATED: ["READY", "FAILED", "INVALIDATED"],
  READY: ["RUNNING", "FAILED", "INVALIDATED"],
  RUNNING: ["COMPLETED", "FAILED", "INVALIDATED"],
  COMPLETED: ["INVALIDATED"],
  FAILED: ["INVALIDATED"],
  INVALIDATED: [],
};
export const canTransitionValidationRun = (
  from: ValidationRunState,
  to: ValidationRunState,
) => edges[from].includes(to);
