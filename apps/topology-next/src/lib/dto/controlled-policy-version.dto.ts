export const CONTROLLED_POLICY_VERSION_SCHEMA="controlled-policy-version:v1";
export const CONTROLLED_POLICY_MATERIALIZER_VERSION="controlled-policy-materializer:v1";

export type ControlledPolicyVersionStatus="CANDIDATE";

export interface ControlledPolicyConfiguration {
  strategy_type:"proportional"|"threshold";
  strategy_schema_version:number;
  parameters:Record<string,unknown>;
}

export interface ControlledPolicyVersionCandidate {
  id:string;
  project_id:string;
  promotion_proposal_id:string;
  proposal_hash:string;
  promotion_assessment_id:string;
  assessment_hash:string;
  source_candidate_id:string;
  candidate_hash:string;
  strategy_type:"proportional"|"threshold";
  strategy_schema_version:number;
  version_number:number;
  version_label:string;
  configuration_snapshot:ControlledPolicyConfiguration;
  configuration_hash:string;
  policy_version_hash:string;
  provenance_snapshot:Record<string,string>;
  status:ControlledPolicyVersionStatus;
  policy_version_schema:string;
  materializer_version:string;
  created_by:string;
  created_at:string;
  physical_effects_allowed:false;
}
