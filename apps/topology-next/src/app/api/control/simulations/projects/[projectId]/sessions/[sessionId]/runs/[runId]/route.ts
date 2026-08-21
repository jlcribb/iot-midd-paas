import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { SimulationRunService } from "@/lib/services/simulation-run.service";
import { uuidSchema } from "@/lib/validators/common";
const service = new SimulationRunService();
interface RouteParams { params: Promise<{ projectId: string; sessionId: string; runId: string }>; }
export const GET = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => { const actor = await resolveAuthenticatedControlActor(request); const values = await params; return ok(await service.get(actor, uuidSchema.parse(values.projectId), uuidSchema.parse(values.sessionId), uuidSchema.parse(values.runId))); });
