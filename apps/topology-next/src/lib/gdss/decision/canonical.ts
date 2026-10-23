import { validationHash, canonicalValidationJson } from "@/lib/gdss/validation";
import {
  decisionProblemDraftInputSchema,
  preferenceDraftInputSchema,
  riskDraftInputSchema,
  type DecisionProblemDraftInput,
  type PreferenceDraftInput,
  type RiskDraftInput,
} from "./contracts";

const scientificContent = <T extends { idempotencyKey: string; identityId: string; predecessorVersionId?: string }>(value: T) => {
  const { idempotencyKey: _idempotency, identityId: _identity, predecessorVersionId: _predecessor, ...semantic } = value;
  return semantic;
};

export function canonicalPreference(value: unknown): PreferenceDraftInput {
  const parsed = preferenceDraftInputSchema.parse(value);
  return { ...parsed, items: [...parsed.items].sort((a, b) => a.objectiveKey.localeCompare(b.objectiveKey)) };
}

export function canonicalRisk(value: unknown): RiskDraftInput {
  const parsed = riskDraftInputSchema.parse(value);
  return { ...parsed, dimensions: [...parsed.dimensions].sort((a, b) => a.key.localeCompare(b.key)) };
}

export function canonicalDecisionProblem(value: unknown): DecisionProblemDraftInput {
  const parsed = decisionProblemDraftInputSchema.parse(value);
  return {
    ...parsed,
    context: {
      ...parsed.context,
      modelBindings: [...parsed.context.modelBindings].sort((a, b) => a.modelVersionId.localeCompare(b.modelVersionId)),
      evidenceBindings: [...parsed.context.evidenceBindings].sort((a, b) => a.evidenceSetId.localeCompare(b.evidenceSetId)),
      targetVariables: [...new Set(parsed.context.targetVariables)].sort(),
    },
    objectives: [...parsed.objectives].sort((a, b) => a.key.localeCompare(b.key)),
    constraints: [...parsed.constraints].sort((a, b) => a.key.localeCompare(b.key)),
    allowedAlternativeProvenance: [...new Set(parsed.allowedAlternativeProvenance)].sort(),
    allowedScenarioMethods: [...new Set(parsed.allowedScenarioMethods)].sort(),
  };
}

export const preferenceProfileHash = (value: unknown) =>
  validationHash("midd:gdss:decision-preference:v1", scientificContent(canonicalPreference(value)));
export const riskProfileHash = (value: unknown) =>
  validationHash("midd:gdss:decision-risk:v1", scientificContent(canonicalRisk(value)));
export const decisionProblemHash = (value: unknown) =>
  validationHash("midd:gdss:decision-problem:v1", scientificContent(canonicalDecisionProblem(value)));
export { canonicalValidationJson as canonicalDecisionJson };
