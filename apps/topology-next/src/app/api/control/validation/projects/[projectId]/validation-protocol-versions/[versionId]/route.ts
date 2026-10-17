import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssValidationFoundationService } from "@/lib/services/gdss-validation-foundation.service";
import { uuidSchema } from "@/lib/validators/common";
import { validationDraftUpdateSchema } from "@/lib/validators/gdss-validation-foundation.schemas";
const service = new GdssValidationFoundationService();
type P = { params: Promise<{ projectId: string; versionId: string }> };
export const GET = withRouteErrorHandling(
  async (request: Request, { params }: P) => {
    const actor = await resolveAuthenticatedControlActor(request),
      p = await params;
    return ok(
      await service.readProtocol(
        actor,
        uuidSchema.parse(p.projectId),
        uuidSchema.parse(p.versionId),
      ),
    );
  },
);
export const PATCH = withRouteErrorHandling(
  async (request: Request, { params }: P) => {
    const actor = await resolveAuthenticatedControlActor(request),
      p = await params,
      input = validationDraftUpdateSchema.parse(await request.json());
    return ok(
      await service.updateProtocolDraft(
        actor,
        uuidSchema.parse(p.projectId),
        uuidSchema.parse(p.versionId),
        input.content,
      ),
    );
  },
);
