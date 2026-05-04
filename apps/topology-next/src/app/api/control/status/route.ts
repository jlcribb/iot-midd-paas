import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ControlObservabilityService } from "@/lib/services/control-observability.service";

const controlObservabilityService = new ControlObservabilityService();

export const GET = withRouteErrorHandling(async (request: Request) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const status = await controlObservabilityService.getStatus(actor);
  return ok(status);
});
