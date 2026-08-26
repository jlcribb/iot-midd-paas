import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ExperimentEvaluationService } from "@/lib/services/experiment-evaluation.service";
import { uuidSchema } from "@/lib/validators/common";
import { createExperimentEvaluationSchema } from "@/lib/validators/experiment-evaluation.schemas";

const service = new ExperimentEvaluationService();
interface RouteParams { params: Promise<{ projectId: string }>; }

export const GET = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const { projectId } = await params;
  return ok(await service.list(actor, uuidSchema.parse(projectId)));
});

export const POST = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const { projectId } = await params;
  const input = createExperimentEvaluationSchema.parse(await request.json());
  return ok(await service.evaluate(actor, uuidSchema.parse(projectId), input.simulationResultId, input.evaluationProfileId), 201);
});
