import { describe, expect, it, vi } from "vitest";
import { SimulationRunService } from "@/lib/services/simulation-run.service";
import { InternalError } from "@/lib/errors/domain-errors";

const projectId="11111111-1111-4111-8111-111111111111",sessionId="22222222-2222-4222-8222-222222222222";
const actor={actor_id:"operator",user_id:"operator",display_name:"Operator",role:"operator" as const,all_projects:false,project_ids:[projectId],project_roles:{[projectId]:"operator" as const},auth_source:"oauth_session" as const};
describe("SimulationRunService",()=>{it("retains runner reachability detail for the batch failure boundary",async()=>{vi.stubGlobal("fetch",vi.fn().mockRejectedValue(new Error("getaddrinfo ENOTFOUND simulation-replay-runner")));await expect(new SimulationRunService().execute(actor,projectId,sessionId)).rejects.toMatchObject({message:"Simulation replay runner is unavailable: getaddrinfo ENOTFOUND simulation-replay-runner"} satisfies Partial<InternalError>);vi.unstubAllGlobals();});});
