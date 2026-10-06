import { binary64Hex } from "@/lib/gdss/expression/canonical";
import type { AdequacyClassification,CalibrationDesign,CalibrationResult,CandidateOutcome,ParameterEstimateSet } from "./contracts";
import { calibrationResultHash,parameterEstimateSetHash } from "./canonical";
import { selectWinner } from "./candidate";
import { governedHash } from "@/lib/gdss/observation";
export function assessAdequacy(design:CalibrationDesign,objective:number):AdequacyClassification{const criteria=design.adequacyCriteria;if(!criteria)return"FIT_COMPUTED_NO_ADEQUACY_CLAIM";const passes=criteria.operator==="LTE"?objective<=criteria.threshold:criteria.operator==="LT"?objective<criteria.threshold:criteria.operator==="GTE"?objective>=criteria.threshold:objective>criteria.threshold;return passes?"ACCEPTABLE_UNDER_DECLARED_CRITERIA":"POOR_FIT_UNDER_DECLARED_CRITERIA";}
export function constructCalibrationResult(design:CalibrationDesign,designHash:string,alignmentHash:string,outcomes:readonly CandidateOutcome[]){
  const winner=selectWinner(outcomes);const estimates=design.parameters.map(parameter=>({parameterIdentity:parameter.parameterIdentity,baseValue:parameter.baseValue,estimatedValue:winner.candidate.values[parameter.parameterIdentity],unit:parameter.unit,lowerBound:parameter.lowerBound,upperBound:parameter.upperBound}));
  const base={selectedCandidateOrdinal:winner.candidate.ordinal,selectedParameterVectorHash:winner.candidate.parameterVectorHash,objectiveVersion:design.objectiveVersion,objective:winner.objective,objectiveBits:winner.objectiveBits??binary64Hex(winner.objective),modelBindingEvidence:{modelIdentityId:design.modelIdentityId,modelVersionId:design.modelVersionId,modelContentHash:design.modelContentHash,bindingId:design.bindingId,bindingVersionId:design.bindingVersionId,dynamicBindingHash:design.dynamicBindingHash},datasetAlignmentEvidence:{datasets:design.datasets,designHash,alignmentHash},simulationEvidence:{simulationAttemptId:winner.simulationAttemptId,simulationResultHash:winner.simulationResultHash,trajectoryHash:winner.trajectoryHash},estimates};
  const computationalEstimate={...base,simulationEvidence:{simulationResultHash:winner.simulationResultHash,trajectoryHash:winner.trajectoryHash}};
  const estimateSet:ParameterEstimateSet={...base,estimateSetHash:parameterEstimateSetHash(computationalEstimate)};
  const residualHash=governedHash("midd:gdss:calibration-residuals:v1",winner.residuals??[]);
  const resultBase:Omit<CalibrationResult,"resultHash">={status:"ESTIMATE_COMPUTED",designHash,alignmentHash,estimateSetHash:estimateSet.estimateSetHash,residualHash,adequacy:assessAdequacy(design,winner.objective),physicalAuthority:"NONE"};
  return{winner,estimateSet,result:{...resultBase,resultHash:calibrationResultHash(resultBase)}};
}
