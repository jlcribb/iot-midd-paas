import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ExperimentEvaluationService } from "@/lib/services/experiment-evaluation.service";
import { uuidSchema } from "@/lib/validators/common";

const service = new ExperimentEvaluationService();
interface RouteParams { params: Promise<{ projectId: string; evaluationId: string }>; }

export const GET = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const { projectId, evaluationId } = await params;
  return ok(await service.get(actor, uuidSchema.parse(projectId), uuidSchema.parse(evaluationId)));
});
