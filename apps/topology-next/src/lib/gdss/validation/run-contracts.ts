import { z } from "zod";

const sha = z.string().regex(/^[0-9a-f]{64}$/);
const key = z.string().trim().min(1).max(256);
const instant = z.string().datetime({ offset: true });
const unit = z.object({ key, revision: z.number().int().positive() }).strict();

export const validationRunModes = [
  "RETROSPECTIVE",
  "PSEUDO_PROSPECTIVE",
  "PROSPECTIVE",
] as const;
export const validationRunStates = [
  "CREATED",
  "READY",
  "RUNNING",
  "COMPLETED",
  "FAILED",
  "INVALIDATED",
] as const;
export const predictionModes = validationRunModes;
export const pairingRules = [
  "EXACT_TIMESTAMP",
  "NEAREST_WITHIN_TOLERANCE",
  "WINDOW_AGGREGATE",
  "EXACT_EVENT_ID",
] as const;
export const pairingDirections = [
  "BIDIRECTIONAL",
  "BEFORE_ONLY",
  "AFTER_ONLY",
] as const;
export const pairIntegrityStates = [
  "PASS",
  "TEMPORAL_INTEGRITY_UNKNOWN",
  "PREDICTION_AFTER_OBSERVATION",
  "TARGET_MISMATCH",
  "HORIZON_MISMATCH",
  "UNIT_MISMATCH",
  "PAIRING_RULE_VIOLATION",
  "OBSERVATION_NOT_ELIGIBLE",
  "INVALIDATED",
] as const;

export const validationRunContentSchema = z
  .object({
    semanticVersion: z.literal("GDSS_VALIDATION_RUN_V1"),
    protocolVersionId: z.string().uuid(),
    protocolHash: sha,
    modelVersionId: z.string().uuid(),
    modelHash: sha,
    partitionPlanVersionId: z.string().uuid(),
    partitionPlanHash: sha,
    snapshotId: z.string().uuid(),
    snapshotHash: sha,
    validityDomainVersionId: z.string().uuid(),
    validityDomainHash: sha,
    holdoutId: z.string().uuid().optional(),
    holdoutEvaluationReferenceId: z.string().uuid().optional(),
    runMode: z.enum(validationRunModes),
    epistemicCutoff: instant.optional(),
  })
  .strict()
  .superRefine((v, c) => {
    if (!!v.holdoutId !== !!v.holdoutEvaluationReferenceId)
      c.addIssue({
        code: "custom",
        message: "holdout and evaluation reference must be bound together",
      });
  });

export const predictionContentSchema = z
  .object({
    semanticVersion: z.literal("GDSS_PREDICTION_V1"),
    modelVersionId: z.string().uuid(),
    modelHash: sha,
    targetKey: key,
    forecastOrigin: instant,
    horizonKey: key,
    horizonDuration: z.number().positive(),
    horizonUnit: unit,
    predictedValue: z.number().finite(),
    predictedUnit: unit,
    inputSnapshotHash: sha,
    parameterSnapshotHash: sha,
    boundaryConditionHash: sha,
    predictionMode: z.enum(predictionModes),
    trajectoryReference: key.optional(),
    trajectoryHash: sha.optional(),
  })
  .strict()
  .superRefine((v, c) => {
    if (!!v.trajectoryReference !== !!v.trajectoryHash)
      c.addIssue({
        code: "custom",
        message: "trajectory reference/hash must be complete",
      });
  });

export const observationReferenceContentSchema = z
  .object({
    semanticVersion: z.literal("GDSS_OBSERVATION_REFERENCE_V1"),
    observationIdentity: key,
    source: key,
    targetKey: key,
    observedValue: z.number().finite(),
    unit,
    measurementTime: instant.nullable(),
    availabilityTime: instant.nullable(),
    ingestionTime: instant.nullable(),
    sourceContentHash: sha,
    qualityProvenanceReference: key.nullable(),
    successorOfId: z.string().uuid().optional(),
  })
  .strict();

export const pairingContractSchema = z
  .object({
    semanticVersion: z.literal("GDSS_PREDICTION_OBSERVATION_PAIR_V1"),
    targetKey: key,
    horizonKey: key,
    pairingRule: z.enum(pairingRules),
    tolerance: z.number().nonnegative().optional(),
    toleranceUnit: unit.optional(),
    directionality: z.enum(pairingDirections).optional(),
    aggregateIdentity: key.optional(),
    eventIdentity: key.optional(),
    conversionIdentity: key.optional(),
    conversionVersion: key.optional(),
  })
  .strict()
  .superRefine((v, c) => {
    const tolerant =
      v.pairingRule === "NEAREST_WITHIN_TOLERANCE" ||
      v.pairingRule === "WINDOW_AGGREGATE";
    if (
      tolerant !==
      (v.tolerance !== undefined && !!v.toleranceUnit && !!v.directionality)
    )
      c.addIssue({
        code: "custom",
        message: "deterministic tolerance contract incomplete",
      });
    if (
      (v.conversionIdentity && !v.conversionVersion) ||
      (!v.conversionIdentity && v.conversionVersion)
    )
      c.addIssue({
        code: "custom",
        message: "conversion identity/version must be complete",
      });
    if (v.pairingRule === "WINDOW_AGGREGATE" && !v.aggregateIdentity)
      c.addIssue({
        code: "custom",
        message: "window aggregate identity required",
      });
    if (v.pairingRule === "EXACT_EVENT_ID" && !v.eventIdentity)
      c.addIssue({ code: "custom", message: "exact event identity required" });
  });

export const pairSetContentSchema = z
  .object({
    semanticVersion: z.literal("GDSS_PREDICTION_PAIR_SET_V1"),
    targetKey: key,
    horizonKey: key,
    scope: key,
    pairHashes: z.array(sha).min(1).max(100000),
  })
  .strict();
export type ValidationRunContent = z.infer<typeof validationRunContentSchema>;
export type PredictionContent = z.infer<typeof predictionContentSchema>;
export type ObservationReferenceContent = z.infer<
  typeof observationReferenceContentSchema
>;
export type PairingContract = z.infer<typeof pairingContractSchema>;
export type PairSetContent = z.infer<typeof pairSetContentSchema>;
export type ValidationRunState = (typeof validationRunStates)[number];
export type PairIntegrityState = (typeof pairIntegrityStates)[number];
