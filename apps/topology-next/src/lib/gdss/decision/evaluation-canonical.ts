import {validationHash,canonicalValidationJson} from "@/lib/gdss/validation";
import {scenarioEvaluationInputSchema,scenarioOutcomeSchema,type ScenarioEvaluationInput,type ScenarioOutcomeInput} from "./evaluation-contracts";
const semantic=<T extends {idempotencyKey:string}>(v:T)=>{const {idempotencyKey:_,...rest}=v;return rest;};
export function canonicalScenarioEvaluation(raw:unknown):ScenarioEvaluationInput{const v=scenarioEvaluationInputSchema.parse(raw);return {...v,executionManifest:{...v.executionManifest,declaredInputs:[...new Set(v.executionManifest.declaredInputs)].sort(),requiredOutputs:[...v.executionManifest.requiredOutputs].sort((a,b)=>`${a.target}:${a.horizon}:${a.quantity}`.localeCompare(`${b.target}:${b.horizon}:${b.quantity}`)),methodParameters:[...v.executionManifest.methodParameters].sort((a,b)=>a.key.localeCompare(b.key))}};}
export const canonicalScenarioEvaluationContent=(raw:unknown)=>semantic(canonicalScenarioEvaluation(raw));
export function canonicalScenarioOutcome(raw:unknown):ScenarioOutcomeInput{return scenarioOutcomeSchema.parse(raw);}
export const scenarioEvaluationHash=(raw:unknown)=>validationHash("midd:gdss:scenario-evaluation:v1",canonicalScenarioEvaluationContent(raw));
export const scenarioOutcomeHash=(raw:unknown)=>validationHash("midd:gdss:scenario-outcome:v1",canonicalScenarioOutcome(raw));
export {canonicalValidationJson as canonicalEvaluationJson};
