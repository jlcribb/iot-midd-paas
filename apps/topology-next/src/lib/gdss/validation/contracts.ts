import { z } from "zod";

const key = z.string().trim().min(1).max(128).regex(/^[A-Za-z][A-Za-z0-9_.:-]*$/);
const sha256 = z.string().regex(/^[0-9a-f]{64}$/);
const unit = z.object({ key, revision: z.number().int().positive() }).strict();
const finite = z.number().finite();
export const GDSS_VALIDATION_RESOURCE_LIMITS = {
  metricDefinitionsPerProtocol: 16,
  baselinesPerProtocol: 8,
} as const;

export const protocolStates = ["DRAFT","REVIEW_REQUIRED","APPROVED","SEALED","SUPERSEDED","INVALIDATED"] as const;
export const domainStates = ["DRAFT","APPROVED","SEALED","SUPERSEDED","INVALIDATED"] as const;
export type ProtocolState = typeof protocolStates[number];
export type DomainState = typeof domainStates[number];

export const validationTargetSchema = z.object({
  targetKey:key, variableReference:key, unitReference:unit,
  aggregation:z.enum(["NONE","MEAN","SUM","MIN","MAX"]),
  transformation:z.enum(["IDENTITY","DECLARED_REFERENCE"]),
  transformationReference:key.optional(),
  semanticRole:z.enum(["OBSERVED_TARGET","DERIVED_TARGET"])
}).strict().superRefine((value,ctx)=>{
  if((value.transformation==="DECLARED_REFERENCE")!==Boolean(value.transformationReference))
    ctx.addIssue({code:"custom",message:"INVALID_TARGET_TRANSFORMATION"});
});

export const validationHorizonSchema = z.object({
  horizonKey:key, duration:finite.positive(), unit:unit,
  forecastOriginSemantics:z.enum(["RUN_START","EXPLICIT_ORIGIN","ROLLING_ORIGIN"])
}).strict();

export const acceptanceCriterionSchema = z.object({
  criterionKey:key, metricKey:key, metricVersion:key,
  operator:z.enum(["LT","LTE","GT","GTE","EQ"]), threshold:finite,
  unit:unit.nullable(), scope:z.enum(["GLOBAL","TARGET","HORIZON","TARGET_HORIZON","SUBGROUP"]),
  scopeReference:key.nullable(), required:z.boolean()
}).strict().superRefine((value,ctx)=>{
  if((value.scope==="GLOBAL")!== (value.scopeReference===null))
    ctx.addIssue({code:"custom",message:"INVALID_ACCEPTANCE_SCOPE"});
});

export const exclusionPolicySchema = z.object({
  version:z.literal("GDSS_VALIDATION_EXCLUSION_V1"),
  rules:z.array(z.object({ruleKey:key,criterion:z.string().trim().min(1).max(1000),justification:z.string().trim().min(1).max(2000)}).strict()).max(64)
}).strict();
export const missingnessPolicySchema = z.object({
  version:z.literal("GDSS_VALIDATION_MISSINGNESS_V1"),
  mode:z.enum(["REJECT","ALLOW_WITH_LIMIT","IMPUTE_DECLARED_METHOD","MARK_INCONCLUSIVE"]),
  maximumFraction:finite.min(0).max(1).optional(), declaredMethod:key.optional()
}).strict().superRefine((value,ctx)=>{
  if(value.mode==="ALLOW_WITH_LIMIT"&&value.maximumFraction===undefined)ctx.addIssue({code:"custom",message:"MISSINGNESS_LIMIT_REQUIRED"});
  if(value.mode==="IMPUTE_DECLARED_METHOD"&&!value.declaredMethod)ctx.addIssue({code:"custom",message:"IMPUTATION_METHOD_REQUIRED"});
  if(value.mode!=="IMPUTE_DECLARED_METHOD"&&value.declaredMethod)ctx.addIssue({code:"custom",message:"IMPUTATION_METHOD_FORBIDDEN"});
});
export const outlierPolicySchema = z.object({
  version:z.literal("GDSS_VALIDATION_OUTLIER_V1"),
  mode:z.enum(["INCLUDE","EXCLUDE_BY_DECLARED_RULE","WINSORIZE_DECLARED","FLAG_ONLY"]),
  declaredRule:key.optional()
}).strict().superRefine((value,ctx)=>{
  if(["EXCLUDE_BY_DECLARED_RULE","WINSORIZE_DECLARED"].includes(value.mode)!==Boolean(value.declaredRule))ctx.addIssue({code:"custom",message:"OUTLIER_RULE_MISMATCH"});
});
export const multiplicityPolicySchema = z.object({
  version:z.literal("GDSS_VALIDATION_MULTIPLICITY_V1"),
  mode:z.enum(["NONE","DECLARED_MULTIPLE_TARGETS","DECLARED_MULTIPLE_HORIZONS","CORRECTION_REQUIRED"]),
  correctionMethod:key.optional()
}).strict().superRefine((value,ctx)=>{
  if((value.mode==="CORRECTION_REQUIRED")!==Boolean(value.correctionMethod))ctx.addIssue({code:"custom",message:"MULTIPLICITY_METHOD_MISMATCH"});
});

export const revalidationTriggerSchema = z.enum([
  "MODEL_STRUCTURE_CHANGED","FORMULA_CHANGED","PARAMETER_REGIME_CHANGED","NUMERICAL_METHOD_CHANGED",
  "INPUT_DOMAIN_CHANGED","SENSOR_CHANGED","VALIDITY_DOMAIN_CHANGED","HORIZON_CHANGED","DRIFT_DETECTED",
  "CONTRADICTORY_EVIDENCE","BASELINE_CHANGED","METRIC_CHANGED"
]);

const basePredicate = {predicateKey:key,variableKey:key,unit:unit.nullable(),rationale:z.string().trim().min(1).max(2000)};
export const domainPredicateSchema = z.discriminatedUnion("predicateType",[
  z.object({...basePredicate,predicateType:z.literal("NUMERIC_RANGE"),lowerBound:finite,upperBound:finite,lowerInclusive:z.boolean(),upperInclusive:z.boolean()}).strict(),
  z.object({...basePredicate,predicateType:z.literal("PARAMETER_RANGE"),lowerBound:finite,upperBound:finite,lowerInclusive:z.boolean(),upperInclusive:z.boolean()}).strict(),
  z.object({...basePredicate,predicateType:z.literal("TEMPORAL_RANGE"),startEpochMicros:z.string().regex(/^-?[0-9]+$/),endEpochMicros:z.string().regex(/^-?[0-9]+$/)}).strict(),
  z.object({...basePredicate,predicateType:z.literal("CATEGORICAL_MEMBERSHIP"),unit:z.null(),allowedValues:z.array(z.string().min(1).max(200)).min(1).max(128)}).strict(),
  z.object({...basePredicate,predicateType:z.literal("BOOLEAN_CONDITION"),unit:z.null(),expected:z.boolean()}).strict()
]).superRefine((value,ctx)=>{
  if("lowerBound" in value&&value.lowerBound>value.upperBound)ctx.addIssue({code:"custom",message:"INVALID_DOMAIN_RANGE"});
  if("startEpochMicros" in value&&BigInt(value.startEpochMicros)>BigInt(value.endEpochMicros))ctx.addIssue({code:"custom",message:"INVALID_TEMPORAL_RANGE"});
  if("allowedValues" in value&&new Set(value.allowedValues).size!==value.allowedValues.length)ctx.addIssue({code:"custom",message:"DUPLICATE_ALLOWED_VALUE"});
});
export const domainBoundarySchema = z.object({
  boundaryKey:key, kind:z.enum(["HARD","DECLARED_OPERATIONAL","UNKNOWN"]),
  predicateKeys:z.array(key).min(1).max(64), description:z.string().trim().min(1).max(2000)
}).strict();

export const validityDomainContentSchema = z.object({
  semanticVersion:z.literal("GDSS_VALIDITY_DOMAIN_V1"), description:z.string().trim().min(1).max(10000),
  predicates:z.array(domainPredicateSchema).min(1).max(64), boundaries:z.array(domainBoundarySchema).min(1).max(64)
}).strict().superRefine((value,ctx)=>{
  const keys=new Set(value.predicates.map(item=>item.predicateKey));
  if(keys.size!==value.predicates.length)ctx.addIssue({code:"custom",message:"DUPLICATE_DOMAIN_PREDICATE"});
  for(const boundary of value.boundaries)for(const ref of boundary.predicateKeys)if(!keys.has(ref))ctx.addIssue({code:"custom",message:"UNKNOWN_BOUNDARY_PREDICATE"});
});

export const validationProtocolContentSchema = z.object({
  semanticVersion:z.literal("GDSS_VALIDATION_PROTOCOL_V1"),
  modelIdentityId:z.string().uuid(), modelVersionId:z.string().uuid(), modelVersionNumber:z.number().int().positive(), modelContentHash:sha256,
  validityDomainVersionId:z.string().uuid(), validityDomainHash:sha256,
  targets:z.array(validationTargetSchema).min(1).max(16), horizons:z.array(validationHorizonSchema).min(1).max(16),
  acceptanceCriteria:z.array(acceptanceCriterionSchema).min(1).max(64),
  exclusionPolicy:exclusionPolicySchema, missingnessPolicy:missingnessPolicySchema,
  outlierPolicy:outlierPolicySchema, multiplicityPolicy:multiplicityPolicySchema,
  revalidationTriggers:z.array(revalidationTriggerSchema).min(1).max(12)
}).strict().superRefine((value,ctx)=>{
  for(const items of [value.targets.map(v=>v.targetKey),value.horizons.map(v=>v.horizonKey),value.acceptanceCriteria.map(v=>v.criterionKey)])
    if(new Set(items).size!==items.length)ctx.addIssue({code:"custom",message:"DUPLICATE_PROTOCOL_KEY"});
  if(new Set(value.revalidationTriggers).size!==value.revalidationTriggers.length)ctx.addIssue({code:"custom",message:"DUPLICATE_REVALIDATION_TRIGGER"});
  const metricDefinitions=new Set(value.acceptanceCriteria.map(item=>`${item.metricKey}\u0000${item.metricVersion}`));
  if(metricDefinitions.size>GDSS_VALIDATION_RESOURCE_LIMITS.metricDefinitionsPerProtocol)ctx.addIssue({code:"custom",message:"RESOURCE_LIMIT_EXCEEDED resource=METRIC_DEFINITIONS_PER_PROTOCOL limit=16 actual="+metricDefinitions.size,path:["acceptanceCriteria"]});
});

export type ValidationProtocolContent=z.infer<typeof validationProtocolContentSchema>;
export type ValidityDomainContent=z.infer<typeof validityDomainContentSchema>;
export type DomainPredicate=z.infer<typeof domainPredicateSchema>;
