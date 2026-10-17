import { z } from "zod";

const key = z.string().trim().min(1).max(256);
const sha = z.string().regex(/^[0-9a-f]{64}$/);
const uuid = z.string().uuid();
const unit = z.object({ key, revision: z.number().int().positive() }).strict();

export const domainAssessmentResults = [
  "WITHIN_VALIDITY_DOMAIN",
  "NEAR_DOMAIN_BOUNDARY",
  "OUTSIDE_VALIDITY_DOMAIN",
  "DOMAIN_UNKNOWN",
] as const;
export const predictivePositions = [
  "INTERPOLATION",
  "BOUNDARY_PREDICTION",
  "EXTRAPOLATION",
  "UNKNOWN_POSITION",
] as const;
export const evidenceRoles = [
  "SUPPORTING",
  "CONTRADICTING",
  "LIMITING",
  "CONTEXTUAL",
  "INVALIDATING",
] as const;
export const evidenceArtifactTypes = [
  "VALIDATION_PROTOCOL_VERSION",
  "PARTITION_PLAN_VERSION",
  "DATASET_SNAPSHOT",
  "VALIDATION_RUN",
  "PREDICTION_PAIR_SET",
  "METRIC_RESULT",
  "BASELINE_COMPARISON_RESULT",
  "UNCERTAINTY_ASSESSMENT",
  "PREDICTION_INTERVAL",
  "INTERVAL_ASSESSMENT",
  "DOMAIN_VALIDITY_ASSESSMENT",
  "PREDICTIVE_POSITION_ASSESSMENT",
  "NEGATIVE_FINDING",
  "EVIDENCE_CONFLICT",
  "EVIDENCE_LIMITATION",
] as const;
export const negativeFindingTypes = [
  "MODEL_UNDERPERFORMS_BASELINE",
  "HIGH_BIAS",
  "LOW_COVERAGE",
  "UNCERTAINTY_INSUFFICIENT",
  "OUTSIDE_VALIDITY_DOMAIN",
  "TEMPORAL_INTEGRITY_UNKNOWN",
  "INDEPENDENCE_COMPROMISED",
] as const;
export const evidenceLimitationTypes = [
  "UNCERTAINTY_PARTIAL",
  "EXTERNAL_VALIDATION_ABSENT",
  "DOMAIN_COVERAGE_NARROW",
  "HOLDOUT_SINGLE_USE_CONSUMED",
  "PLATFORM_ONLY_PROSPECTIVITY",
  "DEPENDENT_GROUP_LIMITATION",
  "NEAR_DUPLICATE_DETECTION_UNAVAILABLE",
  "SPARSE_HORIZON_COVERAGE",
  "DATA_QUALITY_UNKNOWN",
] as const;
export const evidenceConflictTypes = [
  "METRIC_DIRECTION_CONFLICT",
  "BASELINE_COMPARISON_CONFLICT",
  "DOMAIN_SUPPORT_CONFLICT",
  "UNCERTAINTY_CONFLICT",
] as const;
export const evidenceCompletenessStates = [
  "COMPLETE",
  "PARTIAL",
  "INSUFFICIENT",
  "UNKNOWN",
] as const;
export const strengthAxes = [
  "INDEPENDENCE",
  "TEMPORALITY",
  "DOMAIN_COVERAGE",
  "UNCERTAINTY_COMPLETENESS",
  "BASELINE_STRENGTH",
  "REPLICATION",
  "DATA_QUALITY",
] as const;
export const strengthStates = [
  "UNKNOWN",
  "INSUFFICIENT",
  "LIMITED",
  "ADEQUATE",
  "STRONG",
] as const;
export const AI_EVIDENCE_BOUNDARY = {
  maySummarizeEvidence: true,
  maySuggestConflicts: true,
  mayAlterEvidenceSetMembership: false,
  mayUpgradeEvidenceStrength: false,
  mayAuthorizeScientificConclusion: false,
} as const;

export const domainContextValueSchema = z.discriminatedUnion("kind", [
  z
    .object({
      kind: z.literal("NUMERIC"),
      variableKey: key,
      value: z.number().finite(),
      unit,
    })
    .strict(),
  z
    .object({
      kind: z.literal("CATEGORICAL"),
      variableKey: key,
      value: z.string().min(1).max(200),
    })
    .strict(),
  z
    .object({
      kind: z.literal("BOOLEAN"),
      variableKey: key,
      value: z.boolean(),
    })
    .strict(),
  z
    .object({
      kind: z.literal("TEMPORAL"),
      variableKey: key,
      epochMicros: z.string().regex(/^-?[0-9]+$/),
    })
    .strict(),
]);

export const domainContextSnapshotSchema = z
  .object({
    semanticVersion: z.literal("GDSS_DOMAIN_CONTEXT_V1"),
    values: z.array(domainContextValueSchema).max(64),
  })
  .strict()
  .superRefine((value, context) => {
    if (
      new Set(value.values.map((item) => item.variableKey)).size !==
      value.values.length
    )
      context.addIssue({
        code: "custom",
        message: "duplicate context variable",
      });
  });

export const domainAssessmentInputSchema = z
  .object({
    semanticVersion: z.literal("GDSS_DOMAIN_ASSESSMENT_V1"),
    modelVersionId: uuid,
    modelHash: sha,
    validityDomainVersionId: uuid,
    validityDomainHash: sha,
    validationRunId: uuid,
    targetKey: key,
    horizonKey: key,
    contextSnapshot: domainContextSnapshotSchema,
    idempotencyKey: key,
  })
  .strict();

export const supportDimensionSchema = z.discriminatedUnion("kind", [
  z
    .object({
      kind: z.literal("NUMERIC_RANGE"),
      variableKey: key,
      lowerBound: z.number().finite(),
      upperBound: z.number().finite(),
      unit,
      evidenceAssessmentIds: z.array(uuid).min(1).max(10000),
    })
    .strict(),
  z
    .object({
      kind: z.literal("TEMPORAL_RANGE"),
      variableKey: key,
      startEpochMicros: z.string().regex(/^-?[0-9]+$/),
      endEpochMicros: z.string().regex(/^-?[0-9]+$/),
      evidenceAssessmentIds: z.array(uuid).min(1).max(10000),
    })
    .strict(),
  z
    .object({
      kind: z.literal("CATEGORICAL_SET"),
      variableKey: key,
      values: z.array(z.string().min(1).max(200)).min(1).max(128),
      evidenceAssessmentIds: z.array(uuid).min(1).max(10000),
    })
    .strict(),
  z
    .object({
      kind: z.literal("BOOLEAN_SET"),
      variableKey: key,
      values: z.array(z.boolean()).min(1).max(2),
      evidenceAssessmentIds: z.array(uuid).min(1).max(10000),
    })
    .strict(),
]);

export const predictivePositionInputSchema = z
  .object({
    semanticVersion: z.literal("GDSS_PREDICTIVE_POSITION_V1"),
    domainAssessmentId: uuid,
    modelVersionId: uuid,
    validityDomainVersionId: uuid,
    validationRunId: uuid,
    targetKey: key,
    horizonKey: key,
    contextSnapshot: domainContextSnapshotSchema,
    supportDimensions: z.array(supportDimensionSchema).min(1).max(64),
    idempotencyKey: key,
  })
  .strict()
  .superRefine((value, context) => {
    if (
      new Set(value.supportDimensions.map((item) => item.variableKey)).size !==
      value.supportDimensions.length
    )
      context.addIssue({
        code: "custom",
        message: "duplicate support dimension",
      });
    for (const item of value.supportDimensions) {
      if (item.kind === "NUMERIC_RANGE" && item.lowerBound > item.upperBound)
        context.addIssue({
          code: "custom",
          message: "invalid numeric support range",
        });
      if (
        item.kind === "TEMPORAL_RANGE" &&
        BigInt(item.startEpochMicros) > BigInt(item.endEpochMicros)
      )
        context.addIssue({
          code: "custom",
          message: "invalid temporal support range",
        });
    }
  });

const scopedFinding = {
  modelVersionId: uuid,
  protocolVersionId: uuid,
  validityDomainVersionId: uuid,
  targetKey: key,
  horizonKey: key,
  sourceArtifactType: z.enum([
    "VALIDATION_RUN",
    "PREDICTION_PAIR_SET",
    "METRIC_RESULT",
    "BASELINE_COMPARISON_RESULT",
    "UNCERTAINTY_ASSESSMENT",
    "DOMAIN_VALIDITY_ASSESSMENT",
    "PREDICTIVE_POSITION_ASSESSMENT",
  ]),
  sourceArtifactId: uuid,
  sourceArtifactHash: sha,
  description: z.string().trim().min(1).max(4000),
  idempotencyKey: key,
};
export const negativeFindingInputSchema = z
  .object({ ...scopedFinding, findingType: z.enum(negativeFindingTypes) })
  .strict();
export const conflictInputSchema = z
  .object({
    ...scopedFinding,
    conflictType: z.enum(evidenceConflictTypes),
    conflictingArtifactIds: z.array(uuid).min(2).max(64),
  })
  .strict();
export const limitationInputSchema = z
  .object({ ...scopedFinding, limitationType: z.enum(evidenceLimitationTypes) })
  .strict();

export const evidenceSetInputSchema = z
  .object({
    semanticVersion: z.literal("GDSS_PREDICTIVE_EVIDENCE_SET_V1"),
    modelVersionId: uuid,
    modelHash: sha,
    protocolVersionId: uuid,
    protocolHash: sha,
    validityDomainVersionId: uuid,
    validityDomainHash: sha,
    partitionPlanVersionId: uuid,
    partitionPlanHash: sha,
    snapshotId: uuid,
    snapshotHash: sha,
    targetKey: key,
    horizonKey: key,
    validationRunIds: z.array(uuid).min(1).max(100),
    pairSetIds: z.array(uuid).min(1).max(100),
    domainAssessmentIds: z.array(uuid).min(1).max(1000),
    positionAssessmentIds: z.array(uuid).min(1).max(1000),
    idempotencyKey: key,
  })
  .strict();

export type DomainContextSnapshot = z.infer<typeof domainContextSnapshotSchema>;
export type DomainAssessmentInput = z.infer<typeof domainAssessmentInputSchema>;
export type SupportDimension = z.infer<typeof supportDimensionSchema>;
export type PredictivePositionInput = z.infer<
  typeof predictivePositionInputSchema
>;
export type EvidenceSetInput = z.infer<typeof evidenceSetInputSchema>;
export type EvidenceRole = (typeof evidenceRoles)[number];
export type EvidenceArtifactType = (typeof evidenceArtifactTypes)[number];
export type StrengthAxis = (typeof strengthAxes)[number];
export type StrengthState = (typeof strengthStates)[number];
