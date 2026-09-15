import {resolveAuthenticatedControlActor} from "@/lib/auth/control-auth-session";
import {ok} from "@/lib/http/response";
import {withRouteErrorHandling} from "@/lib/http/route-handler";
import {ControlledPolicyVersionService} from "@/lib/services/controlled-policy-version.service";
import {uuidSchema} from "@/lib/validators/common";
const service=new ControlledPolicyVersionService();
export const GET=withRouteErrorHandling(async(request:Request,{params}:any)=>{const actor=await resolveAuthenticatedControlActor(request),raw=await params;return ok(await service.get(actor,uuidSchema.parse(raw.projectId),uuidSchema.parse(raw.versionCandidateId)));});
