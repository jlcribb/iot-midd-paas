import { binary64Hex } from "@/lib/gdss/expression/canonical";
import type { CalibrationParameter,Candidate } from "./contracts";
import { parameterVectorHash } from "./canonical";
import { calibrationFail } from "./diagnostics";
import { GDSS_CALIBRATION_LIMITS_V1 } from "./limits";
function values(parameter:CalibrationParameter){
  const input=parameter.mode==="FIXED"?[parameter.fixedValue]:parameter.candidateValues;
  if(!input?.length||input.length>GDSS_CALIBRATION_LIMITS_V1.gridValuesPerParameter) calibrationFail("INVALID_GRID","Grid must be explicit, non-empty and bounded");
  const normalized=input.map(value=>Object.is(value,-0)?0:value as number);
  if(normalized.some(value=>!Number.isFinite(value)||value<parameter.lowerBound||value>parameter.upperBound)) calibrationFail("INVALID_GRID","Grid value is non-finite or outside bounds");
  if(new Set(normalized.map(binary64Hex)).size!==normalized.length) calibrationFail("INVALID_GRID","Grid contains semantic duplicates");
  return normalized.sort((a,b)=>a-b);
}
export function materializeCandidateUniverse(parameters:readonly CalibrationParameter[]):Candidate[]{
  const ordered=[...parameters].sort((a,b)=>Buffer.from(a.parameterIdentity).compare(Buffer.from(b.parameterIdentity)));
  const domains=ordered.map(parameter=>({parameter,values:values(parameter)}));
  const count=domains.reduce((total,domain)=>total*domain.values.length,1);
  if(count>GDSS_CALIBRATION_LIMITS_V1.candidates) calibrationFail("CANDIDATE_LIMIT_EXCEEDED","Candidate universe exceeds limit");
  const candidates:Candidate[]=[];
  const visit=(index:number,current:Record<string,number>)=>{if(index===domains.length){const immutable={...current};candidates.push({ordinal:candidates.length,values:immutable,parameterVectorHash:parameterVectorHash(immutable)});return;}const domain=domains[index];for(const value of domain.values){current[domain.parameter.parameterIdentity]=value;visit(index+1,current);}delete current[domain.parameter.parameterIdentity];};
  visit(0,{}); return candidates;
}
