export const EXPRESSION_LANGUAGE_VERSION = "GDSS_EXPR_V1" as const;
export const EVALUATOR_VERSION = "GDSS_EVALUATOR_V1" as const;
export const UNIT_CONVERSION_CATALOG_VERSION_V1 = "GDSS_UNIT_CONVERSION_V1" as const;
export const UNIT_CONVERSION_CATALOG_VERSION_V2 = "GDSS_UNIT_CONVERSION_V2" as const;
// Historical default retained for every pre-extension GDSS-002 caller.
export const UNIT_CONVERSION_CATALOG_VERSION = UNIT_CONVERSION_CATALOG_VERSION_V1;
export const RESOURCE_LIMITS_PROFILE = "GDSS_EXPR_LIMITS_V1" as const;

export type ExpressionLanguageVersion = typeof EXPRESSION_LANGUAGE_VERSION;
export type EvaluatorVersion = typeof EVALUATOR_VERSION;
export type UnitConversionCatalogVersion = typeof UNIT_CONVERSION_CATALOG_VERSION_V1 | typeof UNIT_CONVERSION_CATALOG_VERSION_V2;
export type ResourceLimitsProfile = typeof RESOURCE_LIMITS_PROFILE;
