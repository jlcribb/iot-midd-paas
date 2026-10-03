import type { DimensionDefinition, ModelContent } from "@/lib/gdss/core";
import type { QuantitySemantics, UnitIdentity } from "@/lib/gdss/expression";
import type { SimulationDiagnostic } from "./diagnostics";
import type { GDSS_SIM_LIMITS_V1 } from "./limits";
import type { CONSTRAINT_POLICY, DYNAMIC_SEMANTIC_VERSION, SOLVER_VERSION } from "./versions";

export type DynamicRole = "STATE" | "RATE" | "ALGEBRAIC" | "PARAMETER";
export type BindingLifecycle = "DRAFT" | "PUBLISHED" | "DEPRECATED";
export interface StateBinding { role:"STATE"; stateRef:string; unit:UnitIdentity; dimension:DimensionDefinition; constraintRefs:string[] }
export interface RateBinding { role:"RATE"; rateRef:string; stateRef:string; formulaRef:string; outputRef:string; unit:UnitIdentity; dimension:DimensionDefinition }
export interface AlgebraicBinding { role:"ALGEBRAIC"; algebraicRef:string; formulaRef:string; outputRef:string }
export interface ParameterBinding { role:"PARAMETER"; parameterRef:string }
export interface DynamicBindingContent {
  projectId:string; modelVersionId:string; modelContentHash:string;
  dynamicSemanticVersion:typeof DYNAMIC_SEMANTIC_VERSION;
  states:StateBinding[]; rates:RateBinding[]; algebraics:AlgebraicBinding[];
  parameters:ParameterBinding[]; constraintRefs:string[]; provenanceIdentities:string[];
}
export interface DynamicBindingSnapshot extends DynamicBindingContent {
  bindingId:string; bindingVersionId:string; bindingVersion:number; dynamicBindingHash:string;
  lifecycleStatus:BindingLifecycle; model:ModelContent;
}
export interface ExplicitQuantityInput {
  ref:string; value:number; unit:UnitIdentity; quantitySemantics?:QuantitySemantics; provenanceIdentity:string;
}
export interface TemporalConfiguration {
  start:number; step:number; stepCount:number; timeUnit:UnitIdentity;
  unitConversionCatalogVersion:"GDSS_UNIT_CONVERSION_V2";
}
export interface SimulationInputManifest {
  projectId:string; modelVersionId:string; modelContentHash:string;
  bindingId:string; bindingVersionId:string; bindingVersion:number; dynamicBindingHash:string;
  dynamicSemanticVersion:typeof DYNAMIC_SEMANTIC_VERSION; solverVersion:typeof SOLVER_VERSION;
  initialConditions:ExplicitQuantityInput[]; parameterValues:ExplicitQuantityInput[];
  temporalConfiguration:TemporalConfiguration;
  expressionLanguageVersion:string; evaluatorVersion:string;
  unitConversionCatalogVersion:"GDSS_UNIT_CONVERSION_V2";
  resourceProfile:typeof GDSS_SIM_LIMITS_V1; constraintPolicy:typeof CONSTRAINT_POLICY;
}
export interface SimulationPointState { value:number; unit:UnitIdentity; dimension:DimensionDefinition }
export interface SimulationPoint { stepIndex:number; epistemicKind:"SIMULATED"; states:Record<string,SimulationPointState> }
export interface SimulationTrajectory { completeness:"COMPLETE"|"PARTIAL"; simulationInputHash:string; points:SimulationPoint[] }
export type SimulationStatus = "COMPLETED"|"FAILED";
export type TerminationReason = "END_TIME_REACHED" | "NON_FINITE_STATE" | "NON_FINITE_RATE" | "EXPRESSION_FAILURE" | "DIMENSION_FAILURE" | "CONSTRAINT_VIOLATION" | "RESOURCE_LIMIT_EXCEEDED" | "INVALID_CONFIGURATION" | "INSTANTANEOUS_ALGEBRAIC_LOOP_UNSUPPORTED" | "SOLVER_FAILURE" | "ARTIFACT_INTEGRITY_FAILURE" | "EXECUTION_INTERRUPTED";
export interface SimulationResult {
  status:SimulationStatus; terminationReason:TerminationReason; simulationInputHash:string;
  trajectory:SimulationTrajectory|null; trajectoryHash:string|null; simulationResultHash:string;
  diagnostics:SimulationDiagnostic[]; physicalAuthority:"NONE"; evaluatorOperations:number;
}
export interface FormulaEvaluation { value:number; operations:number }
export interface SimulationProgram {
  binding:DynamicBindingSnapshot; manifest:SimulationInputManifest;
  evaluateAlgebraics(snapshot:Readonly<Record<string,number>>, parameters:Readonly<Record<string,number>>):Record<string,FormulaEvaluation>;
  evaluateRates(snapshot:Readonly<Record<string,number>>, algebraics:Readonly<Record<string,number>>, parameters:Readonly<Record<string,number>>):Record<string,FormulaEvaluation>;
  validateConstraints(candidates:Readonly<Record<string,number>>):{ok:true}|{ok:false;constraintRef:string};
}
