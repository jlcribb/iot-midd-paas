import {canonicalClone,sha256Canonical} from "@/lib/simulation/canonical";
import {ConflictError} from "@/lib/errors/domain-errors";
import {CONTROLLED_POLICY_MATERIALIZER_VERSION,CONTROLLED_POLICY_VERSION_SCHEMA,type ControlledPolicyConfiguration} from "@/lib/dto/controlled-policy-version.dto";

export interface ControlledPolicyVersionMaterializationInput {
  project_id:string;
  proposal_id:string;
  proposal_hash:string;
  proposal_status:string;
  assessment_id:string|null;
  assessment_hash:string|null;
  assessment_status:string|null;
  candidate_id:string;
  candidate_hash:string;
  candidate_strategy_type:"proportional"|"threshold";
  strategy_schema_version:number;
  candidate_parameters:Record<string,unknown>;
  recommendation_hash:string;
  review_hash:string;
  evaluation_hash:string;
  ranking_hash:string;
}

export function assertControlledPolicyVersionEligibility(input:ControlledPolicyVersionMaterializationInput){
  if(input.proposal_status!=="VALIDATED")throw new ConflictError("CONTROLLED_POLICY_VERSION_PROPOSAL_NOT_VALIDATED");
  if(input.assessment_status!=="PASSED"||!input.assessment_id||!input.assessment_hash)throw new ConflictError("CONTROLLED_POLICY_VERSION_ASSESSMENT_NOT_PASSED");
  if(!input.candidate_id||!input.candidate_hash)throw new ConflictError("CONTROLLED_POLICY_VERSION_CANDIDATE_PROVENANCE_MISSING");
}

/** Materializes only semantic control configuration; simulation artifacts stay in provenance. */
export function materializeControlledPolicyVersionCandidate(input:ControlledPolicyVersionMaterializationInput):ControlledPolicyConfiguration{
  assertControlledPolicyVersionEligibility(input);
  return canonicalClone({strategy_type:input.candidate_strategy_type,strategy_schema_version:input.strategy_schema_version,parameters:input.candidate_parameters});
}

export function buildControlledPolicyConfigurationHash(configuration:ControlledPolicyConfiguration){return sha256Canonical(configuration);}

export function buildControlledPolicyVersionHash(input:{project_id:string;configuration_hash:string;proposal_hash:string;assessment_hash:string;candidate_hash:string;strategy_type:string;version_number:number;materializer_version?:string;policy_version_schema?:string}){
  return sha256Canonical({project_id:input.project_id,configuration_hash:input.configuration_hash,proposal_hash:input.proposal_hash,assessment_hash:input.assessment_hash,candidate_hash:input.candidate_hash,strategy_type:input.strategy_type,version_number:input.version_number,materializer_version:input.materializer_version??CONTROLLED_POLICY_MATERIALIZER_VERSION,policy_version_schema:input.policy_version_schema??CONTROLLED_POLICY_VERSION_SCHEMA});
}

export function buildControlledPolicyVersionProvenance(input:ControlledPolicyVersionMaterializationInput){
  return canonicalClone({proposal_hash:input.proposal_hash,assessment_hash:input.assessment_hash!,candidate_hash:input.candidate_hash,recommendation_hash:input.recommendation_hash,review_hash:input.review_hash,evaluation_hash:input.evaluation_hash,ranking_hash:input.ranking_hash});
}
