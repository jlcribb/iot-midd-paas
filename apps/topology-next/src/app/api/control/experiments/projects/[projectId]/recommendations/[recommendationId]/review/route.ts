import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { RecommendationReviewService } from "@/lib/services/recommendation-review.service";
import { uuidSchema } from "@/lib/validators/common";
const service = new RecommendationReviewService(); interface Params { params: Promise<{ projectId: string; recommendationId: string }>; }
export const GET = withRouteErrorHandling(async (request: Request, { params }: Params) => { const actor = await resolveAuthenticatedControlActor(request); const { projectId, recommendationId } = await params; return ok(await service.get(actor, uuidSchema.parse(projectId), uuidSchema.parse(recommendationId))); });
