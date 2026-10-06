import type { DynamicBindingSnapshot } from "@/lib/gdss/simulation";
import type { ModelContent } from "@/lib/gdss/core";
import type { CalibrationDesign } from "./contracts";
import { calibrationFail } from "./diagnostics";
import { GDSS_CALIBRATION_LIMITS_V1 } from "./limits";
const sha=/^[0-9a-f]{64}$/;
export function validateCalibrationDesign(design:CalibrationDesign,model:ModelContent,binding:DynamicBindingSnapshot){
  if(design.lifecycleStatus==="DEPRECATED") calibrationFail("MODEL_BINDING_MISMATCH","Deprecated design is not executable");
  if(binding.lifecycleStatus!=="PUBLISHED"||binding.modelVersionId!==design.modelVersionId||binding.bindingId!==design.bindingId||binding.bindingVersionId!==design.bindingVersionId||binding.bindingVersion!==design.bindingVersionNumber||binding.modelContentHash!==design.modelContentHash||binding.dynamicBindingHash!==design.dynamicBindingHash||!sha.test(design.modelContentHash)||!sha.test(design.dynamicBindingHash)) calibrationFail("MODEL_BINDING_MISMATCH","Exact model/binding projection does not reconcile");
  const modelParameters=new Map(model.children.filter(child=>child.kind==="Parameter").map(child=>[child.symbol,child]));
  const bindingParameters=new Set(binding.parameters.map(parameter=>parameter.parameterRef));
  const calibrated=design.parameters.filter(parameter=>parameter.mode==="CALIBRATED");
  if(calibrated.length>GDSS_CALIBRATION_LIMITS_V1.calibratedParameters||design.parameters.length-calibrated.length>GDSS_CALIBRATION_LIMITS_V1.fixedParameters) calibrationFail("RESOURCE_LIMIT_EXCEEDED","Parameter limit exceeded");
  for(const parameter of design.parameters){
    if(!modelParameters.has(parameter.parameterIdentity)||!bindingParameters.has(parameter.parameterIdentity)) calibrationFail("MODEL_BINDING_MISMATCH","Parameter is outside exact model/binding context");
    if(!Number.isFinite(parameter.baseValue)||parameter.lowerBound>parameter.upperBound||parameter.baseValue<parameter.lowerBound||parameter.baseValue>parameter.upperBound) calibrationFail("INVALID_GRID","Invalid parameter base/bounds");
  }
  if(design.datasets.some(value=>value.role==="EXPLORATORY")) calibrationFail("INVALID_DATASET","Exploratory data is not executable");
  return design;
}
