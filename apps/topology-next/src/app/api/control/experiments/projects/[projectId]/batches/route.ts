import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ExperimentBatchService } from "@/lib/services/experiment-batch.service";
import { uuidSchema } from "@/lib/validators/common";
import { createExperimentBatchSchema } from "@/lib/validators/experiment-batch.schemas";
const service=new ExperimentBatchService(); interface Params{params:Promise<{projectId:string}>;}
export const GET=withRouteErrorHandling(async(request:Request,{params}:Params)=>{const actor=await resolveAuthenticatedControlActor(request);const {projectId}=await params;return ok(await service.list(actor,uuidSchema.parse(projectId)));});
export const POST=withRouteErrorHandling(async(request:Request,{params}:Params)=>{const actor=await resolveAuthenticatedControlActor(request);const {projectId}=await params;return ok(await service.create(actor,uuidSchema.parse(projectId),createExperimentBatchSchema.parse(await request.json())),201);});
