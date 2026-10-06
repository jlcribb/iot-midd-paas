import { governedHash } from "@/lib/gdss/observation";
import type { CalibrationDesign,CalibrationResult,ParameterEstimateSet } from "./contracts";
export const calibrationDesignHash=(design:CalibrationDesign)=>governedHash("midd:gdss:calibration-design:v1",{
  modelIdentityId:design.modelIdentityId,modelVersionId:design.modelVersionId,modelVersionNumber:design.modelVersionNumber,modelContentHash:design.modelContentHash,
  bindingId:design.bindingId,bindingVersionId:design.bindingVersionId,bindingVersionNumber:design.bindingVersionNumber,dynamicBindingHash:design.dynamicBindingHash,
  datasets:[...design.datasets].sort((a,b)=>a.ordinal-b.ordinal),alignmentSpecification:design.alignmentSpecification,
  parameters:[...design.parameters].sort((a,b)=>a.parameterIdentity.localeCompare(b.parameterIdentity)),objectiveVersion:design.objectiveVersion,adequacyCriteria:design.adequacyCriteria,
});
export const alignmentHash=(designHash:string,datasetHashes:readonly string[],gridHash:string,result:unknown)=>governedHash("midd:gdss:observation-alignment:v1",{designHash,datasetHashes:[...datasetHashes],gridHash,result});
export const parameterVectorHash=(values:Readonly<Record<string,number>>)=>governedHash("midd:gdss:calibration-parameter-vector:v1",values);
export const parameterEstimateSetHash=(value:Omit<ParameterEstimateSet,"estimateSetHash">&Record<string,unknown>)=>governedHash("midd:gdss:parameter-estimate-set:v1",value);
export const calibrationResultHash=(value:Omit<CalibrationResult,"resultHash">)=>governedHash("midd:gdss:calibration-result:v1",value);
