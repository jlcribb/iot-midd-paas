import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { StrategyRecommendationService } from "@/lib/services/strategy-recommendation.service";
import { uuidSchema } from "@/lib/validators/common";
const service=new StrategyRecommendationService();interface Params{params:Promise<{projectId:string;rankingId:string}>;}
export const POST=withRouteErrorHandling(async(request:Request,{params}:Params)=>{const actor=await resolveAuthenticatedControlActor(request);const {projectId,rankingId}=await params;await request.json().catch(()=>({}));return ok(await service.create(actor,uuidSchema.parse(projectId),uuidSchema.parse(rankingId)),201);});
