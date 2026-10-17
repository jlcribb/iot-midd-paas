import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssEvidenceCustodyService } from "@/lib/services/gdss-evidence-custody.service";
import { uuidSchema } from "@/lib/validators/common";
import { custodyTransitionSchema } from "@/lib/validators/gdss-evidence-custody.schemas";
import { z } from "zod";
const service = new GdssEvidenceCustodyService(),
  actions = {
    submit: "REVIEW_REQUIRED",
    return_to_draft: "DRAFT",
    approve: "APPROVED",
    publish: "PUBLISHED",
    supersede: "SUPERSEDED",
    invalidate: "INVALIDATED",
  } as const,
  actionSchema = z.enum(
    Object.keys(actions) as [
      keyof typeof actions,
      ...Array<keyof typeof actions>,
    ],
  );
export const POST = withRouteErrorHandling(
  async (
    r: Request,
    {
      params,
    }: {
      params: Promise<{ projectId: string; versionId: string; action: string }>;
    },
  ) => {
    const a = await resolveAuthenticatedControlActor(r),
      p = await params,
      v = custodyTransitionSchema.parse(await r.json()),
      action = actionSchema.parse(p.action);
    return ok(
      await service.transitionPartitionPlan(
        a,
        uuidSchema.parse(p.projectId),
        uuidSchema.parse(p.versionId),
        actions[action],
        v.reason,
        v.idempotencyKey,
      ),
    );
  },
);
