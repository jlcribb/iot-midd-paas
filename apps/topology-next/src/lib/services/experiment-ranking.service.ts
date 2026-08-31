import { assertControlPermission } from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { DEFAULT_RANKING_POLICY, RANKING_POLICY_VERSION, type ExperimentRanking } from "@/lib/dto/experiment-ranking.dto";
import { ConflictError, NotFoundError, ValidationError } from "@/lib/errors/domain-errors";
import { rankExperimentBatch } from "@/lib/ranking/experiment-ranking-engine";
import { ExperimentBatchRepository } from "@/lib/repositories/experiment-batch.repository";
import { ExperimentRankingRepository } from "@/lib/repositories/experiment-ranking.repository";
import { ProjectRepository } from "@/lib/repositories/project.repository";

interface Deps { rankings?: Pick<ExperimentRankingRepository,"loadCohort"|"createOrGet"|"listByBatch"|"findByProjectAndId">; batches?: Pick<ExperimentBatchRepository,"findByProjectAndId">; projects?: Pick<ProjectRepository,"findById">; }
const RANKABLE_BATCH_STATUSES = new Set(["COMPLETED","COMPLETED_WITH_WARNINGS","PARTIALLY_FAILED"]);
export class ExperimentRankingService {
  private readonly rankings:NonNullable<Deps["rankings"]>; private readonly batches:NonNullable<Deps["batches"]>; private readonly projects:NonNullable<Deps["projects"]>;
  constructor(deps:Deps={}){this.rankings=deps.rankings??new ExperimentRankingRepository();this.batches=deps.batches??new ExperimentBatchRepository();this.projects=deps.projects??new ProjectRepository();}
  async create(actor:ControlActor,projectId:string,batchId:string,policyVersion=RANKING_POLICY_VERSION):Promise<ExperimentRanking>{await this.authorize(actor,projectId,"edit_policies");if(policyVersion!==RANKING_POLICY_VERSION)throw new ValidationError("Unsupported ranking policy version");const batch=await this.batches.findByProjectAndId(projectId,batchId);if(!batch)throw new NotFoundError("Experiment batch not found in project scope");if(!RANKABLE_BATCH_STATUSES.has(batch.status))throw new ConflictError("Ranking requires a terminal experiment batch");const cohort=await this.rankings.loadCohort(projectId,batchId);if(!cohort)throw new NotFoundError("Experiment batch ranking cohort not found in project scope");return this.rankings.createOrGet(projectId,actor.actor_id??actor.user_id,cohort,rankExperimentBatch(cohort,DEFAULT_RANKING_POLICY));}
  async list(actor:ControlActor,projectId:string,batchId:string):Promise<ExperimentRanking[]>{await this.authorize(actor,projectId,"view_dashboard");await this.requireBatch(projectId,batchId);return this.rankings.listByBatch(projectId,batchId);}
  async get(actor:ControlActor,projectId:string,batchId:string,rankingId:string):Promise<ExperimentRanking>{await this.authorize(actor,projectId,"view_dashboard");await this.requireBatch(projectId,batchId);const ranking=await this.rankings.findByProjectAndId(projectId,rankingId);if(!ranking||ranking.batch_id!==batchId)throw new NotFoundError("Experiment ranking not found in batch/project scope");return ranking;}
  private async requireBatch(projectId:string,batchId:string){const batch=await this.batches.findByProjectAndId(projectId,batchId);if(!batch)throw new NotFoundError("Experiment batch not found in project scope");return batch;}
  private async authorize(actor:ControlActor,projectId:string,permission:"view_dashboard"|"edit_policies"){assertControlPermission(actor,permission,projectId);if(!await this.projects.findById(projectId))throw new NotFoundError("Project not found");}
}
