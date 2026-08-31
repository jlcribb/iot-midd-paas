import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ExperimentRankingService } from "@/lib/services/experiment-ranking.service";
import { uuidSchema } from "@/lib/validators/common";

const service=new ExperimentRankingService(); interface Params{params:Promise<{projectId:string;batchId:string;rankingId:string}>;}
export const GET=withRouteErrorHandling(async(request:Request,{params}:Params)=>{const actor=await resolveAuthenticatedControlActor(request);const {projectId,batchId,rankingId}=await params;return ok(await service.get(actor,uuidSchema.parse(projectId),uuidSchema.parse(batchId),uuidSchema.parse(rankingId)));});
