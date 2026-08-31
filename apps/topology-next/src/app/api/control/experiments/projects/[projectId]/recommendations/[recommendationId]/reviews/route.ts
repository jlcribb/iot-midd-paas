import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { RecommendationReviewService } from "@/lib/services/recommendation-review.service";
import { uuidSchema } from "@/lib/validators/common";
import { createRecommendationReviewSchema } from "@/lib/validators/recommendation-review.schemas";
const service = new RecommendationReviewService(); interface Params { params: Promise<{ projectId: string; recommendationId: string }>; }
export const POST = withRouteErrorHandling(async (request: Request, { params }: Params) => { const actor = await resolveAuthenticatedControlActor(request); const { projectId, recommendationId } = await params; const input = createRecommendationReviewSchema.parse(await request.json()); return ok(await service.create(actor, uuidSchema.parse(projectId), uuidSchema.parse(recommendationId), input), 201); });
