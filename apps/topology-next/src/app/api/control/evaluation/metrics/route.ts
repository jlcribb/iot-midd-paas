import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { EvaluationProfileService } from "@/lib/services/evaluation-profile.service";

const service = new EvaluationProfileService();

export const GET = withRouteErrorHandling(async (request: Request) => {
  const actor = await resolveAuthenticatedControlActor(request);
  return ok(await service.listMetrics(actor));
});
