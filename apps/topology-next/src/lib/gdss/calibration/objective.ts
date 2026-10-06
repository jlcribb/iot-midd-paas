import { binary64Hex } from "@/lib/gdss/expression/canonical";
import type { ObjectiveSeries,ObjectiveVersion } from "./contracts";
import { calibrationFail } from "./diagnostics";
import { GDSS_CALIBRATION_LIMITS_V1 } from "./limits";
const finite=(value:number)=>{const normalized=Object.is(value,-0)?0:value;if(!Number.isFinite(normalized))calibrationFail("NONFINITE_OBJECTIVE","Non-finite objective arithmetic");return normalized;};
export interface ObjectiveResult{value:number;bits:string;operations:number;contributions:number[][];}
export function evaluateObjective(version:ObjectiveVersion,series:readonly ObjectiveSeries[]):ObjectiveResult{
  if(!series.length)calibrationFail("INSUFFICIENT_OBSERVATIONS","Objective has no included series");
  let operations=0;
  if(series.some(item=>item.observed.length!==item.simulated.length||!item.observed.length))calibrationFail("INSUFFICIENT_OBSERVATIONS","Objective series cardinality mismatch");
  const pairs:number[][]=[];
  let value:number;
  if(version==="RMSE_V1"){
    if(series.length!==1)calibrationFail("DIMENSION_MISMATCH","RMSE requires exactly one series");
    let sum=0;const contributions=series[0].observed.map((observed,index)=>{const residual=finite(observed-series[0].simulated[index]);operations++;const contribution=finite(residual*residual);operations++;sum=finite(sum+contribution);operations++;return contribution;});pairs.push(contributions);value=finite(Math.sqrt(finite(sum/contributions.length)));operations+=2;
  }else{
    let numerator=0,totalWeight=0;
    for(let i=0;i<series.length;i++){const scale=series[i].normalizationScale,weight=series[i].weight;if(scale===undefined||weight===undefined||!Number.isFinite(scale)||scale<=0||!Number.isFinite(weight)||weight<=0)calibrationFail("NONFINITE_OBJECTIVE","Scale and weight must be finite and positive");let sum=0;const normalized=series[i].observed.map((observed,index)=>{const residual=finite(observed-series[i].simulated[index]);operations++;const z=finite(residual/scale);operations++;const q=finite(z*z);operations++;sum=finite(sum+q);operations++;return q;});pairs.push(normalized);const mean=finite(sum/normalized.length);const weighted=finite(weight*mean);operations+=2;numerator=finite(numerator+weighted);totalWeight=finite(totalWeight+weight);operations+=2;}value=finite(numerator/totalWeight);operations++;
  }
  if(operations>GDSS_CALIBRATION_LIMITS_V1.objectiveOperations)calibrationFail("RESOURCE_LIMIT_EXCEEDED","Objective operation limit exceeded");
  return{value,bits:binary64Hex(value),operations,contributions:pairs};
}
