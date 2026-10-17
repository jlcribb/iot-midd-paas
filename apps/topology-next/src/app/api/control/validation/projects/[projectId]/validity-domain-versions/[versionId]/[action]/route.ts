import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssValidationFoundationService } from "@/lib/services/gdss-validation-foundation.service";
import { domainStates, type DomainState } from "@/lib/gdss/validation";
import { uuidSchema } from "@/lib/validators/common";
import { validationTransitionSchema } from "@/lib/validators/gdss-validation-foundation.schemas";
import { z } from "zod";
const service = new GdssValidationFoundationService(),
  actions = {
    approve: "APPROVED",
    seal: "SEALED",
    supersede: "SUPERSEDED",
    invalidate: "INVALIDATED",
  } as const;
export const POST = withRouteErrorHandling(
  async (
    request: Request,
    {
      params,
    }: {
      params: Promise<{ projectId: string; versionId: string; action: string }>;
    },
  ) => {
    const actor = await resolveAuthenticatedControlActor(request),
      p = await params,
      input = validationTransitionSchema.parse(await request.json()),
      target =
        actions[
          z.enum(["approve", "seal", "supersede", "invalidate"]).parse(p.action)
        ];
    return ok(
      await service.transitionDomain(
        actor,
        uuidSchema.parse(p.projectId),
        uuidSchema.parse(p.versionId),
        z.enum(domainStates).parse(target) as DomainState,
        input.reason,
        input.idempotencyKey,
        input.sodExceptionReason,
      ),
    );
  },
);
