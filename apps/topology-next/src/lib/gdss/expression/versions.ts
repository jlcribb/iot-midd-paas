export const EXPRESSION_LANGUAGE_VERSION = "GDSS_EXPR_V1" as const;
export const EVALUATOR_VERSION = "GDSS_EVALUATOR_V1" as const;
export const UNIT_CONVERSION_CATALOG_VERSION = "GDSS_UNIT_CONVERSION_V1" as const;
export const RESOURCE_LIMITS_PROFILE = "GDSS_EXPR_LIMITS_V1" as const;

export type ExpressionLanguageVersion = typeof EXPRESSION_LANGUAGE_VERSION;
export type EvaluatorVersion = typeof EVALUATOR_VERSION;
export type UnitConversionCatalogVersion = typeof UNIT_CONVERSION_CATALOG_VERSION;
export type ResourceLimitsProfile = typeof RESOURCE_LIMITS_PROFILE;
