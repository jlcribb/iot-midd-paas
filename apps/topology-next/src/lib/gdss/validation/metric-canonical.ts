import { canonicalValidationJson, validationHash } from "./canonical";
import {
  baselineDefinitionContentSchema,
  comparisonRuleSchema,
  metricDefinitionContentSchema,
  predictionIntervalContentSchema,
  uncertaintyAssessmentContentSchema,
  type BaselineDefinitionContent,
  type ComparisonRule,
  type MetricDefinitionContent,
  type PredictionIntervalContent,
  type UncertaintyAssessmentContent,
} from "./metric-contracts";
export const canonicalMetricDefinition = (
  v: unknown,
): MetricDefinitionContent => metricDefinitionContentSchema.parse(v);
export const canonicalBaselineDefinition = (
  v: unknown,
): BaselineDefinitionContent => baselineDefinitionContentSchema.parse(v);
export const canonicalUncertaintyAssessment = (
  v: unknown,
): UncertaintyAssessmentContent => {
  const x = uncertaintyAssessmentContentSchema.parse(v);
  return {
    ...x,
    assumptions: [...x.assumptions].sort(),
    dependencies: [...x.dependencies].sort(),
  };
};
export const canonicalPredictionInterval = (
  v: unknown,
): PredictionIntervalContent => predictionIntervalContentSchema.parse(v);
export const canonicalComparisonRule = (v: unknown): ComparisonRule =>
  comparisonRuleSchema.parse(v);
export const metricDefinitionHash = (v: unknown) =>
  validationHash("gdss006:metric-definition:v1", canonicalMetricDefinition(v));
export const metricResultHash = (v: unknown) =>
  validationHash("gdss006:metric-result:v1", v);
export const baselineHash = (v: unknown) =>
  validationHash("gdss006:baseline:v1", canonicalBaselineDefinition(v));
export const baselinePredictionHash = (v: unknown) =>
  validationHash("gdss006:baseline-prediction:v1", v);
export const baselineResultHash = (v: unknown) =>
  validationHash("gdss006:baseline-result:v1", v);
export const baselineComparisonHash = (v: unknown) =>
  validationHash("gdss006:baseline-comparison:v1", v);
export const uncertaintySourceHash = (v: unknown) =>
  validationHash("gdss006:uncertainty-source:v1", v);
export const uncertaintyAssessmentHash = (v: unknown) =>
  validationHash(
    "gdss006:uncertainty-assessment:v1",
    canonicalUncertaintyAssessment(v),
  );
export const predictionIntervalHash = (v: unknown) =>
  validationHash(
    "gdss006:prediction-interval:v1",
    canonicalPredictionInterval(v),
  );
export const intervalAssessmentHash = (v: unknown) =>
  validationHash("gdss006:interval-assessment:v1", v);
export { canonicalValidationJson };
