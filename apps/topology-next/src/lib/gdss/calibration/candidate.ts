import type { CandidateOutcome } from "./contracts";
import { calibrationFail } from "./diagnostics";
export function selectWinner(outcomes:readonly CandidateOutcome[]){
  const successful=outcomes.filter((outcome):outcome is CandidateOutcome&{objective:number;objectiveBits:string}=>outcome.state==="SUCCEEDED"&&outcome.objective!==undefined&&outcome.objectiveBits!==undefined);
  if(!successful.length)calibrationFail("NO_FEASIBLE_PARAMETER_SET","No successful candidate");
  return [...successful].sort((left,right)=>left.objective-right.objective||left.candidate.ordinal-right.candidate.ordinal)[0];
}
