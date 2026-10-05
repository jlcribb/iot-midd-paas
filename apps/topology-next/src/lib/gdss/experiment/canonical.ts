import { createHash,randomUUID } from "node:crypto";
import { TextEncoder } from "node:util";
import { canonicalJson,derivedHash } from "@/lib/gdss/expression/canonical";
import type { ExperimentDesign,ExperimentManifest,ExperimentResult,MaterializedScenario } from "./contracts";
import { COMPARISONS_VERSION,EXPANSION_VERSION,EXPERIMENT_SEMANTIC_VERSION,LIMITS_VERSION,METRICS_VERSION,NUMERIC_VERSION,TEMPORAL_COMPARABILITY_VERSION } from "./versions";
const encoder=new TextEncoder();
const sha=(bytes:Uint8Array)=>createHash("sha256").update(bytes).digest("hex");
const semanticVersions=()=>({experiment:EXPERIMENT_SEMANTIC_VERSION,expansion:EXPANSION_VERSION,metrics:METRICS_VERSION,comparisons:COMPARISONS_VERSION,numeric:NUMERIC_VERSION,temporalComparability:TEMPORAL_COMPARABILITY_VERSION,limits:LIMITS_VERSION});
const designProjection=(d:ExperimentDesign)=>({projectId:d.projectId,researchQuestion:d.researchQuestion,hypothesis:d.hypothesis??null,baseManifest:d.baseManifest,factors:d.factors,controlledInputs:d.controlledInputs,metrics:d.metrics,comparisons:d.comparisons,completenessPolicy:d.completenessPolicy,baselineAssignments:d.baselineAssignments,semanticVersions:semanticVersions(),resourceProfile:d.resourceProfile});
export const experimentDesignHash=(d:ExperimentDesign)=>derivedHash("gdss-experiment-design:v1",designProjection(d));
const scenarioProjection=(s:Omit<MaterializedScenario,"scenarioDefinitionHash">)=>({experimentDesignHash:s.experimentDesignHash,ordinal:s.ordinal,scenarioType:s.scenarioType,factorAssignments:s.factorAssignments,overrides:s.overrides,controlledInputProofHash:s.controlledInputProofHash,simulationInputHash:s.simulationInputHash});
export const scenarioDefinitionHash=(s:Omit<MaterializedScenario,"scenarioDefinitionHash">)=>derivedHash("gdss-experiment-scenario:v1",scenarioProjection(s));
export const controlledInputProofHash=(value:unknown)=>derivedHash("gdss-experiment-controlled-input-proof:v1",value);
export function encodeManifest(value:ExperimentManifest){const bytes=encoder.encode(canonicalJson({schema:"gdss-experiment-execution-manifest:v1",value}));return{bytes,hash:sha(bytes)};}
export function encodeResult(value:ExperimentResult){const bytes=encoder.encode(canonicalJson({schema:"gdss-experiment-result:v1",value}));return{bytes,hash:sha(bytes)};}
export const experimentExecutionAttemptId=()=>randomUUID();
export { canonicalJson,semanticVersions };
