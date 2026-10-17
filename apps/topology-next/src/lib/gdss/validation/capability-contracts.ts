import { z } from "zod";

const key = z.string().trim().min(1).max(256);
const sha = z.string().regex(/^[0-9a-f]{64}$/);
const uuid = z.string().uuid();
const epochMicros = z.string().regex(/^-?[0-9]+$/);
const unit = z.object({ key, revision: z.number().int().positive() }).strict();
const metricProfile = z.array(key).min(1).max(16, "RESOURCE_LIMIT_EXCEEDED resource=METRIC_DEFINITIONS_PER_PROTOCOL limit=16");
const baselineProfile = z.array(key).min(1).max(8, "RESOURCE_LIMIT_EXCEEDED resource=BASELINES_PER_PROTOCOL limit=8");

export const capabilityStates = [
  "NOT_EVALUATED",
  "INSUFFICIENT_EVIDENCE",
  "EVIDENCE_OF_LIMITED_CAPABILITY",
  "EVIDENCE_OF_CAPABILITY",
  "CONFLICTING_EVIDENCE",
  "EVIDENCE_OF_FAILURE",
  "INVALIDATED",
] as const;
export const claimStates = [
  "DRAFT",
  "EVIDENCE_ASSEMBLED",
  "REVIEW_REQUIRED",
  "AUTHORIZED",
  "REJECTED",
  "SUPERSEDED",
  "REVOKED",
] as const;
export const claimReviewDecisions = [
  "APPROVE_FOR_AUTHORIZATION",
  "REQUEST_REVISION",
  "REJECT",
] as const;
export const revalidationTriggerTypes = [
  "MODEL_STRUCTURE_CHANGED",
  "FORMULA_CHANGED",
  "PARAMETER_REGIME_CHANGED",
  "NUMERICAL_METHOD_CHANGED",
  "INPUT_DOMAIN_CHANGED",
  "SENSOR_CHANGED",
  "VALIDITY_DOMAIN_CHANGED",
  "HORIZON_CHANGED",
  "DRIFT_DETECTED",
  "CONTRADICTORY_EVIDENCE",
  "BASELINE_CHANGED",
  "METRIC_CHANGED",
] as const;
export const revalidationTriggerStates = [
  "DETECTED",
  "REVIEW_REQUIRED",
  "ACKNOWLEDGED",
  "REVALIDATION_REQUIRED",
  "RESOLVED",
  "INVALIDATED",
] as const;
export const transferOutcomes = [
  "FULL_REVALIDATION_REQUIRED",
  "TRANSFER_REJECTED",
] as const;
export const claimCurrentnessStates = [
  "AUTHORIZED_CURRENT",
  "AUTHORIZED_EXPIRED_REVIEW_REQUIRED",
  "HUMAN_REVIEW_REQUIRED",
  "SUPERSEDED",
  "REVOKED",
  "REJECTED",
  "NOT_AUTHORIZED",
] as const;

export const capabilityDomainConstraintSchema = z.discriminatedUnion("kind", [
  z
    .object({
      kind: z.literal("NUMERIC_RANGE"),
      variableKey: key,
      lowerBound: z.number().finite(),
      upperBound: z.number().finite(),
      lowerInclusive: z.boolean(),
      upperInclusive: z.boolean(),
      unit,
    })
    .strict(),
  z
    .object({
      kind: z.literal("TEMPORAL_RANGE"),
      variableKey: key,
      startEpochMicros: epochMicros,
      endEpochMicros: epochMicros,
    })
    .strict(),
  z
    .object({
      kind: z.literal("CATEGORICAL_SET"),
      variableKey: key,
      values: z.array(z.string().trim().min(1).max(200)).min(1).max(128),
    })
    .strict(),
  z
    .object({
      kind: z.literal("BOOLEAN_SET"),
      variableKey: key,
      values: z.array(z.boolean()).min(1).max(2),
    })
    .strict(),
]);

export const evidencePeriodSchema = z
  .object({ startEpochMicros: epochMicros, endEpochMicros: epochMicros })
  .strict()
  .refine(
    (value) => BigInt(value.startEpochMicros) <= BigInt(value.endEpochMicros),
    "invalid evidence period",
  );

export const capabilityScopeSchema = z
  .object({
    modelVersionId: uuid,
    modelContentHash: sha,
    targetKey: key,
    horizonKey: key,
    validityDomainVersionId: uuid,
    protocolFamily: key,
    metricProfile,
    baselineProfile,
    uncertaintyProfile: z.array(key).min(1).max(32),
    evidencePeriod: evidencePeriodSchema,
    domainConstraints: z.array(capabilityDomainConstraintSchema).min(1).max(64),
  })
  .strict()
  .superRefine((value, context) => {
    if (
      new Set(value.domainConstraints.map((item) => item.variableKey)).size !==
      value.domainConstraints.length
    )
      context.addIssue({ code: "custom", message: "duplicate domain constraint" });
    for (const item of value.domainConstraints) {
      if (item.kind === "NUMERIC_RANGE" && item.lowerBound > item.upperBound)
        context.addIssue({ code: "custom", message: "invalid numeric scope" });
      if (
        item.kind === "TEMPORAL_RANGE" &&
        BigInt(item.startEpochMicros) > BigInt(item.endEpochMicros)
      )
        context.addIssue({ code: "custom", message: "invalid temporal scope" });
    }
  });

export const capabilityAssessmentInputSchema = z
  .object({
    semanticVersion: z.literal("GDSS_CAPABILITY_ASSESSMENT_V1"),
    evidenceSetId: uuid,
    evidenceSetHash: sha,
    assessmentPolicyVersion: z.literal("GDSS_CAPABILITY_POLICY_V1"),
    requestedAction: z.enum(["REGISTER_SCOPE", "EVALUATE"]),
    scope: capabilityScopeSchema,
    predecessorAssessmentId: uuid.optional(),
    idempotencyKey: key,
  })
  .strict();

export const capabilityInvalidationInputSchema = z
  .object({
    assessmentId: uuid,
    causalReference: key,
    reason: z.string().trim().min(1).max(4000),
    idempotencyKey: key,
  })
  .strict();

export const claimIdentityInputSchema = z
  .object({ canonicalKey: key, idempotencyKey: key })
  .strict();

export const claimDraftInputSchema = z
  .object({
    semanticVersion: z.literal("GDSS_PREDICTIVE_CLAIM_V1"),
    claimIdentityId: uuid,
    capabilityAssessmentId: uuid,
    capabilityAssessmentHash: sha,
    claimScope: capabilityScopeSchema,
    templateVersion: z.literal("GDSS_PREDICTIVE_CLAIM_TEMPLATE_V1"),
    validThroughEpochMicros: epochMicros.optional(),
    predecessorClaimId: uuid.optional(),
    idempotencyKey: key,
  })
  .strict();

export const claimDraftUpdateInputSchema = z
  .object({
    claimScope: capabilityScopeSchema,
    validThroughEpochMicros: epochMicros.optional(),
    expectedClaimHash: sha,
    idempotencyKey: key,
  })
  .strict();

export const claimTransitionInputSchema = z
  .object({ expectedClaimHash: sha, reason: key, idempotencyKey: key })
  .strict();

export const claimReviewInputSchema = z
  .object({
    expectedClaimHash: sha,
    decision: z.enum(claimReviewDecisions),
    rationale: z.string().trim().min(1).max(4000),
    scopeFindings: z.array(z.string().trim().min(1).max(1000)).max(64),
    evidenceFindings: z.array(z.string().trim().min(1).max(1000)).max(64),
    idempotencyKey: key,
  })
  .strict();

export const claimAuthorizationInputSchema = z
  .object({
    expectedClaimHash: sha,
    expectedAssessmentHash: sha,
    expectedEvidenceSetHash: sha,
    authorizedScope: capabilityScopeSchema,
    decision: z.literal("AUTHORIZE"),
    sodException: z
      .object({ reason: z.string().trim().min(1).max(2000) })
      .strict()
      .optional(),
    idempotencyKey: key,
  })
  .strict();

export const claimRevocationInputSchema = z
  .object({
    authorizationId: uuid,
    reason: z.string().trim().min(1).max(4000),
    trigger: z.enum(revalidationTriggerTypes),
    idempotencyKey: key,
  })
  .strict();

export const claimSupersessionInputSchema = z
  .object({
    successorClaimId: uuid,
    reason: z.string().trim().min(1).max(4000),
    idempotencyKey: key,
  })
  .strict();

export const revalidationTriggerInputSchema = z
  .object({
    capabilityAssessmentId: uuid,
    claimId: uuid.optional(),
    evidenceSetId: uuid,
    triggerType: z.enum(revalidationTriggerTypes),
    causalArtifactId: uuid,
    causalArtifactHash: sha,
    rationale: z.string().trim().min(1).max(4000),
    idempotencyKey: key,
  })
  .strict();

export const revalidationResolutionInputSchema = z
  .object({
    expectedContentHash: sha,
    resolution: z.enum(["ACKNOWLEDGED", "RESOLVED", "INVALIDATED"]),
    rationale: z.string().trim().min(1).max(4000),
    idempotencyKey: key,
  })
  .strict();

export const evidenceTransferInputSchema = z
  .object({
    sourceModelVersionId: uuid,
    targetModelVersionId: uuid,
    sourceEvidenceSetId: uuid,
    sourceEvidenceSetHash: sha,
    requestedTransferScope: capabilityScopeSchema,
    requestedMode: z.enum([
      "FULL_REVALIDATION",
      "DIRECT_TRANSFER",
      "PARTIAL_REVALIDATION_ALLOWED",
      "EQUIVALENCE_ESTABLISHED",
    ]),
    reason: z.string().trim().min(1).max(4000),
    idempotencyKey: key,
  })
  .strict();

export type CapabilityState = (typeof capabilityStates)[number];
export type ClaimState = (typeof claimStates)[number];
export type CapabilityScope = z.infer<typeof capabilityScopeSchema>;
export type CapabilityAssessmentInput = z.infer<
  typeof capabilityAssessmentInputSchema
>;
export type ClaimDraftInput = z.infer<typeof claimDraftInputSchema>;
export type RevalidationTriggerType = (typeof revalidationTriggerTypes)[number];
export type EvidenceTransferInput = z.infer<typeof evidenceTransferInputSchema>;
