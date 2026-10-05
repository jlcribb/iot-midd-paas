import { canAccessProject,getControlRoleForProject } from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { ForbiddenError } from "@/lib/errors/domain-errors";
export type ExperimentCapability="READ_EXPERIMENT"|"CREATE_EXPERIMENT"|"VALIDATE_EXPERIMENT"|"PUBLISH_EXPERIMENT"|"RUN_EXPERIMENT"|"DEPRECATE_EXPERIMENT"|"ABORT_EXPERIMENT";
const allowed:Record<ExperimentCapability,readonly string[]>={READ_EXPERIMENT:["viewer","operator","admin"],CREATE_EXPERIMENT:["operator","admin"],VALIDATE_EXPERIMENT:["operator","admin"],PUBLISH_EXPERIMENT:["admin"],RUN_EXPERIMENT:["operator","admin"],DEPRECATE_EXPERIMENT:["admin"],ABORT_EXPERIMENT:["admin"]};
export function assertExperimentAccess(actor:ControlActor,projectId:string,capability:ExperimentCapability){if(actor.auth_source!=="oauth_session"||!actor.user_id||!canAccessProject(actor,projectId))throw new ForbiddenError("GDSS experiment requires scoped OAuth membership");const role=getControlRoleForProject(actor,projectId);if(!role||!allowed[capability].includes(role))throw new ForbiddenError(`${capability} is not authorized for project role`);}
