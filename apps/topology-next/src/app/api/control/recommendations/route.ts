import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { ValidationError } from "@/lib/errors/domain-errors";
import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ControlObservabilityService } from "@/lib/services/control-observability.service";

const controlObservabilityService = new ControlObservabilityService();

export const GET = withRouteErrorHandling(async (request: Request) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const { searchParams } = new URL(request.url);
  const projectId = searchParams.get("projectId") ?? undefined;
  const limitParam = searchParams.get("limit");
  const limit = limitParam === null ? undefined : Number(limitParam);

  if (limitParam !== null && !Number.isFinite(limit)) {
    throw new ValidationError("limit must be a number");
  }

  const recommendations = await controlObservabilityService.listRecommendations(actor, {
    projectId,
    limit
  });
  return ok(recommendations);
});
