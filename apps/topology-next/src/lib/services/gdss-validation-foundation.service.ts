import type { ControlActor } from "@/lib/dto/control-access.dto";
import { assertValidationFoundationAccess,canonicalDomainContent,canonicalProtocolContent,protocolContentHash,validityDomainContentHash,canTransitionDomain,canTransitionProtocol,type DomainState,type ProtocolState } from "@/lib/gdss/validation";
import { GdssValidationFoundationRepository } from "@/lib/repositories/gdss-validation-foundation.repository";
import { ValidationFoundationError } from "@/lib/gdss/validation/diagnostics";

const keyPattern=/^[A-Za-z][A-Za-z0-9_.:-]{0,127}$/;
export class GdssValidationFoundationService{
  constructor(private readonly repository=new GdssValidationFoundationRepository()){}
  private author(actor:ControlActor,projectId:string){assertValidationFoundationAccess(actor,projectId,"AUTHOR_VALIDATION_PROTOCOL");}
  private approver(actor:ControlActor,projectId:string){assertValidationFoundationAccess(actor,projectId,"APPROVE_VALIDATION_PROTOCOL");}
  private key(value:string){if(!keyPattern.test(value))throw new ValidationFoundationError("INVALID_DOMAIN_PREDICATE","Invalid logical key",400);return value;}
  createDomainIdentity(actor:ControlActor,projectId:string,logicalKey:string){this.author(actor,projectId);return this.repository.createDomainIdentity(actor,projectId,this.key(logicalKey));}
  createDomainDraft(actor:ControlActor,projectId:string,identityId:string,input:unknown,predecessorId?:string){this.author(actor,projectId);return this.repository.createDomainDraft(actor,projectId,identityId,canonicalDomainContent(input),predecessorId);}
  updateDomainDraft(actor:ControlActor,projectId:string,versionId:string,input:unknown){this.author(actor,projectId);return this.repository.updateDomainDraft(actor,projectId,versionId,canonicalDomainContent(input));}
  async transitionDomain(actor:ControlActor,projectId:string,versionId:string,target:DomainState,reason:string,idempotencyKey:string,sodExceptionReason?:string){
    target==="DRAFT"?this.author(actor,projectId):this.approver(actor,projectId);const row=await this.repository.getDomain(projectId,versionId);if(!row)throw new ValidationFoundationError("VALIDITY_DOMAIN_VERSION_MISMATCH");if(row.status===target)return row;if(!canTransitionDomain(row.status as DomainState,target))throw new ValidationFoundationError(target==="SEALED"?"VALIDITY_DOMAIN_NOT_SEALABLE":"VALIDITY_DOMAIN_NOT_APPROVABLE");const hash=target==="SEALED"?validityDomainContentHash(row.content):undefined;return this.repository.transitionDomain(actor,projectId,versionId,{target,reason,idempotencyKey,contentHash:hash,sodExceptionReason});
  }
  createProtocolIdentity(actor:ControlActor,projectId:string,logicalKey:string){this.author(actor,projectId);return this.repository.createProtocolIdentity(actor,projectId,this.key(logicalKey));}
  createProtocolDraft(actor:ControlActor,projectId:string,identityId:string,input:unknown,predecessorId?:string){this.author(actor,projectId);return this.repository.createProtocolDraft(actor,projectId,identityId,canonicalProtocolContent(input),predecessorId);}
  updateProtocolDraft(actor:ControlActor,projectId:string,versionId:string,input:unknown){this.author(actor,projectId);return this.repository.updateProtocolDraft(actor,projectId,versionId,canonicalProtocolContent(input));}
  async transitionProtocol(actor:ControlActor,projectId:string,versionId:string,target:ProtocolState,reason:string,idempotencyKey:string,sodExceptionReason?:string){
    if(target==="DRAFT"||target==="REVIEW_REQUIRED")this.author(actor,projectId);else this.approver(actor,projectId);const row=await this.repository.getProtocol(projectId,versionId);if(!row)throw new ValidationFoundationError("VALIDATION_PROTOCOL_NOT_APPROVABLE");if(row.status===target)return row;if(!canTransitionProtocol(row.status as ProtocolState,target))throw new ValidationFoundationError(target==="SEALED"?"VALIDATION_PROTOCOL_NOT_SEALABLE":"VALIDATION_PROTOCOL_NOT_APPROVABLE");const hash=target==="SEALED"?protocolContentHash(row.content):undefined;return this.repository.transitionProtocol(actor,projectId,versionId,{target,reason,idempotencyKey,contentHash:hash,sodExceptionReason});
  }
  readDomain(actor:ControlActor,projectId:string,versionId:string){assertValidationFoundationAccess(actor,projectId,"READ_VALIDATION_PROTOCOL");return this.repository.getDomain(projectId,versionId);}
  readProtocol(actor:ControlActor,projectId:string,versionId:string){assertValidationFoundationAccess(actor,projectId,"READ_VALIDATION_PROTOCOL");return this.repository.getProtocol(projectId,versionId);}
}
