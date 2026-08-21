import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { SimulationSessionService } from "@/lib/services/simulation-session.service";
import { uuidSchema } from "@/lib/validators/common";

const service = new SimulationSessionService();

interface RouteParams { params: Promise<{ projectId: string; sessionId: string }>; }

export const GET = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const { projectId: rawProjectId, sessionId: rawSessionId } = await params;
  const projectId = uuidSchema.parse(rawProjectId);
  const sessionId = uuidSchema.parse(rawSessionId);
  return ok(await service.get(actor, projectId, sessionId));
});
