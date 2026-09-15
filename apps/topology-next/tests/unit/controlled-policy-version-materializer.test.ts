import {describe,expect,it} from "vitest";
import {ConflictError} from "@/lib/errors/domain-errors";
import {buildControlledPolicyConfigurationHash,buildControlledPolicyVersionHash,materializeControlledPolicyVersionCandidate} from "@/lib/promotion/controlled-policy-version-materializer";

const input:any={project_id:"11111111-1111-4111-8111-111111111111",proposal_id:"p",proposal_hash:"a".repeat(64),proposal_status:"VALIDATED",assessment_id:"a",assessment_hash:"b".repeat(64),assessment_status:"PASSED",candidate_id:"c",candidate_hash:"c".repeat(64),candidate_strategy_type:"proportional",strategy_schema_version:1,candidate_parameters:{setpoint_value:50,gain:.3,deadband:0,min_action:0},recommendation_hash:"d".repeat(64),review_hash:"e".repeat(64),evaluation_hash:"f".repeat(64),ranking_hash:"1".repeat(64)};

describe("controlled policy version materializer",()=>{
  it("creates a canonical semantic configuration independently of provenance",()=>{
    const configuration=materializeControlledPolicyVersionCandidate(input);
    expect(configuration).toEqual({strategy_type:"proportional",strategy_schema_version:1,parameters:{deadband:0,gain:.3,min_action:0,setpoint_value:50}});
    expect(buildControlledPolicyConfigurationHash(configuration)).toBe(buildControlledPolicyConfigurationHash({...configuration,parameters:{setpoint_value:50,min_action:0,gain:.3,deadband:0}}));
  });
  it("requires a validated proposal and passed authoritative assessment",()=>{
    for(const proposal_status of ["VALIDATION_PENDING","VALIDATION_FAILED","BLOCKED"])expect(()=>materializeControlledPolicyVersionCandidate({...input,proposal_status})).toThrow(ConflictError);
    expect(()=>materializeControlledPolicyVersionCandidate({...input,assessment_status:"FAILED"})).toThrow("CONTROLLED_POLICY_VERSION_ASSESSMENT_NOT_PASSED");
  });
  it("separates provenance identity from semantic configuration identity",()=>{
    const configurationHash=buildControlledPolicyConfigurationHash(materializeControlledPolicyVersionCandidate(input));
    const first=buildControlledPolicyVersionHash({project_id:input.project_id,configuration_hash:configurationHash,proposal_hash:input.proposal_hash,assessment_hash:input.assessment_hash,candidate_hash:input.candidate_hash,strategy_type:"proportional",version_number:1});
    const second=buildControlledPolicyVersionHash({project_id:input.project_id,configuration_hash:configurationHash,proposal_hash:input.proposal_hash,assessment_hash:"9".repeat(64),candidate_hash:input.candidate_hash,strategy_type:"proportional",version_number:1});
    expect(first).not.toBe(second);
  });
});
