import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { SimulationRunService } from "@/lib/services/simulation-run.service";
import { uuidSchema } from "@/lib/validators/common";
import { ValidationError } from "@/lib/errors/domain-errors";
const service = new SimulationRunService();
interface RouteParams { params: Promise<{ projectId: string; sessionId: string }>; }
export const POST = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => { const actor = await resolveAuthenticatedControlActor(request); const values = await params; return ok(await service.execute(actor, uuidSchema.parse(values.projectId), uuidSchema.parse(values.sessionId)), 201); });
export const GET = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const values = await params;
  const query = new URL(request.url).searchParams;
  const limit = Math.min(200, Math.max(1, Number(query.get("limit") ?? 100)));
  const offset = Math.max(0, Number(query.get("offset") ?? 0));
  if (!Number.isInteger(limit) || !Number.isInteger(offset)) throw new ValidationError("Run pagination must use integers");
  return ok(await service.list(actor, uuidSchema.parse(values.projectId), uuidSchema.parse(values.sessionId), limit, offset));
});
