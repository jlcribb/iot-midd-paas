import type {ControlActor} from "@/lib/dto/control-access.dto";
import {
  assertDecisionAccess,
  canonicalScenarioEvaluation,
  completeEvaluationInputSchema,
  failEvaluationInputSchema,
  invalidateEvaluationInputSchema,
  startEvaluationInputSchema,
  type CompleteEvaluationInput,
} from "@/lib/gdss/decision";
import {DecisionError} from "@/lib/gdss/decision/diagnostics";
import {canonicalValidationJson,isAiAuthority} from "@/lib/gdss/validation";
import {artifactContentHash,GdssScenarioEvaluationRepository} from "@/lib/repositories/gdss-scenario-evaluation.repository";

const outputKey=(value:{target:string;horizon:string;quantity:string;unit:unknown})=>
  canonicalValidationJson({target:value.target,horizon:value.horizon,quantity:value.quantity,unit:value.unit});

export class ScenarioEvaluationService{
  constructor(private readonly repository=new GdssScenarioEvaluationRepository()){}

  private async denyAi(actor:ControlActor,projectId:string,evaluationId:string|undefined,key:string){
    if(!isAiAuthority(actor))return;
    if(evaluationId)await this.repository.recordAiDenial(actor,projectId,evaluationId,"AI cannot execute or alter authoritative scenario evidence",`${key}:ai-denial`);
    throw new DecisionError("AI_AUTHORITY_FORBIDDEN",undefined,403);
  }

  async admitEvaluation(actor:ControlActor,projectId:string,raw:unknown){
    const input=canonicalScenarioEvaluation(raw);
    await this.denyAi(actor,projectId,undefined,input.idempotencyKey);
    assertDecisionAccess(actor,projectId,"RUN_SCENARIO_EVALUATION");
    const [scenario,alternative,problem,model]=await Promise.all([
      this.repository.getScenario(projectId,input.scenarioDefinitionId),
      this.repository.getAlternative(projectId,input.alternativeVersionId),
      this.repository.getProblem(projectId,input.problemVersionId),
      this.repository.getModel(projectId,input.modelVersionId),
    ]);
    if(!scenario||!alternative||!problem||!model)throw new DecisionError("CROSS_PROJECT_DECISION_REFERENCE");
    if(scenario.status!=="ADMITTED")throw new DecisionError("SCENARIO_NOT_ADMISSIBLE");
    if(scenario.alternative_version_id!==alternative.id||scenario.problem_version_id!==problem.id||alternative.problem_version_id!==problem.id)
      throw new DecisionError("CROSS_PROJECT_DECISION_REFERENCE");
    if(scenario.scenario_hash!==input.scenarioHash||alternative.alternative_hash!==input.alternativeHash||problem.decision_problem_hash!==input.problemHash||
      scenario.model_version_id!==model.id||scenario.model_content_hash!==input.modelHash||model.content_hash!==input.modelHash||
      canonicalValidationJson(scenario.decision_context_snapshot)!==canonicalValidationJson(input.decisionContextSnapshot)||
      scenario.input_snapshot_hash!==input.inputHash||scenario.method_version!==input.methodVersion||scenario.resource_profile!==input.resourceProfile)
      throw new DecisionError("DECISION_INPUT_NOT_CURRENT");
    return this.repository.admit(actor,projectId,input);
  }

  async startEvaluation(actor:ControlActor,projectId:string,evaluationId:string,raw:unknown){
    const input=startEvaluationInputSchema.parse(raw);await this.denyAi(actor,projectId,evaluationId,input.idempotencyKey);
    assertDecisionAccess(actor,projectId,"RUN_SCENARIO_EVALUATION");
    return this.repository.start(actor,projectId,evaluationId,input.reason,input.idempotencyKey,input.technicalMetadata);
  }

  async recordAttemptFailure(actor:ControlActor,projectId:string,evaluationId:string,raw:unknown){
    const input=failEvaluationInputSchema.parse(raw);await this.denyAi(actor,projectId,evaluationId,input.idempotencyKey);
    assertDecisionAccess(actor,projectId,"RUN_SCENARIO_EVALUATION");
    return this.repository.recordAttemptFailure(actor,projectId,evaluationId,input.attemptId,input.diagnostics,input.reason,input.idempotencyKey);
  }

  private async validateTerminal(projectId:string,evaluationId:string,to:"COMPLETED"|"COMPLETED_WITH_LIMITATIONS",input:CompleteEvaluationInput){
    if(artifactContentHash(input.artifact.canonicalBytes)!==input.artifact.contentHash)throw new DecisionError("ARTIFACT_INTEGRITY_FAILURE");
    const evaluation=await this.repository.read(projectId,evaluationId);if(!evaluation)throw new DecisionError("CROSS_PROJECT_DECISION_REFERENCE");
    const required=new Set((evaluation.execution_manifest.requiredOutputs as Array<{target:string;horizon:string;quantity:string;unit:unknown}>).map(outputKey));
    const produced=new Set(input.outcomes.map(outputKey));
    if(produced.size!==input.outcomes.length||[...produced].some(key=>!required.has(key)))throw new DecisionError("SCENARIO_EVALUATION_INCOMPLETE");
    const missing=[...required].filter(key=>!produced.has(key));
    if(to==="COMPLETED"&&(missing.length||input.limitations.length||input.missingOutputs.length))throw new DecisionError("SCENARIO_EVALUATION_INCOMPLETE");
    if(to==="COMPLETED_WITH_LIMITATIONS"&&!missing.length&&!input.limitations.length&&!input.missingOutputs.length)throw new DecisionError("SCENARIO_EVALUATION_INCOMPLETE");
    if(to==="COMPLETED_WITH_LIMITATIONS"&&missing.length&&!input.missingOutputs.length)throw new DecisionError("SCENARIO_EVALUATION_INCOMPLETE");
  }

  async completeEvaluation(actor:ControlActor,projectId:string,evaluationId:string,raw:unknown){return this.complete(actor,projectId,evaluationId,"COMPLETED",raw);}
  async completeWithLimitations(actor:ControlActor,projectId:string,evaluationId:string,raw:unknown){return this.complete(actor,projectId,evaluationId,"COMPLETED_WITH_LIMITATIONS",raw);}
  private async complete(actor:ControlActor,projectId:string,evaluationId:string,to:"COMPLETED"|"COMPLETED_WITH_LIMITATIONS",raw:unknown){
    const input=completeEvaluationInputSchema.parse(raw);await this.denyAi(actor,projectId,evaluationId,input.idempotencyKey);
    assertDecisionAccess(actor,projectId,"RUN_SCENARIO_EVALUATION");await this.validateTerminal(projectId,evaluationId,to,input);
    return this.repository.complete(actor,projectId,evaluationId,to,input);
  }

  async failEvaluation(actor:ControlActor,projectId:string,evaluationId:string,raw:unknown){
    const input=failEvaluationInputSchema.parse(raw);await this.denyAi(actor,projectId,evaluationId,input.idempotencyKey);
    assertDecisionAccess(actor,projectId,"RUN_SCENARIO_EVALUATION");return this.repository.fail(actor,projectId,evaluationId,input.attemptId,input.diagnostics,input.reason,input.idempotencyKey);
  }
  async invalidateEvaluation(actor:ControlActor,projectId:string,evaluationId:string,raw:unknown){
    const input=invalidateEvaluationInputSchema.parse(raw);await this.denyAi(actor,projectId,evaluationId,input.idempotencyKey);
    assertDecisionAccess(actor,projectId,"INVALIDATE_SCENARIO_EVALUATION");return this.repository.invalidate(actor,projectId,evaluationId,input.reason,input.idempotencyKey);
  }
  readExactEvaluation(actor:ControlActor,projectId:string,evaluationId:string){assertDecisionAccess(actor,projectId,"AUDIT_DECISION_SUPPORT");return this.repository.read(projectId,evaluationId);}
}
