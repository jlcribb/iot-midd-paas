import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { StrategySearchSpaceService } from "@/lib/services/strategy-search-space.service";
import { uuidSchema } from "@/lib/validators/common";

const service = new StrategySearchSpaceService();
interface RouteParams { params: Promise<{ projectId: string; searchSpaceId: string }>; }

export const GET = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const { projectId, searchSpaceId } = await params;
  return ok(await service.get(actor, uuidSchema.parse(projectId), uuidSchema.parse(searchSpaceId)));
});
