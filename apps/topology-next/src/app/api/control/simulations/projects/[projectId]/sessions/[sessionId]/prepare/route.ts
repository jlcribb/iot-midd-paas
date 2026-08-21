import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { SimulationSessionService } from "@/lib/services/simulation-session.service";
import { prepareSimulationSessionSchema } from "@/lib/validators/simulation-session.schemas";
import { uuidSchema } from "@/lib/validators/common";

const service = new SimulationSessionService();

interface RouteParams { params: Promise<{ projectId: string; sessionId: string }>; }

export const POST = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const { projectId: rawProjectId, sessionId: rawSessionId } = await params;
  const projectId = uuidSchema.parse(rawProjectId);
  const sessionId = uuidSchema.parse(rawSessionId);
  const input = prepareSimulationSessionSchema.parse(await request.json());
  return ok(await service.prepare(actor, projectId, sessionId, input));
});
