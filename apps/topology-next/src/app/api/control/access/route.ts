import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ControlAccessService } from "@/lib/services/control-access.service";

const controlAccessService = new ControlAccessService();

export const GET = withRouteErrorHandling(async (request: Request) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const snapshot = await controlAccessService.getSnapshot(actor);
  return ok(snapshot);
});
