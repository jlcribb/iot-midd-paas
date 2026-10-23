import {randomUUID} from "node:crypto";
import {describe,expect,it} from "vitest";
import type {ControlActor} from "@/lib/dto/control-access.dto";
import {
  DECISION_AUTHORITY_BOUNDARY,
  assertDecisionAccess,
  canonicalScenarioEvaluation,
  scenarioEvaluationHash,
  scenarioEvaluationInputSchema,
  scenarioOutcomeHash,
  scenarioOutcomeSchema,
} from "@/lib/gdss/decision";
import {artifactContentHash} from "@/lib/repositories/gdss-scenario-evaluation.repository";

const id=()=>randomUUID(),sha=(c:string)=>c.repeat(64);
const output={target:"tank",horizon:"five_min",quantity:"level",unit:{key:"meter",revision:1}};
const evaluation=(overrides:Record<string,unknown>={})=>({
  semanticVersion:"GDSS_SCENARIO_EVALUATION_V1",scenarioDefinitionId:id(),scenarioHash:sha("a"),alternativeVersionId:id(),alternativeHash:sha("b"),
  problemVersionId:id(),problemHash:sha("c"),modelVersionId:id(),modelHash:sha("d"),decisionContextSnapshot:{scope:"tank"},inputHash:sha("e"),
  methodVersion:"DETERMINISTIC_SIMULATION_V1",methodHash:sha("f"),resourceProfile:"GDSS_DECISION_LIMITS_V1",
  executionManifest:{engineContract:"GDSS_SCIENTIFIC_SIMULATION_V1",declaredInputs:["pump","level"],requiredOutputs:[output],methodParameters:[{key:"step",value:0.1}],causalClass:"MODEL_CONDITIONAL_OUTPUT"},idempotencyKey:"eval-1",...overrides,
});
const outcome=(overrides:Record<string,unknown>={})=>({...output,value:{kind:"NUMERIC",numericValue:4.2},uncertaintyState:"CHARACTERIZED",limitationState:"NONE",provenance:"EXACT_METHOD_OUTPUT",outputReference:"artifact.json#/level",outputHash:sha("9"),...overrides});

describe("GDSS-007C scenario evaluation contracts",()=>{
  it("accepts an exact scientific manifest and normalized outcome",()=>{expect(scenarioEvaluationInputSchema.parse(evaluation()).semanticVersion).toBe("GDSS_SCENARIO_EVALUATION_V1");expect(scenarioOutcomeSchema.parse(outcome()).provenance).toBe("EXACT_METHOD_OUTPUT");});
  it("canonicalizes insertion order for deterministic identity",()=>{const value=evaluation({executionManifest:{engineContract:"GDSS_SCIENTIFIC_SIMULATION_V1",declaredInputs:["z","a"],requiredOutputs:[output,{target:"a",horizon:"one_min",quantity:"flow",unit:{key:"liter_per_second",revision:1}}],methodParameters:[{key:"z",value:2},{key:"a",value:1}],causalClass:"MODEL_CONDITIONAL_OUTPUT"}}),canonical=canonicalScenarioEvaluation(value);expect(canonical.executionManifest.declaredInputs).toEqual(["a","z"]);expect(scenarioEvaluationHash(value)).toBe(scenarioEvaluationHash({...value,executionManifest:{...value.executionManifest,declaredInputs:["a","z"],requiredOutputs:[...value.executionManifest.requiredOutputs].reverse(),methodParameters:[...value.executionManifest.methodParameters].reverse()}}));});
  it("excludes idempotency and execution attempts from scientific identity",()=>{const value=evaluation();expect(scenarioEvaluationHash(value)).toBe(scenarioEvaluationHash({...value,idempotencyKey:"retry-key"}));expect("attemptId" in canonicalScenarioEvaluation(value)).toBe(false);});
  it.each([["scenarioHash",sha("1")],["modelHash",sha("2")],["inputHash",sha("3")],["methodHash",sha("4")]])("changes identity when %s changes",(field,value)=>{const base=evaluation();expect(scenarioEvaluationHash(base)).not.toBe(scenarioEvaluationHash({...base,[field]:value}));});
  it("preserves unknown outputs instead of coercing them",()=>{const parsed=scenarioOutcomeSchema.parse(outcome({value:{kind:"UNKNOWN",reason:"NO_CONVERGENCE"},uncertaintyState:"UNKNOWN",limitationState:"MISSING"}));expect(parsed.value).toEqual({kind:"UNKNOWN",reason:"NO_CONVERGENCE"});});
  it.each([Number.NaN,Number.POSITIVE_INFINITY,Number.NEGATIVE_INFINITY])("rejects unsafe numeric outcome %s",numericValue=>{expect(()=>scenarioOutcomeSchema.parse(outcome({value:{kind:"NUMERIC",numericValue}}))).toThrow();});
  it("distinguishes typed outcome semantics in its hash",()=>{expect(scenarioOutcomeHash(outcome())).not.toBe(scenarioOutcomeHash(outcome({value:{kind:"UNKNOWN",reason:"NOT_AVAILABLE"},uncertaintyState:"UNKNOWN",limitationState:"MISSING"})));});
  it.each(["recommended_option","best_alternative","utility_score","decision_score","causal_effect","mqtt","actuator","policy_activation"])('rejects forbidden shortcut "%s"',field=>{expect(()=>scenarioEvaluationInputSchema.parse({...evaluation(),decisionContextSnapshot:{[field]:true}})).toThrow(/SCENARIO_EVALUATION_INCOMPLETE/);});
  it("rejects criterion/ranking fields as opaque outcome extensions",()=>{expect(()=>scenarioOutcomeSchema.parse({...outcome(),rank:1,score:0.9})).toThrow(/unrecognized/i);});
  it("computes canonical artifact SHA-256",()=>{expect(artifactContentHash('{"level":4.2}')).toMatch(/^[0-9a-f]{64}$/);expect(artifactContentHash('{"level":4.2}')).not.toBe(artifactContentHash('{"level":4.3}'));});
  it("hard-denies AI execution and exports zero fabricated-outcome authority",()=>{const project=id(),ai:ControlActor={user_id:"ai:test",actor_id:"ai:test",display_name:"AI",auth_provider:"ai",auth_source:"oauth_session",role:"admin",project_ids:[project],project_roles:{[project]:"admin"},all_projects:false};expect(()=>assertDecisionAccess(ai,project,"RUN_SCENARIO_EVALUATION")).toThrow(/AI_AUTHORITY_FORBIDDEN/);expect(DECISION_AUTHORITY_BOUNDARY).toMatchObject({RecommendationAuthority:"NONE",aiMayFabricateOutcome:false,aiMayInvalidateEvaluation:false});});
});
