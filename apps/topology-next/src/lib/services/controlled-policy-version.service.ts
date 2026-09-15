import {assertControlPermission} from "@/lib/auth/control-access";
import type {ControlActor} from "@/lib/dto/control-access.dto";
import {NotFoundError} from "@/lib/errors/domain-errors";
import {ProjectRepository} from "@/lib/repositories/project.repository";
import {ControlledPolicyVersionRepository} from "@/lib/repositories/controlled-policy-version.repository";

export class ControlledPolicyVersionService {
  constructor(private repo=new ControlledPolicyVersionRepository(),private projects=new ProjectRepository()){}
  private async auth(actor:ControlActor,projectId:string,permission:"view_dashboard"|"edit_policies"){assertControlPermission(actor,permission,projectId);if(!await this.projects.findById(projectId))throw new NotFoundError("Project not found");}
  async create(actor:ControlActor,projectId:string,proposalId:string){await this.auth(actor,projectId,"edit_policies");return this.repo.createOrGet(projectId,proposalId,actor.actor_id??actor.user_id);}
  async list(actor:ControlActor,projectId:string,strategyType?:"proportional"|"threshold"){await this.auth(actor,projectId,"view_dashboard");return this.repo.list(projectId,strategyType);}
  async get(actor:ControlActor,projectId:string,id:string){await this.auth(actor,projectId,"view_dashboard");const candidate=await this.repo.get(projectId,id);if(!candidate)throw new NotFoundError("Controlled policy version candidate not found in project scope");return candidate;}
}
