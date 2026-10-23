import type {RecommendationCandidateInput} from "./recommendation-contracts";
import {DecisionError} from "./diagnostics";

export type RecommendationEligibilityFacts={capabilityStates:string[];claimStatuses:string[];claimExpired:boolean;comparisonComplete:boolean;sensitivityConclusion:string;sensitivityStatus:string;robustnessStatuses:string[];riskConclusions:string[];hardConstraintStates:string[];hasMandatoryReview:boolean;hasBlockingReview:boolean;hasAdverseEvidence:boolean;inputsCurrent:boolean};
export function assessRecommendationEligibility(f:RecommendationEligibilityFacts){
  if(!f.inputsCurrent||f.claimStatuses.some(x=>x!=="AUTHORIZED")||f.claimExpired)throw new DecisionError("CLAIM_NOT_CURRENT");
  if(f.capabilityStates.some(x=>x!=="EVIDENCE_OF_CAPABILITY"))throw new DecisionError("RECOMMENDATION_EVIDENCE_INSUFFICIENT");
  if(!f.comparisonComplete||f.sensitivityStatus!=="COMPLETE"||f.robustnessStatuses.some(x=>x!=="ACTIVE"))throw new DecisionError("RECOMMENDATION_EVIDENCE_INCOMPLETE");
  if(f.hardConstraintStates.some(x=>x!=="SATISFIED"))throw new DecisionError("HARD_CONSTRAINT_VIOLATED");
  if(f.riskConclusions.some(x=>x==="UNACCEPTABLE"))throw new DecisionError("RISK_UNACCEPTABLE");
  if(f.riskConclusions.some(x=>x==="REVIEW_REQUIRED")||["INCOMPLETE","UNKNOWN"].includes(f.sensitivityConclusion))throw new DecisionError("RECOMMENDATION_REVIEW_REQUIRED");
  if(!f.hasMandatoryReview||f.hasBlockingReview||!f.hasAdverseEvidence)throw new DecisionError("RECOMMENDATION_EVIDENCE_INCOMPLETE");
  return "ELIGIBLE_FOR_HUMAN_AUTHORIZATION" as const;
}
export function requiredRecommendationLimitations(input:RecommendationCandidateInput){const required:string[]=[];if(["LIMITED","INSUFFICIENT"].includes(input.qualityDimensions.evidenceAdequacy))required.push("EVIDENCE");if(["PARTIAL","UNKNOWN","UNACCEPTABLE"].includes(input.qualityDimensions.uncertaintyAcceptability))required.push("UNCERTAINTY");if(input.qualityDimensions.robustness!=="ROBUST")required.push("ROBUSTNESS");if(input.qualityDimensions.riskAcceptability!=="ACCEPTABLE")required.push("RISK");return required;}
export function isScopeSubset(requested:{target:string;horizon:string;domain:string[];modelVersionId:string;alternativeIds:string[]},basis:typeof requested){return requested.target===basis.target&&requested.horizon===basis.horizon&&requested.modelVersionId===basis.modelVersionId&&requested.domain.every(x=>basis.domain.includes(x))&&requested.alternativeIds.every(x=>basis.alternativeIds.includes(x));}
export function projectRecommendationCurrentness(f:{status:string;validThroughEpochMicros:number|null;nowEpochMicros:number;hasUnresolvedTrigger:boolean;inputsCurrent?:boolean;invalidated:boolean}){if(f.invalidated)return "INVALIDATED";if(f.status==="REVOKED")return "REVOKED";if(f.status==="SUPERSEDED")return "SUPERSEDED";if(f.inputsCurrent===false||f.hasUnresolvedTrigger)return "STALE_REVIEW_REQUIRED";if(f.status==="AUTHORIZED"&&f.validThroughEpochMicros!==null&&f.validThroughEpochMicros<f.nowEpochMicros)return "AUTHORIZED_EXPIRED_REVIEW_REQUIRED";return f.status==="AUTHORIZED"?"AUTHORIZED_CURRENT":f.status;}
