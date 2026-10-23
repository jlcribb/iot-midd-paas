import {z} from "zod";
import {capabilityScopeSchema} from "@/lib/gdss/validation";

const key=z.string().trim().min(1).max(256),text=z.string().trim().min(1).max(4000),uuid=z.string().uuid(),sha=z.string().regex(/^[0-9a-f]{64}$/),finite=z.number().finite();
export const comparisonUnitSchema=z.object({key,revision:z.number().int().positive()}).strict();
const forbidden=/(overall_score|decision_score|recommendation_score|universal_rank|winner|best_option|automatic_recommendation|mqtt|amqp|actuator|physical_channel|policy_activation|control_engine)/i;
const rejectShortcut=(value:unknown,context:z.RefinementCtx)=>{if(forbidden.test(JSON.stringify(value)))context.addIssue({code:"custom",message:"OPERATIONAL_PAYLOAD_FORBIDDEN"});};

export const criterionDefinitionInputSchema=z.object({
  semanticVersion:z.literal("GDSS_DECISION_CRITERION_V1"),identityId:uuid,predecessorVersionId:uuid.optional(),criterionKey:key,
  direction:z.enum(["MINIMIZE","MAXIMIZE","TARGET_RANGE","MAINTAIN_WITHIN"]),targetKey:key,horizonKey:key,quantityKey:key,unit:comparisonUnitSchema,
  evaluationMethod:z.enum(["DIRECT_OUTCOME_V1","TARGET_DISTANCE_V1","RANGE_COMPLIANCE_V1"]),methodVersion:key,
  requiredInputs:z.array(z.object({target:key,horizon:key,quantity:key,unit:comparisonUnitSchema}).strict()).min(1).max(64),
  missingDataSemantics:z.enum(["UNKNOWN","INCOMPLETE","NOT_APPLICABLE"]),uncertaintySemantics:z.literal("PRESERVE_SOURCE_UNCERTAINTY"),
  targetRange:z.object({lower:finite,upper:finite}).strict().optional(),applicability:capabilityScopeSchema,idempotencyKey:key,
}).strict().superRefine((value,context)=>{if((value.direction==="TARGET_RANGE"||value.direction==="MAINTAIN_WITHIN")&&!value.targetRange)context.addIssue({code:"custom",message:"CRITERION_INPUT_INCOMPATIBLE"});if(value.targetRange&&value.targetRange.lower>value.targetRange.upper)context.addIssue({code:"custom",message:"CRITERION_INPUT_INCOMPATIBLE"});rejectShortcut(value,context);});

export const criterionTransitionInputSchema=z.object({expectedContentHash:sha,reason:text,idempotencyKey:key}).strict();
export const criterionEvaluationRequestSchema=z.object({alternativeVersionId:uuid,criterionVersionId:uuid,scenarioEvaluationId:uuid,outcomeIds:z.array(uuid).max(64).default([]),idempotencyKey:key}).strict();
export const constraintEvaluationRequestSchema=z.object({alternativeVersionId:uuid,constraintId:uuid,scenarioEvaluationId:uuid,outcomeIds:z.array(uuid).max(64).default([]),criterionEvaluationIds:z.array(uuid).max(32).default([]),idempotencyKey:key}).strict();
export const comparisonAssemblyInputSchema=z.object({
  semanticVersion:z.literal("GDSS_DECISION_COMPARISON_V1"),problemVersionId:uuid,problemHash:sha,preferenceProfileVersionId:uuid,preferenceProfileHash:sha,riskProfileVersionId:uuid,riskProfileHash:sha,
  alternativeVersionIds:z.array(uuid).min(1).max(64),criterionVersionIds:z.array(uuid).min(1).max(32,"RESOURCE_LIMIT_EXCEEDED resource=CRITERIA_PER_COMPARISON limit=32"),
  criterionEvaluationIds:z.array(uuid).min(1).max(2048),constraintEvaluationIds:z.array(uuid).max(4096),idempotencyKey:key,
}).strict().superRefine((value,context)=>{for(const list of [value.alternativeVersionIds,value.criterionVersionIds,value.criterionEvaluationIds,value.constraintEvaluationIds])if(new Set(list).size!==list.length)context.addIssue({code:"custom",message:"COMPARISON_SET_INCOMPLETE"});rejectShortcut(value,context);});

export const criterionEvaluationStates=["EVALUATED","UNKNOWN","INCOMPLETE","NOT_APPLICABLE","INVALID"] as const;
export const dominanceStates=["DOMINATES","DOMINATED","NON_DOMINATED","INCOMPARABLE","UNKNOWN"] as const;
export type CriterionDefinitionInput=z.infer<typeof criterionDefinitionInputSchema>;
export type ComparisonAssemblyInput=z.infer<typeof comparisonAssemblyInputSchema>;
export type CriterionEvaluationState=typeof criterionEvaluationStates[number];
export type DominanceState=typeof dominanceStates[number];
