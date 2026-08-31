import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ExperimentBatchService } from "@/lib/services/experiment-batch.service";
import { uuidSchema } from "@/lib/validators/common";
const service=new ExperimentBatchService(); interface Params{params:Promise<{projectId:string;batchId:string}>;}
export const GET=withRouteErrorHandling(async(request:Request,{params}:Params)=>{const actor=await resolveAuthenticatedControlActor(request);const {projectId,batchId}=await params;return ok(await service.items(actor,uuidSchema.parse(projectId),uuidSchema.parse(batchId)));});
