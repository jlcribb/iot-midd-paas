import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ExperimentRankingService } from "@/lib/services/experiment-ranking.service";
import { uuidSchema } from "@/lib/validators/common";
import { createExperimentRankingSchema } from "@/lib/validators/experiment-ranking.schemas";

const service=new ExperimentRankingService(); interface Params{params:Promise<{projectId:string;batchId:string}>;}
export const GET=withRouteErrorHandling(async(request:Request,{params}:Params)=>{const actor=await resolveAuthenticatedControlActor(request);const {projectId,batchId}=await params;return ok(await service.list(actor,uuidSchema.parse(projectId),uuidSchema.parse(batchId)));});
export const POST=withRouteErrorHandling(async(request:Request,{params}:Params)=>{const actor=await resolveAuthenticatedControlActor(request);const {projectId,batchId}=await params;const input=createExperimentRankingSchema.parse(await request.json());return ok(await service.create(actor,uuidSchema.parse(projectId),uuidSchema.parse(batchId),input.policyVersion),201);});
