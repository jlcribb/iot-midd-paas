import type { DimensionDefinition } from "@/lib/gdss/core";
import type { QuantitySemantics,UnitIdentity } from "@/lib/gdss/expression";
import type { SimulationInputManifest,SimulationPoint,SimulationTrajectory } from "@/lib/gdss/simulation";
import type { GDSS_EXPERIMENT_LIMITS_V1 } from "./limits";

export type ExperimentLifecycle="DRAFT"|"VALIDATED"|"PUBLISHED"|"DEPRECATED";
export type ScenarioType="BASELINE"|"ALTERNATIVE"|"COUNTERFACTUAL";
export type OverrideTargetKind="PARAMETER"|"INITIAL_CONDITION"|"TEMPORAL_CONFIGURATION";
export type CompletenessPolicy="ALL_REQUIRED_SCENARIOS"|"ALLOW_PARTIAL_EXPLICIT";
export type ExperimentTerminalStatus="COMPLETED"|"COMPLETED_WITH_FAILURES"|"FAILED"|"ABORTED";
export type ScenarioDispatchState="PENDING"|"CLAIMED"|"DISPATCHED"|"TERMINAL_SUCCESS"|"TERMINAL_FAILURE"|"NOT_DISPATCHED_ABORTED";
export type MetricOperation="INITIAL_VALUE"|"FINAL_VALUE"|"MINIMUM"|"MAXIMUM"|"ARITHMETIC_POINT_MEAN"|"LEFT_RECTANGLE_INTEGRAL"|"PEAK_STEP"|"TIME_TO_THRESHOLD";
export type ComparisonOperation="ABSOLUTE_DIFFERENCE"|"RELATIVE_DIFFERENCE"|"PERCENT_DIFFERENCE"|"ORDERING";
export type ThresholdDirection="AT_OR_ABOVE"|"ABOVE"|"AT_OR_BELOW"|"BELOW";
export interface ExperimentValue { value:number; unit?:UnitIdentity; quantitySemantics?:QuantitySemantics; provenanceIdentity:string; scenarioType?:ScenarioType }
export interface ExperimentalFactor { factorKey:string; targetKind:OverrideTargetKind; targetIdentity:string; values:ExperimentValue[] }
export interface ControlledInput { targetKind:OverrideTargetKind; targetIdentity:string; expectedGovernedValue:ExperimentValue }
export interface MetricDefinition { key:string; operation:MetricOperation; stateSymbol:string; expectedUnit:UnitIdentity; expectedDimension:DimensionDefinition; requiredCompleteness:"COMPLETE"|"PARTIAL"; threshold?:{value:number;unit:UnitIdentity;direction:ThresholdDirection} }
export interface ComparisonDefinition { key:string; operation:ComparisonOperation; metricKey:string; referenceScenarioOrdinal:number; targetScenarioOrdinal:number; requiredScenarioOrdinals:number[] }
export interface ExperimentDesign { projectId:string; experimentVersionId:string; lifecycleStatus:ExperimentLifecycle; researchQuestion:string; hypothesis?:string; baseManifest:SimulationInputManifest; factors:ExperimentalFactor[]; controlledInputs:ControlledInput[]; metrics:MetricDefinition[]; comparisons:ComparisonDefinition[]; completenessPolicy:CompletenessPolicy; baselineAssignments:Record<string,number>; resourceProfile:typeof GDSS_EXPERIMENT_LIMITS_V1 }
export interface ScenarioOverride { targetKind:OverrideTargetKind; targetIdentity:string; expectedPreviousValue:ExperimentValue; replacementValue:ExperimentValue; provenanceIdentity:string }
export interface MaterializedScenario { ordinal:number; scenarioType:ScenarioType; experimentDesignHash:string; factorAssignments:Record<string,ExperimentValue>; overrides:ScenarioOverride[]; controlledInputProofHash:string; manifest:SimulationInputManifest; simulationInputHash:string; scenarioDefinitionHash:string }
export interface ExperimentManifest { experimentDesignHash:string; completenessPolicy:CompletenessPolicy; scenarios:MaterializedScenario[]; metrics:MetricDefinition[]; comparisons:ComparisonDefinition[]; semanticVersions:Record<string,string> }
export interface TrajectoryEvidence { projectId:string; simulationAttemptId:string; simulationResultHash:string; trajectoryHash:string; mediaType:string; formatVersion:string; byteLength:number; pointCount:number; completeness:"COMPLETE"|"PARTIAL"; simulationInputHash:string; temporalStep:number; timeUnit:UnitIdentity; expectedStates:Record<string,{unit:UnitIdentity;dimension:DimensionDefinition}>; payload:Uint8Array }
export interface GovernedTrajectory { evidence:TrajectoryEvidence; trajectory:SimulationTrajectory; points:readonly SimulationPoint[] }
export type MetricResult={metricKey:string;scenarioOrdinal:number;status:"SUCCEEDED";value?:number;stepIndex?:number;thresholdStepIndex?:number;elapsedTime?:number;unit?:UnitIdentity;dimension?:DimensionDefinition;quantitySemantics?:QuantitySemantics;operationCount:number;trajectoryHash:string;simulationResultHash:string}|{metricKey:string;scenarioOrdinal:number;status:"NOT_REACHED"|"INELIGIBLE"|"FAILED";diagnosticCode:string;operationCount:number;trajectoryHash?:string;simulationResultHash?:string};
export type ComparisonResult={comparisonKey:string;status:"SUCCEEDED";value?:number;ordering?:"TARGET_LESS_THAN_REFERENCE"|"TARGET_EQUAL_TO_REFERENCE"|"TARGET_GREATER_THAN_REFERENCE";unit?:UnitIdentity;dimension?:DimensionDefinition;operationCount:number}|{comparisonKey:string;status:"INELIGIBLE"|"FAILED";diagnosticCode:string;operationCount:number};
export interface ScenarioOutcome { ordinal:number;scenarioDefinitionHash:string;dispatchClassification:ScenarioDispatchState;terminalClassification:"SUCCESS"|"FAILURE"|"ABSENT"|"ABORTED";simulationResultHash:string|null;trajectoryHash:string|null;failureClassification:string|null }
export interface ExperimentResult { manifestHash:string;status:ExperimentTerminalStatus;completeness:"COMPLETE"|"PARTIAL"|"ABORTED";scenarios:ScenarioOutcome[];metrics:MetricResult[];comparisons:ComparisonResult[];findings:Array<Record<string,unknown>>;diagnostics:Array<{code:string;stage:string;details:Record<string,unknown>}>;provenance:"SIMULATION_DERIVED";physicalAuthority:"NONE" }
