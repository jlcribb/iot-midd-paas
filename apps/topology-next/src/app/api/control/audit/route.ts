import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { ValidationError } from "@/lib/errors/domain-errors";
import { resolveControlActor } from "@/lib/auth/control-access";
import { ControlObservabilityService } from "@/lib/services/control-observability.service";

const controlObservabilityService = new ControlObservabilityService();

export const GET = withRouteErrorHandling(async (request: Request) => {
  const actor = resolveControlActor(request);
  const { searchParams } = new URL(request.url);
  const projectId = searchParams.get("projectId") ?? undefined;
  const statusParam = searchParams.get("status");
  const limitParam = searchParams.get("limit");
  const limit = limitParam === null ? undefined : Number(limitParam);

  if (limitParam !== null && !Number.isFinite(limit)) {
    throw new ValidationError("limit must be a number");
  }

  const allowedStatuses = ["processed", "skipped", "error"] as const;
  if (statusParam && !allowedStatuses.includes(statusParam as (typeof allowedStatuses)[number])) {
    throw new ValidationError("Invalid status query parameter");
  }

  const auditEntries = await controlObservabilityService.listAudit(actor, {
    projectId,
    status: statusParam as "processed" | "skipped" | "error" | undefined,
    limit
  });
  return ok(auditEntries);
});
