import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { SimulationSessionService } from "@/lib/services/simulation-session.service";
import { createSimulationSessionSchema } from "@/lib/validators/simulation-session.schemas";
import { uuidSchema } from "@/lib/validators/common";

const service = new SimulationSessionService();

interface RouteParams { params: Promise<{ projectId: string }>; }

export const GET = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const { projectId: rawProjectId } = await params;
  const projectId = uuidSchema.parse(rawProjectId);
  return ok(await service.list(actor, projectId));
});

export const POST = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const { projectId: rawProjectId } = await params;
  const projectId = uuidSchema.parse(rawProjectId);
  const input = createSimulationSessionSchema.parse(await request.json());
  return ok(await service.create(actor, projectId, input), 201);
});
