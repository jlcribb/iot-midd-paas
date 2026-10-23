import {z} from "zod";

const key=z.string().trim().min(1).max(256),text=z.string().trim().min(1).max(4000),uuid=z.string().uuid(),sha=z.string().regex(/^[0-9a-f]{64}$/),finite=z.number().finite();
const unit=z.object({key,revision:z.number().int().positive()}).strict();
const typed=z.union([z.string().max(2000),finite,z.boolean(),z.null(),z.array(finite).max(256)]);
const forbidden=/(recommended_option|best_alternative|utility_score|decision_score|causal_effect|observed_causal_result|mqtt|amqp|actuator|physical_endpoint|control_command|policy_activation|runtime_deployment)/i;
const rejectForbidden=(v:unknown,c:z.RefinementCtx)=>{if(forbidden.test(JSON.stringify(v)))c.addIssue({code:"custom",message:"SCENARIO_EVALUATION_INCOMPLETE"});};

export const requiredScenarioOutputSchema=z.object({target:key,horizon:key,quantity:key,unit}).strict();
export const scenarioEvaluationInputSchema=z.object({
  semanticVersion:z.literal("GDSS_SCENARIO_EVALUATION_V1"),scenarioDefinitionId:uuid,scenarioHash:sha,
  alternativeVersionId:uuid,alternativeHash:sha,problemVersionId:uuid,problemHash:sha,
  modelVersionId:uuid,modelHash:sha,decisionContextSnapshot:z.record(z.unknown()),inputHash:sha,
  methodVersion:key,methodHash:sha,resourceProfile:z.literal("GDSS_DECISION_LIMITS_V1"),
  executionManifest:z.object({engineContract:z.literal("GDSS_SCIENTIFIC_SIMULATION_V1"),declaredInputs:z.array(key).max(512),requiredOutputs:z.array(requiredScenarioOutputSchema).min(1).max(256),methodParameters:z.array(z.object({key,value:typed}).strict()).max(256),causalClass:z.literal("MODEL_CONDITIONAL_OUTPUT")}).strict(),
  idempotencyKey:key,
}).strict().superRefine(rejectForbidden);

export const scenarioOutcomeSchema=z.object({
  target:key,horizon:key,quantity:key,unit,value:z.discriminatedUnion("kind",[
    z.object({kind:z.literal("NUMERIC"),numericValue:finite}).strict(),
    z.object({kind:z.literal("CATEGORICAL"),categoricalValue:key}).strict(),
    z.object({kind:z.literal("UNKNOWN"),reason:key}).strict(),
  ]),uncertaintyState:z.enum(["CHARACTERIZED","PARTIAL","UNKNOWN"]),
  limitationState:z.enum(["NONE","LIMITED","MISSING"]),provenance:z.literal("EXACT_METHOD_OUTPUT"),outputReference:key,outputHash:sha,
}).strict().superRefine(rejectForbidden);

export const startEvaluationInputSchema=z.object({reason:text,idempotencyKey:key,technicalMetadata:z.object({retryReason:key.optional(),providerClass:z.enum(["LOCAL_SCIENTIFIC","REMOTE_SCIENTIFIC"]).optional()}).strict().default({})}).strict();
export const terminalArtifactSchema=z.object({artifactIdentityId:uuid,canonicalBytes:z.string().max(16*1024*1024),contentHash:sha,mediaType:z.enum(["application/json","application/vnd.midd.scenario-result+json"]),canonicalMetadata:z.object({schemaVersion:z.literal("GDSS_SCENARIO_RESULT_ARTIFACT_V1"),encoding:z.literal("UTF-8"),projectionCount:z.number().int().nonnegative()}).strict()}).strict();
export const completeEvaluationInputSchema=z.object({attemptId:uuid,artifact:terminalArtifactSchema,outcomes:z.array(scenarioOutcomeSchema).max(256),diagnostics:z.array(z.object({code:key,severity:z.enum(["INFO","WARNING","ERROR"]),message:text}).strict()).max(256),limitations:z.array(key).max(256),missingOutputs:z.array(key).max(256),reason:text,idempotencyKey:key}).strict();
export const failEvaluationInputSchema=z.object({attemptId:uuid,diagnostics:z.array(z.object({code:key,severity:z.enum(["WARNING","ERROR"]),message:text}).strict()).min(1).max(256),reason:text,idempotencyKey:key}).strict();
export const invalidateEvaluationInputSchema=z.object({reason:text,idempotencyKey:key}).strict();
export type ScenarioEvaluationInput=z.infer<typeof scenarioEvaluationInputSchema>;
export type ScenarioOutcomeInput=z.infer<typeof scenarioOutcomeSchema>;
export type CompleteEvaluationInput=z.infer<typeof completeEvaluationInputSchema>;
