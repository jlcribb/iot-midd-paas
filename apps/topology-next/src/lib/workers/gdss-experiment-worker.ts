import { simulationInputHash } from "@/lib/gdss/simulation";
import { GDSS_EXPERIMENT_LIMITS_V1 } from "@/lib/gdss/experiment";
import { GdssExperimentRepository,type ScenarioClaim } from "@/lib/repositories/gdss-experiment.repository";

export interface GdssScenarioDispatchResult {simulationAttemptId:string;simulationResultHash:string;trajectoryHash:string|null;success:boolean;failureClassification?:string}
export type GdssScenarioDispatcher=(claim:ScenarioClaim,idempotencyKey:string)=>Promise<GdssScenarioDispatchResult>;

export class GdssExperimentWorker {
  constructor(private readonly dispatch:GdssScenarioDispatcher,private readonly repository=new GdssExperimentRepository()){ }
  async runBatch(attemptId:string){const claims=await this.repository.claim(attemptId,GDSS_EXPERIMENT_LIMITS_V1.concurrentScenarioDispatches);return Promise.all(claims.map(async claim=>{if(simulationInputHash(claim.manifest)!==claim.simulationInputHash)throw Error("IDENTITY_MISMATCH");const key=`gdss-experiment:v1:${claim.projectId}:${claim.scenarioDefinitionHash}:${claim.simulationInputHash}`;if(key.length>256)throw Error("RESOURCE_LIMIT_EXCEEDED");try{const result=await this.dispatch(claim,key);await this.repository.markDispatched(claim,result.simulationAttemptId);await this.repository.markScenarioTerminal(claim,result.simulationAttemptId,result);return result;}catch(error){if(claim.dispatchAttempt===3)await this.repository.markDispatchExhausted(claim);if(claim.dispatchAttempt<3)return null;throw error;}}));}
  async recover(now=new Date()){const attempts=await this.repository.recoverableAttempts(now);for(const attemptId of attempts)await this.runBatch(attemptId);return attempts.length;}
}
