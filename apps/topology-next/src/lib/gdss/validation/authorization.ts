import { canAccessProject,getControlRoleForProject } from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { ForbiddenError } from "@/lib/errors/domain-errors";
export type ValidationFoundationCapability="READ_VALIDATION_PROTOCOL"|"AUTHOR_VALIDATION_PROTOCOL"|"APPROVE_VALIDATION_PROTOCOL";
const allowed:Record<ValidationFoundationCapability,readonly string[]>={READ_VALIDATION_PROTOCOL:["viewer","operator","admin"],AUTHOR_VALIDATION_PROTOCOL:["operator","admin"],APPROVE_VALIDATION_PROTOCOL:["admin"]};
export function assertValidationFoundationAccess(actor:ControlActor,projectId:string,capability:ValidationFoundationCapability){
  if(actor.auth_source!=="oauth_session"||!actor.user_id||!canAccessProject(actor,projectId))throw new ForbiddenError("UNAUTHORIZED_VALIDATION_PROTOCOL_ACTION");
  if(!allowed[capability].includes(getControlRoleForProject(actor,projectId)))throw new ForbiddenError("UNAUTHORIZED_VALIDATION_PROTOCOL_ACTION");
}
