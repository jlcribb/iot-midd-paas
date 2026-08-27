import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ExperimentComparisonService } from "@/lib/services/experiment-comparison.service";
import { uuidSchema } from "@/lib/validators/common";
import { createExperimentComparisonSchema } from "@/lib/validators/experiment-comparison.schemas";

const service = new ExperimentComparisonService();
interface RouteParams { params: Promise<{ projectId: string }>; }
export const GET = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request); const { projectId } = await params;
  return ok(await service.list(actor, uuidSchema.parse(projectId)));
});
export const POST = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request); const { projectId } = await params;
  const input = createExperimentComparisonSchema.parse(await request.json());
  return ok(await service.compare(actor, uuidSchema.parse(projectId), input.baselineEvaluationId, input.candidateEvaluationId), 201);
});
