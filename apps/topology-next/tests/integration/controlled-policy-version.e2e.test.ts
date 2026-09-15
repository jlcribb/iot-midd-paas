import {describe,expect,it} from "vitest";
import {randomUUID} from "node:crypto";
import {pool} from "@/lib/db/pool";
import {experimentFingerprint,sha256Canonical} from "@/lib/simulation/canonical";
import {EvaluationProfileRepository} from "@/lib/repositories/evaluation-profile.repository";
import {StrategySearchSpaceService} from "@/lib/services/strategy-search-space.service";
import {ExperimentBatchService} from "@/lib/services/experiment-batch.service";
import {ExperimentRankingService} from "@/lib/services/experiment-ranking.service";
import {StrategyRecommendationService} from "@/lib/services/strategy-recommendation.service";
import {RecommendationReviewService} from "@/lib/services/recommendation-review.service";
import {PolicyPromotionService} from "@/lib/services/policy-promotion.service";
import {ControlledPolicyVersionService} from "@/lib/services/controlled-policy-version.service";
import {buildControlledPolicyConfigurationHash} from "@/lib/promotion/controlled-policy-version-materializer";

const enabled=process.env.M72_E2E_RUNNER==="1";

async function cleanup(projectId:string){
  await pool.query("DELETE FROM public.control_controlled_policy_version_candidates WHERE project_id=$1::uuid",[projectId]);
  await pool.query("DELETE FROM public.control_policy_promotion_gate_results WHERE assessment_id IN (SELECT a.id FROM public.control_policy_promotion_assessments a JOIN public.control_policy_promotion_proposals p ON p.id=a.proposal_id WHERE p.project_id=$1::uuid)",[projectId]);
  await pool.query("DELETE FROM public.control_policy_promotion_assessments WHERE proposal_id IN (SELECT id FROM public.control_policy_promotion_proposals WHERE project_id=$1::uuid)",[projectId]);
  await pool.query("DELETE FROM public.control_policy_promotion_proposals WHERE project_id=$1::uuid",[projectId]);
  await pool.query("DELETE FROM public.control_strategy_recommendation_candidates WHERE recommendation_id IN (SELECT id FROM public.control_strategy_recommendations WHERE project_id=$1::uuid)",[projectId]);
  await pool.query("DELETE FROM public.control_strategy_recommendation_reviews WHERE project_id=$1::uuid",[projectId]);
  await pool.query("DELETE FROM public.control_strategy_recommendations WHERE project_id=$1::uuid",[projectId]);
  await pool.query("DELETE FROM public.control_experiment_ranking_items WHERE ranking_id IN (SELECT id FROM public.control_experiment_rankings WHERE project_id=$1::uuid)",[projectId]);
  await pool.query("DELETE FROM public.control_experiment_rankings WHERE project_id=$1::uuid",[projectId]);
  await pool.query("DELETE FROM public.control_experiment_batch_items WHERE project_id=$1::uuid",[projectId]);
  await pool.query("DELETE FROM public.control_experiment_evaluation_metrics WHERE evaluation_id IN (SELECT id FROM public.control_experiment_evaluations WHERE project_id=$1::uuid)",[projectId]);
  await pool.query("DELETE FROM public.control_experiment_evaluations WHERE project_id=$1::uuid",[projectId]);
  await pool.query("DELETE FROM public.control_simulation_trace_points WHERE trace_id IN (SELECT id FROM public.control_simulation_traces WHERE project_id=$1::uuid)",[projectId]);
  await pool.query("DELETE FROM public.control_simulation_traces WHERE project_id=$1::uuid",[projectId]);
  await pool.query("DELETE FROM public.control_simulation_results WHERE project_id=$1::uuid",[projectId]);
  await pool.query("DELETE FROM public.control_simulation_run_events WHERE run_id IN (SELECT id FROM public.control_simulation_runs WHERE project_id=$1::uuid)",[projectId]);
  await pool.query("DELETE FROM public.control_simulation_runs WHERE project_id=$1::uuid",[projectId]);
  await pool.query("DELETE FROM public.control_experiment_batches WHERE project_id=$1::uuid",[projectId]);
  await pool.query("DELETE FROM public.control_strategy_candidates WHERE project_id=$1::uuid",[projectId]);
  await pool.query("DELETE FROM public.control_strategy_search_spaces WHERE project_id=$1::uuid",[projectId]);
  await pool.query("DELETE FROM public.control_evaluation_profile_metrics WHERE profile_id IN (SELECT id FROM public.control_evaluation_profiles WHERE project_id=$1::uuid)",[projectId]);
  await pool.query("DELETE FROM public.control_evaluation_profiles WHERE project_id=$1::uuid",[projectId]);
  await pool.query("DELETE FROM public.control_simulation_sessions WHERE project_id=$1::uuid",[projectId]);
  await pool.query("DELETE FROM iot_schema.auditoria WHERE contexto->>'project_id'=$1",[projectId]);
  await pool.query("DELETE FROM public.projects WHERE id=$1::uuid",[projectId]);
}

describe.runIf(enabled)("M7.2A controlled policy version candidate E2E",()=>{it("reaches M6 through M7.2 without operational side effects",async()=>{
  const projectId=randomUUID(),actorId=`m72-e2e-${randomUUID()}`,actor={actor_id:actorId,user_id:actorId,display_name:"M7.2A E2E",role:"admin" as const,all_projects:true,project_ids:[],project_roles:{[projectId]:"admin" as const},auth_source:"oauth_session" as const};
  try {
    await pool.query("INSERT INTO public.projects(id,name,status,parametric_control_enabled,metadata) VALUES($1::uuid,$2,'active',FALSE,'{}'::jsonb)",[projectId,`M72 E2E ${projectId}`]);
    const policy={schema_version:1,policy:{id:randomUUID(),project_id:projectId,variable:"level",policy_type:"proportional",enabled:true,version:1,priority:1,context_selector:{},source_asset_id:randomUUID(),params:{gain:1,setpoint_value:50,deadband:0,min_action:0}}};
    const topology={schema_version:1,source_asset:{id:policy.policy.source_asset_id,status:"active"},actuation_binding:null,target_asset:null};
    const dataset={schema_version:1,source_kind:"synthetic",ordering:"timestamp_ascending_event_id",records:[1,2,3].map((value,index)=>({event_id:randomUUID(),project_id:projectId,variable:"level",value:45+value,timestamp:`2026-01-01T00:00:0${index}Z`,context:{},metadata:{},quality:"raw",source:"m72-e2e",event_kind:"telemetry.observed"}))};
    const configuration={schema_version:1,execution_context:"SIMULATION",engine:{name:"parametric-control-engine",version:"0.1.0"},clock:{model_type:"SIMULATION_CLOCK",model_version:"1",initial_virtual_time:"2026-01-01T00:00:00Z"},evaluation_options:{include_trace:true},random_seed:null,operational_side_effects:{outbox:false,transport:false,physical_effects:false}};
    const baseSessionId=randomUUID(),policyHash=sha256Canonical(policy),topologyHash=sha256Canonical(topology),datasetHash=sha256Canonical(dataset),configurationHash=sha256Canonical(configuration),fingerprint=experimentFingerprint({policy_snapshot_hash:policyHash,topology_snapshot_hash:topologyHash,dataset_snapshot_hash:datasetHash,configuration_snapshot_hash:configurationHash});
    await pool.query("INSERT INTO public.control_simulation_sessions(id,project_id,execution_context,status,created_by,snapshot_refs,metadata,policy_snapshot,topology_snapshot,dataset_snapshot,configuration_snapshot,policy_snapshot_hash,topology_snapshot_hash,dataset_snapshot_hash,configuration_snapshot_hash,experiment_fingerprint,snapshot_schema_version,prepared_at) VALUES($1::uuid,$2::uuid,'SIMULATION','READY',$3,'{}','{}',$4::jsonb,$5::jsonb,$6::jsonb,$7::jsonb,$8,$9,$10,$11,$12,1,NOW())",[baseSessionId,projectId,actorId,JSON.stringify(policy),JSON.stringify(topology),JSON.stringify(dataset),JSON.stringify(configuration),policyHash,topologyHash,datasetHash,configurationHash,fingerprint]);
    const profiles=new EvaluationProfileRepository(),metrics=await profiles.listMetrics(),profile=await profiles.create(projectId,actorId,{code:`m72${randomUUID().replaceAll("-","").slice(0,16)}`,name:"M72 E2E",metrics:metrics.filter(metric=>["tracking_error","overshoot","undershoot","settling_time","control_effort","actuation_count"].includes(metric.code)).map(metric=>({metric_id:metric.id,weight:1/6,required:true}))});
    const spaces=new StrategySearchSpaceService(),batches=new ExperimentBatchService(),rankings=new ExperimentRankingService(),recommendations=new StrategyRecommendationService(),reviews=new RecommendationReviewService(),promotions=new PolicyPromotionService(),versions=new ControlledPolicyVersionService();
    const promote=async(gain:number)=>{const space=await spaces.create(actor,projectId,{name:`M72 ${gain}`,strategy_type:"proportional",generation_method:"GRID",parameters:{gain:{values:[gain]},setpoint_value:{values:[50]}}});const batch=await batches.create(actor,projectId,{search_space_id:space.id,simulation_session_id:baseSessionId,evaluation_profile_id:profile.id,name:`M72 batch ${gain}`});const completed=await batches.start(actor,projectId,batch.id);expect(completed.status).toBe("COMPLETED");const items=await batches.items(actor,projectId,batch.id);expect(items).toHaveLength(1);expect(items[0]).toMatchObject({status:"COMPLETED"});const ranking=await rankings.create(actor,projectId,batch.id),recommendation=await recommendations.create(actor,projectId,ranking.id),review=await reviews.create(actor,projectId,recommendation.id,{decision:"APPROVE_FOR_FURTHER_TESTING",rationale:"M7.2A real simulation evidence."}),proposal=await promotions.create(actor,projectId,recommendation.id,review.id),assessment=await promotions.assess(actor,projectId,proposal.id);expect(proposal.status).toBe("CREATED");expect(assessment).toMatchObject({status:"PASSED",blocking_pass_count:8,blocking_fail_count:0});expect(assessment.gate_results.every(gate=>gate.status==="PASS")).toBe(true);return {proposal:await promotions.get(actor,projectId,proposal.id),assessment,items};};
    const first=await promote(.1),firstVersion=await versions.create(actor,projectId,first.proposal.id),firstReplay=await versions.create(actor,projectId,first.proposal.id);
    expect(firstVersion).toMatchObject({status:"CANDIDATE",strategy_type:"proportional",version_number:1,source_candidate_id:first.items[0].candidate_id,candidate_hash:first.items[0].candidate_hash,proposal_hash:first.proposal.proposal_hash,assessment_hash:first.assessment.assessment_hash,physical_effects_allowed:false});
    expect(firstReplay).toMatchObject({id:firstVersion.id,version_number:1,configuration_hash:firstVersion.configuration_hash,policy_version_hash:firstVersion.policy_version_hash});
    expect(buildControlledPolicyConfigurationHash({strategy_type:firstVersion.strategy_type,strategy_schema_version:firstVersion.strategy_schema_version,parameters:{setpoint_value:50,gain:.1}})).toBe(firstVersion.configuration_hash);
    expect(Object.keys(firstVersion.configuration_snapshot).sort()).toEqual(["parameters","strategy_schema_version","strategy_type"]);
    expect((await pool.query("SELECT count(*)::int count FROM iot_schema.auditoria WHERE entidad_id=$1::uuid AND accion='CONTROLLED_POLICY_VERSION_CANDIDATE_CREATED'",[firstVersion.id])).rows[0].count).toBe(1);
    await expect(pool.query("UPDATE public.control_controlled_policy_version_candidates SET configuration_hash='0' WHERE id=$1::uuid",[firstVersion.id])).rejects.toThrow(/immutable/);
    const second=await promote(.2),secondVersion=await versions.create(actor,projectId,second.proposal.id);expect(secondVersion.version_number).toBe(2);
    const third=await promote(.3),fourth=await promote(.4),concurrent=await Promise.all([versions.create(actor,projectId,third.proposal.id),versions.create(actor,projectId,fourth.proposal.id)]);expect(concurrent.map(item=>item.version_number).sort((a,b)=>a-b)).toEqual([3,4]);
    const active=await pool.query("SELECT COALESCE(jsonb_agg(to_jsonb(p)-'updated_at' ORDER BY p.id),'[]'::jsonb) snapshot FROM public.project_control_policies p WHERE p.project_id=$1::uuid",[projectId]);expect(active.rows[0].snapshot).toEqual([]);
    if(process.env.M72_E2E_REPORT==="1")console.info(JSON.stringify({status:"M72_CONTROLLED_POLICY_VERSION_CANDIDATE_E2E_PASS",candidates:[firstVersion,secondVersion,...concurrent].map(item=>({id:item.id,strategy:item.strategy_type,version:item.version_number,candidate_hash:item.candidate_hash,configuration_hash:item.configuration_hash,policy_version_hash:item.policy_version_hash,status:item.status})),active_policies_changed:false,runtime_changed:false,deployment:false,physical_effects:false}));
  } finally { await cleanup(projectId); }
},30000);});
