import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { optionalQuery, parseOperationsPage } from "@/lib/http/control-operations-query";
import { ControlOperationsService } from "@/lib/services/control-operations.service";

const service = new ControlOperationsService();

export const GET = withRouteErrorHandling(async (request: Request, context: { params: Promise<{ projectId: string }> }) => {
    const actor = await resolveAuthenticatedControlActor(request);
    const { projectId } = await context.params;
    const query = new URL(request.url).searchParams;
    return ok(await service.listDeliveries(actor, projectId, {
      ...parseOperationsPage(query),
      status: optionalQuery(query, "status"),
      recommendationId: optionalQuery(query, "recommendationId"),
      commandId: optionalQuery(query, "commandId"),
      correlationId: optionalQuery(query, "correlationId"),
    }));
});
