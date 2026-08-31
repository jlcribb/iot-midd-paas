import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { StrategySearchSpaceService } from "@/lib/services/strategy-search-space.service";
import { uuidSchema } from "@/lib/validators/common";
import { createStrategySearchSpaceSchema } from "@/lib/validators/strategy-candidate.schemas";

const service = new StrategySearchSpaceService();
interface RouteParams { params: Promise<{ projectId: string }>; }

export const GET = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const { projectId } = await params;
  return ok(await service.list(actor, uuidSchema.parse(projectId)));
});

export const POST = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const { projectId } = await params;
  return ok(await service.create(actor, uuidSchema.parse(projectId), createStrategySearchSpaceSchema.parse(await request.json())), 201);
});
