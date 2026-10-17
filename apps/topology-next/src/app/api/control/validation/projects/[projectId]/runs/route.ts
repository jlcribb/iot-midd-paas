import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssValidationRunService } from "@/lib/services/gdss-validation-run.service";
import { uuidSchema } from "@/lib/validators/common";
import { governedContentSchema } from "@/lib/validators/gdss-validation-run.schemas";
const service = new GdssValidationRunService();
export const POST = withRouteErrorHandling(
  async (
    r: Request,
    { params }: { params: Promise<{ projectId: string }> },
  ) => {
    const a = await resolveAuthenticatedControlActor(r),
      { projectId } = await params,
      v = governedContentSchema.parse(await r.json());
    return ok(
      await service.createValidationRun(
        a,
        uuidSchema.parse(projectId),
        v.content,
        v.idempotencyKey,
      ),
      201,
    );
  },
);
