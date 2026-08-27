import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ExperimentComparisonService } from "@/lib/services/experiment-comparison.service";
import { uuidSchema } from "@/lib/validators/common";

const service = new ExperimentComparisonService();
interface RouteParams { params: Promise<{ projectId: string; comparisonId: string }>; }
export const GET = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request); const { projectId, comparisonId } = await params;
  return ok(await service.get(actor, uuidSchema.parse(projectId), uuidSchema.parse(comparisonId)));
});
