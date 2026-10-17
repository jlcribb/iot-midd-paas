import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssEvidenceCustodyService } from "@/lib/services/gdss-evidence-custody.service";
import { uuidSchema } from "@/lib/validators/common";
import { custodyTransitionSchema } from "@/lib/validators/gdss-evidence-custody.schemas";
import { z } from "zod";
const service = new GdssEvidenceCustodyService(),
  actionSchema = z.enum(["open", "consume", "retire", "invalidate"]);
export const POST = withRouteErrorHandling(
  async (
    r: Request,
    {
      params,
    }: {
      params: Promise<{ projectId: string; holdoutId: string; action: string }>;
    },
  ) => {
    const a = await resolveAuthenticatedControlActor(r),
      p = await params,
      project = uuidSchema.parse(p.projectId),
      id = uuidSchema.parse(p.holdoutId),
      action = actionSchema.parse(p.action),
      body = await r.json();
    if (action === "open")
      return ok(await service.openHoldoutForEvaluation(a, project, id, body));
    const v = custodyTransitionSchema.parse(body),
      target =
        action === "consume"
          ? "CONSUMED"
          : action === "retire"
            ? "RETIRED"
            : "INVALIDATED";
    return ok(
      await service.transitionHoldout(
        a,
        project,
        id,
        target,
        v.reason,
        v.idempotencyKey,
      ),
    );
  },
);
