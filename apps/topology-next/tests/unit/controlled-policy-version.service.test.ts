import {describe,expect,it,vi} from "vitest";
import {ForbiddenError,NotFoundError} from "@/lib/errors/domain-errors";
import {ControlledPolicyVersionService} from "@/lib/services/controlled-policy-version.service";

const projectId="11111111-1111-4111-8111-111111111111";
const proposalId="22222222-2222-4222-8222-222222222222";
const viewer={actor_id:"viewer",user_id:"viewer",display_name:"Viewer",role:"viewer" as const,all_projects:false,project_ids:[projectId],project_roles:{[projectId]:"viewer" as const},auth_source:"oauth_session" as const};
const editor={...viewer,actor_id:"editor",user_id:"editor",role:"operator" as const,project_roles:{[projectId]:"operator" as const}};
describe("ControlledPolicyVersionService",()=>{it("allows dashboard reads, protects writes, and preserves project isolation",async()=>{const repo={list:vi.fn().mockResolvedValue([]),get:vi.fn().mockResolvedValue(null),createOrGet:vi.fn().mockResolvedValue({id:"candidate"})};const projects={findById:vi.fn().mockResolvedValue({id:projectId})};const service=new ControlledPolicyVersionService(repo as never,projects as never);await expect(service.list(viewer,projectId)).resolves.toEqual([]);await expect(service.create(viewer,projectId,proposalId)).rejects.toBeInstanceOf(ForbiddenError);await expect(service.create(editor,projectId,proposalId)).resolves.toEqual({id:"candidate"});await expect(service.get(viewer,projectId,"33333333-3333-4333-8333-333333333333")).rejects.toBeInstanceOf(NotFoundError);});});
