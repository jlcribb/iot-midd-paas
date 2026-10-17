import { validationHash } from "./canonical";
import {
  domainAssessmentInputSchema,
  evidenceSetInputSchema,
  predictivePositionInputSchema,
  type DomainAssessmentInput,
  type EvidenceSetInput,
  type PredictivePositionInput,
} from "./evidence-contracts";

export const canonicalDomainAssessment = (
  value: unknown,
): DomainAssessmentInput => {
  const parsed = domainAssessmentInputSchema.parse(value);
  return {
    ...parsed,
    contextSnapshot: {
      ...parsed.contextSnapshot,
      values: [...parsed.contextSnapshot.values].sort((a, b) =>
        a.variableKey.localeCompare(b.variableKey),
      ),
    },
  };
};
export const canonicalPredictivePosition = (
  value: unknown,
): PredictivePositionInput => {
  const parsed = predictivePositionInputSchema.parse(value);
  return {
    ...parsed,
    contextSnapshot: {
      ...parsed.contextSnapshot,
      values: [...parsed.contextSnapshot.values].sort((a, b) =>
        a.variableKey.localeCompare(b.variableKey),
      ),
    },
    supportDimensions: [...parsed.supportDimensions]
      .map((dimension) => ({
        ...dimension,
        evidenceAssessmentIds: [
          ...new Set(dimension.evidenceAssessmentIds),
        ].sort(),
        ...(dimension.kind === "CATEGORICAL_SET"
          ? { values: [...new Set(dimension.values)].sort() }
          : {}),
        ...(dimension.kind === "BOOLEAN_SET"
          ? { values: [...new Set(dimension.values)].sort() }
          : {}),
      }))
      .sort((a, b) => a.variableKey.localeCompare(b.variableKey)),
  } as PredictivePositionInput;
};
export const canonicalEvidenceSetInput = (value: unknown): EvidenceSetInput => {
  const parsed = evidenceSetInputSchema.parse(value);
  return {
    ...parsed,
    validationRunIds: [...new Set(parsed.validationRunIds)].sort(),
    pairSetIds: [...new Set(parsed.pairSetIds)].sort(),
    domainAssessmentIds: [...new Set(parsed.domainAssessmentIds)].sort(),
    positionAssessmentIds: [...new Set(parsed.positionAssessmentIds)].sort(),
  };
};
export const domainAssessmentHash = (value: unknown) =>
  validationHash("gdss006:domain-assessment:v1", value);
export const predictivePositionHash = (value: unknown) =>
  validationHash("gdss006:predictive-position:v1", value);
export const evidenceSetHash = (value: unknown) =>
  validationHash("gdss006:evidence-set:v1", value);
export const evidenceReferenceHash = (value: unknown) =>
  validationHash("gdss006:evidence-reference:v1", value);
export const evidenceLimitationHash = (value: unknown) =>
  validationHash("gdss006:evidence-limitation:v1", value);
export const evidenceConflictHash = (value: unknown) =>
  validationHash("gdss006:evidence-conflict:v1", value);
export const negativeEvidenceHash = (value: unknown) =>
  validationHash("gdss006:negative-evidence:v1", value);
export const evidenceStrengthProfileHash = (value: unknown) =>
  validationHash("gdss006:evidence-strength-profile:v1", value);
