import { canAccessProject, getControlRoleForProject } from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { ForbiddenError } from "@/lib/errors/domain-errors";

export const GDSS_RUN_SIMULATION_CAPABILITY = "RUN_SIMULATION" as const;
export type SimulationOperation = "create_binding"|"publish_binding"|"run_simulation"|"read_evidence";

export function assertSimulationAccess(actor:ControlActor,projectId:string,operation:SimulationOperation) {
  if(actor.auth_source!=="oauth_session"||!actor.user_id||!canAccessProject(actor,projectId)) throw new ForbiddenError("GDSS simulation requires scoped OAuth membership");
  const role=getControlRoleForProject(actor,projectId);
  if(operation==="read_evidence") return;
  if(role==="viewer") throw new ForbiddenError("RUN_SIMULATION requires operator or admin");
  if(operation==="publish_binding"&&role!=="admin") throw new ForbiddenError("Dynamic binding publication requires admin");
}
