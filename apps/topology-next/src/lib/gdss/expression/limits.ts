import { fail } from "./diagnostics";
import { RESOURCE_LIMITS_PROFILE, type ResourceLimitsProfile } from "./versions";

export interface ExpressionLimits {
  profile: ResourceLimitsProfile;
  sourceLength: number;
  tokenCount: number;
  astDepth: number;
  astNodes: number;
  distinctSymbols: number;
  functionNesting: number;
  dependencyNodes: number;
  dependencyEdges: number;
  suppliedInputs: number;
  evaluatorOperations: number;
}

export const DEFAULT_EXPRESSION_LIMITS: Readonly<ExpressionLimits> = Object.freeze({
  profile: RESOURCE_LIMITS_PROFILE,
  sourceLength: 2000,
  tokenCount: 1024,
  astDepth: 64,
  astNodes: 1024,
  distinctSymbols: 256,
  functionNesting: 32,
  dependencyNodes: 1000,
  dependencyEdges: 10000,
  suppliedInputs: 256,
  evaluatorOperations: 4096
});

export function assertLimit(actual: number, maximum: number, resource: string, stage: "SOURCE" | "PARSED" | "SYMBOL_RESOLVED" | "EVALUABLE") {
  if (actual > maximum) fail("RESOURCE_LIMIT_EXCEEDED", stage, `${resource} exceeds resource limit`, { expected: maximum, actual });
}
