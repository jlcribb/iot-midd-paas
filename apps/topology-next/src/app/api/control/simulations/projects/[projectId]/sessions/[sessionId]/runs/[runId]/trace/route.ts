import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { SimulationRunService } from "@/lib/services/simulation-run.service";
import { uuidSchema } from "@/lib/validators/common";
const service = new SimulationRunService();
interface RouteParams { params: Promise<{ projectId: string; sessionId: string; runId: string }>; }
function pagination(request: Request) { const url = new URL(request.url); const limit = Number(url.searchParams.get("limit") ?? "100"); const offset = Number(url.searchParams.get("offset") ?? "0"); if (!Number.isInteger(limit) || limit < 1 || limit > 500 || !Number.isInteger(offset) || offset < 0) throw new Error("Invalid trace pagination"); return { limit, offset }; }
export const GET = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => { const actor = await resolveAuthenticatedControlActor(request); const values = await params; const page = pagination(request); return ok(await service.trace(actor, uuidSchema.parse(values.projectId), uuidSchema.parse(values.sessionId), uuidSchema.parse(values.runId), page.limit, page.offset)); });
