import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssValidationRunService } from "@/lib/services/gdss-validation-run.service";
import { uuidSchema } from "@/lib/validators/common";
import { runTransitionSchema } from "@/lib/validators/gdss-validation-run.schemas";
import { z } from "zod";
const service = new GdssValidationRunService(),
  actionSchema = z.enum(["ready", "start", "complete", "fail", "invalidate"]);
export const POST = withRouteErrorHandling(
  async (
    r: Request,
    {
      params,
    }: {
      params: Promise<{ projectId: string; runId: string; action: string }>;
    },
  ) => {
    const a = await resolveAuthenticatedControlActor(r),
      p = await params,
      project = uuidSchema.parse(p.projectId),
      id = uuidSchema.parse(p.runId),
      action = actionSchema.parse(p.action),
      v = runTransitionSchema.parse(await r.json()),
      args = [a, project, id, v.reason, v.idempotencyKey] as const;
    return ok(
      await (action === "ready"
        ? service.markValidationRunReady(...args)
        : action === "start"
          ? service.startValidationRun(...args)
          : action === "complete"
            ? service.completeValidationRun(...args)
            : action === "fail"
              ? service.failValidationRun(...args)
              : service.invalidateValidationRun(...args)),
    );
  },
);
