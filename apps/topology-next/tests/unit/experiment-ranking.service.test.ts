import { describe, expect, it, vi } from "vitest";
import { ExperimentRankingService } from "@/lib/services/experiment-ranking.service";
import { ConflictError, ForbiddenError } from "@/lib/errors/domain-errors";

const projectId="11111111-1111-4111-8111-111111111111",batchId="22222222-2222-4222-8222-222222222222";
const viewer={actor_id:"viewer",user_id:"viewer",display_name:"Viewer",role:"viewer" as const,all_projects:false,project_ids:[projectId],project_roles:{[projectId]:"viewer" as const},auth_source:"oauth_session" as const};
const editor={...viewer,role:"operator" as const,project_roles:{[projectId]:"operator" as const}};
const ranking={id:"33333333-3333-4333-8333-333333333333",project_id:projectId,batch_id:batchId};
function subject(status="COMPLETED"){const rankings={loadCohort:vi.fn().mockResolvedValue({project_id:projectId,batch_id:batchId,batch_hash:"a".repeat(64),evaluation_profile_id:null,evaluation_profile_version:null,items:[]}),createOrGet:vi.fn().mockResolvedValue(ranking),listByBatch:vi.fn().mockResolvedValue([]),findByProjectAndId:vi.fn().mockResolvedValue(ranking)};return {rankings,service:new ExperimentRankingService({rankings:rankings as never,batches:{findByProjectAndId:vi.fn().mockResolvedValue({id:batchId,status})} as never,projects:{findById:vi.fn().mockResolvedValue({id:projectId})}})};}
describe("ExperimentRankingService",()=>{it("requires editor permission for ranking creation",async()=>{const {service,rankings}=subject();await expect(service.create(viewer,projectId,batchId)).rejects.toBeInstanceOf(ForbiddenError);expect(rankings.loadCohort).not.toHaveBeenCalled();});it("only ranks terminal batches",async()=>{const {service}=subject("RUNNING");await expect(service.create(editor,projectId,batchId)).rejects.toBeInstanceOf(ConflictError);});it("keeps reads scoped to the requested batch",async()=>{const {service}=subject();await expect(service.get(viewer,projectId,batchId,ranking.id)).resolves.toMatchObject(ranking);});});
