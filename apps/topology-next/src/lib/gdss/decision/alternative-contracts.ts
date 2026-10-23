import { z } from "zod";
import { capabilityScopeSchema } from "@/lib/gdss/validation";

const key=z.string().trim().min(1).max(256), text=z.string().trim().min(1).max(4000), uuid=z.string().uuid(), sha=z.string().regex(/^[0-9a-f]{64}$/), finite=z.number().finite();
const unit=z.object({key,revision:z.number().int().positive()}).strict();
const typedValue=z.union([z.string().max(1000),finite,z.boolean(),z.null(),z.array(finite).max(256),z.object({lower:finite.optional(),upper:finite.optional()}).strict()]);
const operationalKey=/(mqtt|amqp|actuator|physical_endpoint|control_command|policy_activation|runtime_deployment)/i;
const rejectOperational=(value:unknown,ctx:z.RefinementCtx)=>{if(operationalKey.test(JSON.stringify(value)))ctx.addIssue({code:"custom",message:"OPERATIONAL_PAYLOAD_FORBIDDEN"});};

export const alternativeProvenance=["HUMAN_PROPOSED","DETERMINISTICALLY_GENERATED","AI_SUGGESTED","DERIVED_FROM_PRIOR_ALTERNATIVE"] as const;
export const decisionVariableSchema=z.object({
  semanticVariableRef:key,mode:z.enum(["FIXED","SET_TO","DELTA","RANGE","STRUCTURAL_CHANGE"]),value:typedValue,
  unit:unit.optional(),baselineValue:typedValue.optional(),changeValue:typedValue.optional(),scope:capabilityScopeSchema,ordinal:z.number().int().min(0).max(255),
}).strict().superRefine((v,c)=>{rejectOperational(v,c);if(v.mode==="DELTA"&&v.changeValue===undefined)c.addIssue({code:"custom",message:"DECISION_INPUT_NOT_CURRENT"});if(v.mode==="FIXED"&&v.baselineValue===undefined)c.addIssue({code:"custom",message:"DECISION_INPUT_NOT_CURRENT"});});

export const alternativeIdentityInputSchema=z.object({problemVersionId:uuid,canonicalKey:key,idempotencyKey:key}).strict();
export const alternativeDraftInputSchema=z.object({
  semanticVersion:z.literal("GDSS_DECISION_ALTERNATIVE_V1"),identityId:uuid,predecessorVersionId:uuid.optional(),problemVersionId:uuid,problemContentHash:sha,
  decisionContextSnapshot:z.record(z.unknown()),whatChanges:z.array(key).min(1).max(256),whatRemainsFixed:z.array(key).min(1).max(256),
  variables:z.array(decisionVariableSchema).min(1).max(256),parameterDeltas:z.array(z.object({key,value:typedValue,unit:unit.optional()}).strict()).max(256),
  structuralAssumptions:z.array(z.object({key,type:key,value:typedValue,reference:key.optional(),scope:capabilityScopeSchema,provenance:z.enum(alternativeProvenance)}).strict()).max(256),
  decisionHorizon:z.object({horizonKey:key,startEpochMicros:z.string().regex(/^-?[0-9]+$/).optional(),endEpochMicros:z.string().regex(/^-?[0-9]+$/).optional()}).strict(),
  applicableConstraintKeys:z.array(key).max(64),scope:capabilityScopeSchema,provenance:z.enum(alternativeProvenance),resourceProfile:z.literal("GDSS_DECISION_LIMITS_V1"),idempotencyKey:key,
}).strict().superRefine((v,c)=>{rejectOperational(v,c);const ks=v.variables.map(x=>x.semanticVariableRef);if(new Set(ks).size!==ks.length)c.addIssue({code:"custom",message:"DECISION_INPUT_NOT_CURRENT"});if(new Set(v.applicableConstraintKeys).size!==v.applicableConstraintKeys.length)c.addIssue({code:"custom",message:"DECISION_INPUT_NOT_CURRENT"});});

export const scenarioAssumptionSchema=z.object({key,type:key,value:typedValue,reference:key.optional(),scope:capabilityScopeSchema,provenance:z.enum(alternativeProvenance),explanation:text.optional(),ordinal:z.number().int().min(0).max(255)}).strict();
export const scenarioBoundaryConditionSchema=z.object({variable:key,window:z.object({startEpochMicros:z.string().regex(/^-?[0-9]+$/),endEpochMicros:z.string().regex(/^-?[0-9]+$/)}).strict(),value:typedValue,unit,scope:capabilityScopeSchema,methodSemantics:key,ordinal:z.number().int().min(0).max(255)}).strict();
export const scenarioDraftInputSchema=z.object({
  semanticVersion:z.literal("GDSS_DECISION_SCENARIO_V1"),problemVersionId:uuid,problemContentHash:sha,alternativeVersionId:uuid,alternativeContentHash:sha,
  modelVersionId:uuid,modelContentHash:sha,decisionContextSnapshot:z.record(z.unknown()),inputSnapshotHash:sha,scope:capabilityScopeSchema,
  initialConditions:z.array(z.object({key,value:typedValue,unit:unit.optional()}).strict()).max(256),parameterSet:z.array(z.object({key,value:typedValue,unit:unit.optional()}).strict()).max(256),
  perturbations:z.array(z.object({key,type:key,value:typedValue,scope:capabilityScopeSchema}).strict()).max(256),assumptions:z.array(scenarioAssumptionSchema).max(256),boundaryConditions:z.array(scenarioBoundaryConditionSchema).max(256),
  uncertaintyCondition:z.object({classification:z.enum(["CHARACTERIZED","PARTIAL","UNKNOWN"]),manifest:z.array(z.object({key,value:typedValue}).strict()).max(256)}).strict(),
  counterfactualClassification:z.enum(["BASELINE_CONDITION","SIMULATED_COUNTERFACTUAL"]),methodVersion:key,resourceProfile:z.literal("GDSS_DECISION_LIMITS_V1"),idempotencyKey:key,
}).strict().superRefine((v,c)=>{rejectOperational(v,c);if(/CAUSAL_EFFECT|OBSERVED_CAUSAL_RESULT/i.test(JSON.stringify(v)))c.addIssue({code:"custom",message:"SCENARIO_NOT_ADMISSIBLE"});});

export const alternativeTransitionInputSchema=z.object({expectedContentHash:sha.optional(),reason:text,idempotencyKey:key,sodException:z.object({reason:text}).strict().optional()}).strict();
export type AlternativeDraftInput=z.infer<typeof alternativeDraftInputSchema>;
export type ScenarioDraftInput=z.infer<typeof scenarioDraftInputSchema>;
