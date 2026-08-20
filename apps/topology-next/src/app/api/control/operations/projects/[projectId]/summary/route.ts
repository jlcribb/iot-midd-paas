import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ControlOperationsService } from "@/lib/services/control-operations.service";

const service = new ControlOperationsService();

export const GET = withRouteErrorHandling(async (request: Request, context: { params: Promise<{ projectId: string }> }) => {
    const actor = await resolveAuthenticatedControlActor(request);
    const { projectId } = await context.params;
    return ok(await service.getSummary(actor, projectId));
});
