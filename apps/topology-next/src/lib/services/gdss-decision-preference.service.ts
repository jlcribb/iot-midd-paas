import type { ControlActor } from "@/lib/dto/control-access.dto";
import { assertDecisionAccess, canonicalPreference, decisionIdentityInputSchema, decisionTransitionInputSchema } from "@/lib/gdss/decision";
import { isAiAuthority } from "@/lib/gdss/validation";
import { DecisionError } from "@/lib/gdss/decision/diagnostics";
import { GdssDecisionRepository } from "@/lib/repositories/gdss-decision.repository";

export class DecisionPreferenceService {
  constructor(private readonly repository = new GdssDecisionRepository()) {}
  createIdentity(actor:ControlActor,projectId:string,raw:unknown){assertDecisionAccess(actor,projectId,"AUTHOR_DECISION_PROBLEM");const input=decisionIdentityInputSchema.parse(raw);return this.repository.createIdentity(actor,projectId,"preference",input.canonicalKey,input.idempotencyKey);}
  createDraft(actor:ControlActor,projectId:string,raw:unknown){assertDecisionAccess(actor,projectId,"AUTHOR_DECISION_PROBLEM");return this.repository.createPreferenceDraft(actor,projectId,canonicalPreference(raw));}
  updateDraft(actor:ControlActor,projectId:string,id:string,raw:unknown){assertDecisionAccess(actor,projectId,"AUTHOR_DECISION_PROBLEM");return this.repository.updatePreferenceDraft(actor,projectId,id,canonicalPreference(raw));}
  createSuccessor(actor:ControlActor,projectId:string,raw:unknown){return this.createDraft(actor,projectId,raw);}
  readExactVersion(actor:ControlActor,projectId:string,id:string){assertDecisionAccess(actor,projectId,"AUDIT_DECISION_SUPPORT");return this.repository.getVersion(projectId,"preference",id);}
  async transition(actor:ControlActor,projectId:string,id:string,toStatus:"REVIEW_REQUIRED"|"SEALED"|"INVALIDATED",raw:unknown){
    const input=decisionTransitionInputSchema.parse(raw),permission=toStatus==="REVIEW_REQUIRED"?"AUTHOR_DECISION_PROBLEM":"SEAL_DECISION_PROBLEM" as const;
    if((toStatus==="REVIEW_REQUIRED"||toStatus==="SEALED")&&isAiAuthority(actor)){await this.repository.recordAiDenial(actor,projectId,"preference",id,"AI cannot review or seal preferences",`${input.idempotencyKey}:ai-denial`);throw new DecisionError("AI_AUTHORITY_FORBIDDEN",undefined,403);}
    assertDecisionAccess(actor,projectId,permission);
    return this.repository.transition(actor,projectId,"preference",id,toStatus,input.reason,input.idempotencyKey,input.expectedContentHash,input.sodException?.reason);
  }
}
