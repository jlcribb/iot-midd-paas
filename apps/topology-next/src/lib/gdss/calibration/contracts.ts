import type { DimensionDefinition } from "@/lib/gdss/core";
import type { QuantitySemantics, UnitIdentity } from "@/lib/gdss/expression";
import type { AlignmentResult,AlignmentSpecification } from "@/lib/gdss/observation";
export type CalibrationLifecycle="DRAFT"|"VALIDATED"|"PUBLISHED"|"DEPRECATED";
export type ParameterMode="CALIBRATED"|"FIXED";
export type ObjectiveVersion="RMSE_V1"|"WEIGHTED_NORMALIZED_MSE_V1";
export type CandidateState="PENDING"|"CLAIMED"|"DISPATCHED"|"SUCCEEDED"|"INFEASIBLE"|"SIMULATION_FAILED"|"NOT_DISPATCHED_ABORTED";
export type AttemptState="ACCEPTED"|"RUNNING"|"COMPLETED"|"COMPLETED_WITH_WARNINGS"|"FAILED"|"ABORTED";
export type AdequacyClassification="FIT_COMPUTED_NO_ADEQUACY_CLAIM"|"ACCEPTABLE_UNDER_DECLARED_CRITERIA"|"POOR_FIT_UNDER_DECLARED_CRITERIA"|"INSUFFICIENT_EVIDENCE"|"INCOMPARABLE";
export interface CalibrationParameter { parameterIdentity:string;mode:ParameterMode;baseValue:number;unit:UnitIdentity;dimension:DimensionDefinition;lowerBound:number;upperBound:number;candidateValues?:number[];fixedValue?:number; }
export interface DatasetAssignment { datasetVersionId:string;datasetHash:string;role:"CALIBRATION"|"VALIDATION"|"HOLDOUT"|"EXPLORATORY";ordinal:number; }
export interface CalibrationDesign {
  projectId:string;calibrationIdentityId:string;calibrationVersionId:string;versionNumber:number;lifecycleStatus:CalibrationLifecycle;
  modelIdentityId:string;modelVersionId:string;modelVersionNumber:number;modelContentHash:string;
  bindingId:string;bindingVersionId:string;bindingVersionNumber:number;dynamicBindingHash:string;
  datasets:DatasetAssignment[];alignmentSpecification:AlignmentSpecification;parameters:CalibrationParameter[];
  objectiveVersion:ObjectiveVersion;adequacyCriteria?:{metric:string;operator:"LTE"|"LT"|"GTE"|"GT";threshold:number};
}
export interface Candidate { ordinal:number;values:Readonly<Record<string,number>>;parameterVectorHash:string; }
export interface CalibrationManifest {calibrationDesignHash:string;datasetHashes:string[];alignmentResult:AlignmentResult;alignmentHash:string;candidates:Candidate[];}
export interface Residual {mappingKey:string;pointOrdinal:number;coordinate:number;observed:number;simulated:number;residual:number;contribution:number;trajectoryHash:string;}
export interface CandidateOutcome {candidate:Candidate;state:"SUCCEEDED"|"INFEASIBLE"|"SIMULATION_FAILED";objective?:number;objectiveBits?:string;objectiveOperations?:number;simulationAttemptId?:string;simulationResultHash?:string;trajectoryHash?:string;residuals?:Residual[];}
export interface ParameterEstimate {parameterIdentity:string;baseValue:number;estimatedValue:number;unit:UnitIdentity;lowerBound:number;upperBound:number;}
export interface ParameterEstimateSet {selectedCandidateOrdinal:number;selectedParameterVectorHash:string;objectiveVersion:ObjectiveVersion;objective:number;objectiveBits:string;modelBindingEvidence:Record<string,unknown>;datasetAlignmentEvidence:Record<string,unknown>;simulationEvidence:Record<string,unknown>;estimates:ParameterEstimate[];estimateSetHash:string;}
export interface CalibrationResult {status:"ESTIMATE_COMPUTED";designHash:string;alignmentHash:string;estimateSetHash:string;residualHash:string;adequacy:AdequacyClassification;resultHash:string;physicalAuthority:"NONE";}
export interface ObjectiveSeries {mappingKey:string;observed:number[];simulated:number[];dimension:DimensionDefinition;unit:UnitIdentity;quantitySemantics:QuantitySemantics;normalizationScale?:number;weight?:number;}
