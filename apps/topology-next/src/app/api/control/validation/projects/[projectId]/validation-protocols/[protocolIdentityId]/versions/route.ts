import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssValidationFoundationService } from "@/lib/services/gdss-validation-foundation.service";
import { uuidSchema } from "@/lib/validators/common";
import { validationVersionInputSchema } from "@/lib/validators/gdss-validation-foundation.schemas";
const service = new GdssValidationFoundationService();
export const POST = withRouteErrorHandling(
  async (
    request: Request,
    {
      params,
    }: { params: Promise<{ projectId: string; protocolIdentityId: string }> },
  ) => {
    const actor = await resolveAuthenticatedControlActor(request),
      p = await params,
      input = validationVersionInputSchema.parse(await request.json());
    return ok(
      await service.createProtocolDraft(
        actor,
        uuidSchema.parse(p.projectId),
        uuidSchema.parse(p.protocolIdentityId),
        input.content,
        input.predecessorVersionId,
      ),
      201,
    );
  },
);
