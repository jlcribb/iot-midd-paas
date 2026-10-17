import { validationHash } from "./canonical";
import {
  capabilityAssessmentInputSchema,
  capabilityScopeSchema,
  claimDraftInputSchema,
  type CapabilityAssessmentInput,
  type CapabilityScope,
  type ClaimDraftInput,
} from "./capability-contracts";

export function canonicalCapabilityScope(value: unknown): CapabilityScope {
  const parsed = capabilityScopeSchema.parse(value);
  return {
    ...parsed,
    metricProfile: [...new Set(parsed.metricProfile)].sort(),
    baselineProfile: [...new Set(parsed.baselineProfile)].sort(),
    uncertaintyProfile: [...new Set(parsed.uncertaintyProfile)].sort(),
    domainConstraints: [...parsed.domainConstraints]
      .map((item) => {
        if (item.kind === "CATEGORICAL_SET")
          return { ...item, values: [...new Set(item.values)].sort() };
        if (item.kind === "BOOLEAN_SET")
          return {
            ...item,
            values: [...new Set(item.values)].sort((a, b) => Number(a) - Number(b)),
          };
        return item;
      })
      .sort((a, b) => a.variableKey.localeCompare(b.variableKey)),
  } as CapabilityScope;
}

export function canonicalCapabilityAssessment(
  value: unknown,
): CapabilityAssessmentInput {
  const parsed = capabilityAssessmentInputSchema.parse(value);
  return { ...parsed, scope: canonicalCapabilityScope(parsed.scope) };
}

export function canonicalClaimDraft(value: unknown): ClaimDraftInput {
  const parsed = claimDraftInputSchema.parse(value);
  return { ...parsed, claimScope: canonicalCapabilityScope(parsed.claimScope) };
}

export const capabilityAssessmentHash = (value: unknown) =>
  validationHash("midd:gdss:capability-assessment:v1", value);
export const predictiveClaimHash = (value: unknown) =>
  validationHash("midd:gdss:predictive-claim:v1", value);
export const predictiveClaimReviewHash = (value: unknown) =>
  validationHash("midd:gdss:predictive-claim-review:v1", value);
export const predictiveClaimAuthorizationHash = (value: unknown) =>
  validationHash("midd:gdss:predictive-claim-authorization:v1", value);
export const predictiveClaimRevocationHash = (value: unknown) =>
  validationHash("midd:gdss:predictive-claim-revocation:v1", value);
export const revalidationTriggerAssessmentHash = (value: unknown) =>
  validationHash("midd:gdss:revalidation-trigger-assessment:v1", value);
export const evidenceTransferAssessmentHash = (value: unknown) =>
  validationHash("midd:gdss:evidence-transfer-assessment:v1", value);
