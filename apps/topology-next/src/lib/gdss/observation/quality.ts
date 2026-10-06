import type { ObservationPoint } from "./contracts";
import { observationFail } from "./diagnostics";
export function validatePointQuality(point:ObservationPoint){
  if(point.value!==null&&!Number.isFinite(point.value)) observationFail("INVALID_DATASET","Observation value must be finite");
  if(point.quality==="ACCEPTED"&&point.value===null) observationFail("INVALID_DATASET","Accepted point requires a value");
  if(point.quality==="MISSING"&&point.value!==null) observationFail("INVALID_DATASET","Missing point forbids a value");
  if(point.resolution!==undefined&&(!Number.isFinite(point.resolution)||point.resolution<=0)) observationFail("INVALID_DATASET","Resolution must be finite and positive");
  return point;
}
