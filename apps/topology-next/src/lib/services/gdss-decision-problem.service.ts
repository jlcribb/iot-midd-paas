import type { ControlActor } from "@/lib/dto/control-access.dto";
import { assertDecisionAccess, canonicalDecisionProblem, decisionIdentityInputSchema, decisionTransitionInputSchema, reconcileDecisionEvidence } from "@/lib/gdss/decision";
import { isScopeSubset, isAiAuthority, capabilityScopeSchema } from "@/lib/gdss/validation";
import { DecisionError } from "@/lib/gdss/decision/diagnostics";
import { GdssDecisionRepository } from "@/lib/repositories/gdss-decision.repository";

export class DecisionProblemService {
  constructor(private readonly repository = new GdssDecisionRepository()) {}
  createIdentity(actor:ControlActor,projectId:string,raw:unknown){assertDecisionAccess(actor,projectId,"AUTHOR_DECISION_PROBLEM");const input=decisionIdentityInputSchema.parse(raw);return this.repository.createIdentity(actor,projectId,"problem",input.canonicalKey,input.idempotencyKey);}
  async createDraft(actor:ControlActor,projectId:string,raw:unknown){
    assertDecisionAccess(actor,projectId,"AUTHOR_DECISION_PROBLEM");
    const input=canonicalDecisionProblem(raw);
    const preference=await this.repository.getVersion(projectId,"preference",input.preferenceProfileVersionId),risk=await this.repository.getVersion(projectId,"risk",input.riskProfileVersionId);
    if(!preference||preference.content_hash!==input.preferenceProfileHash||!isScopeSubset(input.context.scope,capabilityScopeSchema.parse(preference.scope)))throw new DecisionError("PREFERENCE_PROFILE_MISMATCH");
    if(!risk||risk.content_hash!==input.riskProfileHash||!isScopeSubset(input.context.scope,capabilityScopeSchema.parse(risk.scope)))throw new DecisionError("DECISION_INPUT_NOT_CURRENT");
    let limited=false;
    for(const binding of input.context.evidenceBindings){const facts=await this.repository.getEvidenceFacts(projectId,binding),result=reconcileDecisionEvidence({...facts,decisionScope:input.context.scope});limited ||= result.reviewRequired;}
    return this.repository.createProblemDraft(actor,projectId,input,{eligibility:limited?"CANNOT_SUPPORT_AUTHORIZED_RECOMMENDATION_V1":"AUTHORIZED_RECOMMENDATION_V1_ELIGIBLE",reviewRequired:limited});
  }
  async updateDraft(actor:ControlActor,projectId:string,id:string,raw:unknown){
    assertDecisionAccess(actor,projectId,"AUTHOR_DECISION_PROBLEM");
    const input=canonicalDecisionProblem(raw),preference=await this.repository.getVersion(projectId,"preference",input.preferenceProfileVersionId),risk=await this.repository.getVersion(projectId,"risk",input.riskProfileVersionId);
    if(!preference||preference.content_hash!==input.preferenceProfileHash||!isScopeSubset(input.context.scope,capabilityScopeSchema.parse(preference.scope)))throw new DecisionError("PREFERENCE_PROFILE_MISMATCH");
    if(!risk||risk.content_hash!==input.riskProfileHash||!isScopeSubset(input.context.scope,capabilityScopeSchema.parse(risk.scope)))throw new DecisionError("DECISION_INPUT_NOT_CURRENT");
    let limited=false;for(const binding of input.context.evidenceBindings){const result=reconcileDecisionEvidence({...await this.repository.getEvidenceFacts(projectId,binding),decisionScope:input.context.scope});limited ||= result.reviewRequired;}
    return this.repository.updateProblemDraft(actor,projectId,id,input,{eligibility:limited?"CANNOT_SUPPORT_AUTHORIZED_RECOMMENDATION_V1":"AUTHORIZED_RECOMMENDATION_V1_ELIGIBLE",reviewRequired:limited});
  }
  createSuccessor(actor:ControlActor,projectId:string,raw:unknown){return this.createDraft(actor,projectId,raw);}
  readExactVersion(actor:ControlActor,projectId:string,id:string){assertDecisionAccess(actor,projectId,"AUDIT_DECISION_SUPPORT");return this.repository.getVersion(projectId,"problem",id);}
  async transition(actor:ControlActor,projectId:string,id:string,toStatus:"REVIEW_REQUIRED"|"SEALED"|"INVALIDATED",raw:unknown){
    const input=decisionTransitionInputSchema.parse(raw),permission=toStatus==="REVIEW_REQUIRED"?"AUTHOR_DECISION_PROBLEM":"SEAL_DECISION_PROBLEM" as const;
    if((toStatus==="REVIEW_REQUIRED"||toStatus==="SEALED")&&isAiAuthority(actor)){await this.repository.recordAiDenial(actor,projectId,"problem",id,"AI cannot perform authoritative decision lifecycle review",`${input.idempotencyKey}:ai-denial`);throw new DecisionError("AI_AUTHORITY_FORBIDDEN",undefined,403);}
    assertDecisionAccess(actor,projectId,permission);
    return this.repository.transition(actor,projectId,"problem",id,toStatus,input.reason,input.idempotencyKey,input.expectedContentHash,input.sodException?.reason);
  }
}
