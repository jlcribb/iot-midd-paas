import { createHash, randomUUID } from "node:crypto";
import { binary64Hex, canonicalJson, derivedHash } from "@/lib/gdss/expression/canonical";
import type { DynamicBindingContent, SimulationInputManifest, SimulationResult } from "./contracts";
import type { SimulationDiagnostic } from "./diagnostics";

const by=<T>(select:(value:T)=>string)=>(left:T,right:T)=>select(left).localeCompare(select(right));
export const dynamicBindingHash = (content:DynamicBindingContent) => derivedHash("gdss-dynamic-binding:v1",{...content,states:[...content.states].sort(by(v=>v.stateRef)),rates:[...content.rates].sort(by(v=>v.rateRef)),algebraics:[...content.algebraics].sort(by(v=>v.algebraicRef)),parameters:[...content.parameters].sort(by(v=>v.parameterRef)),constraintRefs:[...content.constraintRefs].sort(),provenanceIdentities:[...content.provenanceIdentities].sort()});
export const simulationInputHash = (manifest:SimulationInputManifest) => derivedHash("gdss-simulation-input:v1",{...manifest,initialConditions:[...manifest.initialConditions].sort(by(v=>v.ref)),parameterValues:[...manifest.parameterValues].sort(by(v=>v.ref))});
export const executionAttemptId = () => randomUUID();
export const trajectoryHash = (bytes:Uint8Array) => createHash("sha256").update(bytes).digest("hex");

function deterministicDiagnostics(diagnostics:readonly SimulationDiagnostic[]) {
  return diagnostics.map(({code,severity,stage,stepIndex,stateRef,rateRef,formulaRef,details}) => ({code,severity,stage,stepIndex,stateRef,rateRef,formulaRef,details}));
}
export function simulationResultHash(input:{simulationInputHash:string;status:SimulationResult["status"];terminationReason:SimulationResult["terminationReason"];completeness:"COMPLETE"|"PARTIAL"|null;trajectoryHash:string|null;diagnostics:readonly SimulationDiagnostic[]}) {
  return derivedHash("gdss-simulation-result:v1",{...input,diagnostics:deterministicDiagnostics(input.diagnostics)});
}
export function canonicalPointValue(value:number) { return {$binary64:binary64Hex(value)}; }
export { canonicalJson };
