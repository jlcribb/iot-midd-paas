import type { ControlActor } from "@/lib/dto/control-access.dto";
import { assertSimulationAccess } from "@/lib/gdss/simulation/authorization";
import type { SimulationProgram } from "@/lib/gdss/simulation/contracts";
import { runSimulation } from "@/lib/gdss/simulation/runtime";
import { simulationResultHash } from "@/lib/gdss/simulation/canonical";
import type { SimulationResult } from "@/lib/gdss/simulation/contracts";
import { GdssSimulationRepository } from "@/lib/repositories/gdss-simulation.repository";

export class GdssSimulationService {
  constructor(private readonly repository=new GdssSimulationRepository()){}
  async execute(actor:ControlActor,projectId:string,program:SimulationProgram,idempotencyKey?:string){ assertSimulationAccess(actor,projectId,"run_simulation"); if(program.manifest.projectId!==projectId) throw Error("Simulation project mismatch"); const attempt=await this.repository.acceptAttempt(actor,projectId,program.manifest,idempotencyKey); if(attempt.existing) return {attempt,result:null,terminal:null}; let result=runSimulation(program); try { const terminal=await this.repository.terminal(attempt.id,result,projectId,actor.user_id); return {attempt,result,terminal}; } catch(error) { if(error instanceof Error&&error.message.includes("ARTIFACT_INTEGRITY_FAILURE")){ const diagnostics=[{code:"ARTIFACT_INTEGRITY_FAILURE" as const,severity:"ERROR" as const,stage:"PERSISTENCE" as const,details:{},message:"Content-addressed artifact collision failed exact equality verification"}]; const failed:SimulationResult={status:"FAILED",terminationReason:"ARTIFACT_INTEGRITY_FAILURE",simulationInputHash:result.simulationInputHash,trajectory:null,trajectoryHash:null,simulationResultHash:simulationResultHash({simulationInputHash:result.simulationInputHash,status:"FAILED",terminationReason:"ARTIFACT_INTEGRITY_FAILURE",completeness:null,trajectoryHash:null,diagnostics}),diagnostics,physicalAuthority:"NONE",evaluatorOperations:result.evaluatorOperations}; result=failed; const terminal=await this.repository.terminal(attempt.id,result,projectId,actor.user_id); return {attempt,result,terminal}; } const terminal=await this.repository.recoverUnknownCommit(attempt.id,result.simulationResultHash,()=>this.repository.terminal(attempt.id,result,projectId,actor.user_id)); return {attempt,result,terminal}; } }
}
