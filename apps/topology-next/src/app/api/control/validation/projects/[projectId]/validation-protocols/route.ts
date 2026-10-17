import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssValidationFoundationService } from "@/lib/services/gdss-validation-foundation.service";
import { uuidSchema } from "@/lib/validators/common";
import { validationIdentityInputSchema } from "@/lib/validators/gdss-validation-foundation.schemas";
const service = new GdssValidationFoundationService();
export const POST = withRouteErrorHandling(
  async (
    request: Request,
    { params }: { params: Promise<{ projectId: string }> },
  ) => {
    const actor = await resolveAuthenticatedControlActor(request),
      { projectId } = await params,
      input = validationIdentityInputSchema.parse(await request.json());
    return ok(
      await service.createProtocolIdentity(
        actor,
        uuidSchema.parse(projectId),
        input.logicalKey,
      ),
      201,
    );
  },
);
