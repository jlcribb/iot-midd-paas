import { z } from "zod";
import { capabilityScopeSchema } from "@/lib/gdss/validation";

const key = z.string().trim().min(1).max(256);
const text = z.string().trim().min(1).max(4000);
const uuid = z.string().uuid();
const sha = z.string().regex(/^[0-9a-f]{64}$/);
const finite = z.number().finite();
const unit = z.object({ key, revision: z.number().int().positive() }).strict();

export const decisionProblemStates = [
  "DRAFT",
  "REVIEW_REQUIRED",
  "SEALED",
  "EVALUATING",
  "EVALUATED",
  "INVALIDATED",
  "SUPERSEDED",
] as const;
export const preferenceModes = [
  "UNWEIGHTED_PARETO",
  "ORDINAL_PRIORITY",
  "EXPLICIT_NORMALIZED_WEIGHTS",
] as const;
export const riskStates = [
  "ACCEPTABLE",
  "CONDITIONALLY_ACCEPTABLE",
  "UNACCEPTABLE",
  "UNKNOWN",
] as const;

export const decisionIdentityInputSchema = z
  .object({ canonicalKey: key, idempotencyKey: key })
  .strict();

export const decisionObjectiveSchema = z
  .object({
    key,
    direction: z.enum(["MINIMIZE", "MAXIMIZE", "TARGET_RANGE", "MAINTAIN_WITHIN"]),
    quantityKey: key,
    unit,
    target: z.object({ lower: finite.optional(), upper: finite.optional(), exact: finite.optional() }).strict(),
    horizonKey: key,
    criterionVersionId: uuid,
    criterionContentHash: sha,
    aspirationBounds: z.object({ lower: finite.optional(), upper: finite.optional() }).strict(),
    acceptanceBounds: z.object({ lower: finite.optional(), upper: finite.optional() }).strict(),
    required: z.boolean(),
    ordinal: z.number().int().min(0).max(15),
  })
  .strict();

export const decisionConstraintSchema = z
  .object({
    key,
    type: z.enum(["HARD_CONSTRAINT", "SOFT_CONSTRAINT", "ADVISORY_CONSTRAINT"]),
    scope: capabilityScopeSchema,
    predicateMethod: key,
    unit: unit.optional(),
    threshold: z.unknown(),
    requiredInputs: z.array(key).min(1).max(64),
    missingSemantics: z.enum(["FAIL_CLOSED", "REVIEW_REQUIRED", "INCOMPLETE"]),
    provenance: z.object({ kind: z.enum(["HUMAN_PROPOSED", "GOVERNED_DERIVATION"]), reference: key }).strict(),
    explanation: text,
    ordinal: z.number().int().min(0).max(63),
  })
  .strict()
  .superRefine((value, context) => {
    if (value.type === "HARD_CONSTRAINT" && value.missingSemantics !== "FAIL_CLOSED")
      context.addIssue({ code: "custom", message: "UNKNOWN_REQUIRED_HARD_CONSTRAINT_INPUT_FAILS_CLOSED" });
  });

export const preferenceItemSchema = z
  .object({ objectiveKey: key, ordinalPriority: z.number().int().positive().optional(), weight: finite.nonnegative().optional() })
  .strict();

export const preferenceDraftInputSchema = z
  .object({
    semanticVersion: z.literal("GDSS_DECISION_PREFERENCE_V1"),
    identityId: uuid,
    predecessorVersionId: uuid.optional(),
    mode: z.enum(preferenceModes),
    scope: capabilityScopeSchema,
    items: z.array(preferenceItemSchema).min(1).max(16),
    idempotencyKey: key,
  })
  .strict()
  .superRefine((value, context) => {
    const keys = value.items.map((item) => item.objectiveKey);
    if (new Set(keys).size !== keys.length)
      context.addIssue({ code: "custom", message: "duplicate preference objective" });
    if (value.mode === "EXPLICIT_NORMALIZED_WEIGHTS") {
      if (value.items.some((item) => item.weight === undefined))
        context.addIssue({ code: "custom", message: "PREFERENCE_REQUIRED" });
      const total = value.items.reduce((sum, item) => sum + (item.weight ?? 0), 0);
      if (!Number.isFinite(total) || Math.abs(total - 1) > 1e-12)
        context.addIssue({ code: "custom", message: "PREFERENCE_PROFILE_MISMATCH" });
    } else if (value.items.some((item) => item.weight !== undefined)) {
      context.addIssue({ code: "custom", message: "weights require EXPLICIT_NORMALIZED_WEIGHTS" });
    }
    if (value.mode === "ORDINAL_PRIORITY" && value.items.some((item) => item.ordinalPriority === undefined))
      context.addIssue({ code: "custom", message: "PREFERENCE_REQUIRED" });
  });

export const riskDimensionSchema = z
  .object({
    key,
    source: z.object({ kind: key, referenceId: uuid.optional(), referenceHash: sha.optional() }).strict(),
    severity: z.enum(["LOW", "MODERATE", "HIGH", "CRITICAL"]),
    likelihoodKnowledgeState: z.enum(["KNOWN", "BOUNDED", "UNKNOWN"]),
    reversibility: z.enum(["REVERSIBLE", "PARTIALLY_REVERSIBLE", "IRREVERSIBLE", "UNKNOWN"]),
    recoverability: z.enum(["RECOVERABLE", "CONDITIONALLY_RECOVERABLE", "NOT_RECOVERABLE", "UNKNOWN"]),
    uncertainty: z.enum(["CHARACTERIZED", "PARTIAL", "UNKNOWN"]),
    state: z.enum(riskStates),
    unknownHandling: z.enum(["REVIEW_REQUIRED", "FAIL_CLOSED"]),
    acceptanceRule: text,
    scope: capabilityScopeSchema,
    ordinal: z.number().int().min(0).max(255),
  })
  .strict()
  .superRefine((value, context) => {
    if (
      (value.likelihoodKnowledgeState === "UNKNOWN" || value.uncertainty === "UNKNOWN") &&
      value.state !== "UNKNOWN"
    ) context.addIssue({ code: "custom", message: "UNKNOWN_RISK_MUST_REMAIN_UNKNOWN" });
  });

export const riskDraftInputSchema = z
  .object({
    semanticVersion: z.literal("GDSS_DECISION_RISK_V1"),
    identityId: uuid,
    predecessorVersionId: uuid.optional(),
    scope: capabilityScopeSchema,
    dimensions: z.array(riskDimensionSchema).min(1).max(256),
    idempotencyKey: key,
  })
  .strict()
  .superRefine((value, context) => {
    const keys = value.dimensions.map((item) => item.key);
    if (new Set(keys).size !== keys.length)
      context.addIssue({ code: "custom", message: "duplicate risk dimension" });
  });

export const decisionContextSnapshotSchema = z
  .object({
    scope: capabilityScopeSchema,
    modelBindings: z.array(z.object({
      modelVersionId: uuid,
      modelContentHash: sha,
      bindingVersionId: uuid,
      bindingContentHash: sha,
    }).strict()).min(1).max(16),
    evidenceBindings: z.array(z.object({
      evidenceSetId: uuid,
      evidenceSetHash: sha,
      capabilityAssessmentId: uuid,
      capabilityAssessmentHash: sha,
      predictiveClaimId: uuid,
      predictiveClaimHash: sha,
      validityDomainVersionId: uuid,
      validityDomainHash: sha,
    }).strict()).min(1).max(64),
    targetVariables: z.array(key).min(1).max(16),
    decisionHorizon: z.object({ horizonKey: key, startEpochMicros: z.string().regex(/^-?[0-9]+$/).optional(), endEpochMicros: z.string().regex(/^-?[0-9]+$/).optional() }).strict(),
  })
  .strict();

export const decisionProblemDraftInputSchema = z
  .object({
    semanticVersion: z.literal("GDSS_DECISION_PROBLEM_V1"),
    identityId: uuid,
    predecessorVersionId: uuid.optional(),
    context: decisionContextSnapshotSchema,
    objectives: z.array(decisionObjectiveSchema).min(1).max(16, "RESOURCE_LIMIT_EXCEEDED resource=OBJECTIVES_PER_PROBLEM limit=16"),
    constraints: z.array(decisionConstraintSchema).max(64, "RESOURCE_LIMIT_EXCEEDED resource=CONSTRAINTS_PER_PROBLEM limit=64"),
    preferenceProfileVersionId: uuid,
    preferenceProfileHash: sha,
    riskProfileVersionId: uuid,
    riskProfileHash: sha,
    resourceProfile: z.literal("GDSS_DECISION_LIMITS_V1"),
    allowedAlternativeProvenance: z.array(z.enum(["HUMAN_PROPOSED", "DETERMINISTICALLY_GENERATED", "AI_SUGGESTED", "DERIVED_FROM_PRIOR_ALTERNATIVE"])).min(1),
    allowedScenarioMethods: z.array(key).min(1).max(32),
    idempotencyKey: key,
  })
  .strict()
  .superRefine((value, context) => {
    if (new Set(value.objectives.map((item) => item.key)).size !== value.objectives.length)
      context.addIssue({ code: "custom", message: "duplicate objective" });
    if (new Set(value.constraints.map((item) => item.key)).size !== value.constraints.length)
      context.addIssue({ code: "custom", message: "duplicate constraint" });
    if (value.context.scope.horizonKey !== value.context.decisionHorizon.horizonKey)
      context.addIssue({ code: "custom", message: "DECISION_INPUT_NOT_CURRENT" });
    if (!value.context.targetVariables.includes(value.context.scope.targetKey))
      context.addIssue({ code: "custom", message: "DECISION_INPUT_NOT_CURRENT" });
  });

export const decisionTransitionInputSchema = z.object({
  expectedContentHash: sha.optional(),
  reason: text,
  idempotencyKey: key,
  sodException: z.object({ reason: text }).strict().optional(),
}).strict();

export type DecisionProblemState = typeof decisionProblemStates[number];
export type PreferenceMode = typeof preferenceModes[number];
export type DecisionProblemDraftInput = z.infer<typeof decisionProblemDraftInputSchema>;
export type PreferenceDraftInput = z.infer<typeof preferenceDraftInputSchema>;
export type RiskDraftInput = z.infer<typeof riskDraftInputSchema>;
