import { z } from "zod";

const sha = z.string().regex(/^[0-9a-f]{64}$/),
  key = z.string().trim().min(1).max(256),
  instant = z.string().datetime({ offset: true }),
  unit = z.object({ key, revision: z.number().int().positive() }).strict();
export const metricKeys = [
  "MAE_V1",
  "RMSE_V1",
  "BIAS_V1",
  "SMAPE_V1",
  "TRAJECTORY_RMSE_V1",
  "PEAK_MAGNITUDE_ERROR_V1",
  "PEAK_TIMING_ERROR_V1",
  "STEADY_STATE_DEVIATION_V1",
  "INTERVAL_COVERAGE_V1",
  "MEAN_INTERVAL_WIDTH_V1",
] as const;
export const metricCategories = [
  "POINT_ERROR",
  "RELATIVE_ERROR",
  "TRAJECTORY",
  "DYNAMIC_RESPONSE",
  "INTERVAL",
] as const;
export const baselineKeys = [
  "NAIVE_LAST_VALUE_V1",
  "HISTORICAL_MEAN_V1",
  "SEASONAL_NAIVE_V1",
  "AUTHORIZED_REFERENCE_MODEL_V1",
] as const;
export const uncertaintySourceTypes = [
  "MEASUREMENT_UNCERTAINTY",
  "PARAMETER_UNCERTAINTY",
  "INITIAL_CONDITION_UNCERTAINTY",
  "INPUT_UNCERTAINTY",
  "MODEL_STRUCTURAL_UNCERTAINTY",
  "NUMERICAL_UNCERTAINTY",
  "PREDICTIVE_UNCERTAINTY",
  "DOMAIN_UNCERTAINTY",
] as const;
export const uncertaintyKnowledgeStates = [
  "KNOWN_QUANTIFIED",
  "KNOWN_UNQUANTIFIED",
  "UNKNOWN",
  "NOT_APPLICABLE",
] as const;
export const uncertaintyMethods = [
  "DECLARED_BOUNDS",
  "SUPPLIED_INTERVAL",
  "EMPIRICAL_COVERAGE",
] as const;
export const completenessStates = [
  "COMPLETE_FOR_DECLARED_SCOPE",
  "PARTIAL",
  "INSUFFICIENT",
  "UNKNOWN",
] as const;
export const comparisonStates = [
  "MODEL_OUTPERFORMS_BASELINE",
  "MODEL_EQUIVALENT_TO_BASELINE",
  "MODEL_UNDERPERFORMS_BASELINE",
  "INCONCLUSIVE",
] as const;

export const metricDefinitionContentSchema = z
  .object({
    semanticVersion: z.literal("GDSS_METRIC_DEFINITION_V1"),
    metricKey: z.enum(metricKeys),
    name: key,
    category: z.enum(metricCategories),
    formulaVersion: key,
    directionality: z.enum([
      "LOWER_IS_BETTER",
      "HIGHER_IS_BETTER",
      "CLOSER_TO_ZERO_IS_BETTER",
    ]),
    requiredInputs: z.array(key).min(1),
    unitSemantics: key,
    aggregationSemantics: key,
    missingnessBehavior: z.enum(["REJECT", "GOVERNED_PAIR_SET_ONLY"]),
    validityConstraints: z.array(key),
    implementationIdentifier: key,
    smapeDenominatorFloor: z.number().positive().optional(),
    bothZeroTreatment: z.enum(["ZERO_CONTRIBUTION"]).optional(),
    minimumCoverage: z.number().min(0).max(1).optional(),
    peakTimingSigned: z.boolean().optional(),
    steadyStateWindowCount: z.number().int().positive().optional(),
    steadyStateTolerance: z.number().nonnegative().optional(),
  })
  .strict()
  .superRefine((v, c) => {
    if (
      v.metricKey === "SMAPE_V1" &&
      (!v.smapeDenominatorFloor || !v.bothZeroTreatment)
    )
      c.addIssue({ code: "custom", message: "SMAPE contract incomplete" });
    if (
      v.metricKey === "STEADY_STATE_DEVIATION_V1" &&
      (!v.steadyStateWindowCount || v.steadyStateTolerance === undefined)
    )
      c.addIssue({
        code: "custom",
        message: "steady-state contract incomplete",
      });
  });
export const baselineDefinitionContentSchema = z
  .object({
    semanticVersion: z.literal("GDSS_BASELINE_V1"),
    baselineKey: z.enum(baselineKeys),
    name: key,
    algorithmVersion: key,
    targetKey: key,
    horizonKey: key,
    inputPolicy: key,
    referenceWindowStart: instant.optional(),
    referenceWindowEnd: instant.optional(),
    seasonalOffset: z.number().positive().optional(),
    seasonalUnit: unit.optional(),
    lookupRule: z.enum(["EXACT", "NEAREST_BEFORE"]).optional(),
    missingFallback: z.enum(["REJECT", "HISTORICAL_MEAN"]).optional(),
    referenceModelVersionId: z.string().uuid().optional(),
    referenceModelHash: sha.optional(),
  })
  .strict()
  .superRefine((v, c) => {
    if (
      v.referenceWindowStart &&
      v.referenceWindowEnd &&
      v.referenceWindowStart > v.referenceWindowEnd
    )
      c.addIssue({ code: "custom", message: "historical window reversed" });
    if (
      v.baselineKey === "HISTORICAL_MEAN_V1" &&
      (!v.referenceWindowStart || !v.referenceWindowEnd)
    )
      c.addIssue({ code: "custom", message: "historical window required" });
    if (
      v.baselineKey === "SEASONAL_NAIVE_V1" &&
      (!v.seasonalOffset ||
        !v.seasonalUnit ||
        !v.lookupRule ||
        !v.missingFallback)
    )
      c.addIssue({ code: "custom", message: "seasonal contract incomplete" });
    if (
      v.baselineKey === "AUTHORIZED_REFERENCE_MODEL_V1" &&
      (!v.referenceModelVersionId || !v.referenceModelHash)
    )
      c.addIssue({ code: "custom", message: "exact reference model required" });
  });
export const uncertaintyAssessmentContentSchema = z
  .object({
    semanticVersion: z.literal("GDSS_UNCERTAINTY_ASSESSMENT_V1"),
    sourceType: z.enum(uncertaintySourceTypes),
    knowledgeState: z.enum(uncertaintyKnowledgeStates),
    method: z.enum(uncertaintyMethods).nullable(),
    lowerBound: z.number().finite().optional(),
    upperBound: z.number().finite().optional(),
    distributionReference: key.optional(),
    unit: unit.nullable(),
    assumptions: z.array(key),
    dependencies: z.array(key),
    coverageTarget: z.number().min(0).max(1).nullable(),
    qualityProvenanceReference: key.nullable(),
    scope: key,
  })
  .strict()
  .superRefine((v, c) => {
    const quantified =
      v.lowerBound !== undefined ||
      v.upperBound !== undefined ||
      !!v.distributionReference;
    if (v.knowledgeState === "UNKNOWN" && quantified)
      c.addIssue({
        code: "custom",
        message: "unknown uncertainty cannot fabricate zero/bounds",
      });
    if (v.knowledgeState === "KNOWN_QUANTIFIED" && !quantified)
      c.addIssue({
        code: "custom",
        message: "quantified state requires quantity",
      });
    if ((v.lowerBound === undefined) !== (v.upperBound === undefined))
      c.addIssue({ code: "custom", message: "bounds must be complete" });
    if (
      v.lowerBound !== undefined &&
      v.upperBound !== undefined &&
      v.lowerBound > v.upperBound
    )
      c.addIssue({ code: "custom", message: "uncertainty bounds reversed" });
  });
export const predictionIntervalContentSchema = z
  .object({
    semanticVersion: z.literal("GDSS_PREDICTION_INTERVAL_V1"),
    predictionId: z.string().uuid(),
    lowerBound: z.number().finite(),
    upperBound: z.number().finite(),
    coverageLevel: z.number().gt(0).lt(1),
    unit,
    method: z.enum(["DECLARED_BOUNDS", "SUPPLIED_INTERVAL"]),
    methodVersion: key,
  })
  .strict()
  .superRefine((v, c) => {
    if (v.lowerBound > v.upperBound)
      c.addIssue({ code: "custom", message: "interval bounds reversed" });
  });
export const comparisonRuleSchema = z
  .object({
    semanticVersion: z.literal("GDSS_BASELINE_COMPARISON_RULE_V1"),
    tolerance: z.number().nonnegative(),
    unit: unit,
    metricKey: z.enum(metricKeys),
    directionality: z.enum([
      "LOWER_IS_BETTER",
      "HIGHER_IS_BETTER",
      "CLOSER_TO_ZERO_IS_BETTER",
    ]),
  })
  .strict();
export type MetricDefinitionContent = z.infer<
  typeof metricDefinitionContentSchema
>;
export type BaselineDefinitionContent = z.infer<
  typeof baselineDefinitionContentSchema
>;
export type UncertaintyAssessmentContent = z.infer<
  typeof uncertaintyAssessmentContentSchema
>;
export type PredictionIntervalContent = z.infer<
  typeof predictionIntervalContentSchema
>;
export type ComparisonRule = z.infer<typeof comparisonRuleSchema>;
export type MetricKey = (typeof metricKeys)[number];
export type UncertaintyKnowledgeState =
  (typeof uncertaintyKnowledgeStates)[number];
