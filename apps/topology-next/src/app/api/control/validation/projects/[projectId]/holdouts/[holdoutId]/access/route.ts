import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssEvidenceCustodyService } from "@/lib/services/gdss-evidence-custody.service";
import { uuidSchema } from "@/lib/validators/common";
const service = new GdssEvidenceCustodyService();
export const POST = withRouteErrorHandling(
  async (
    r: Request,
    { params }: { params: Promise<{ projectId: string; holdoutId: string }> },
  ) => {
    const a = await resolveAuthenticatedControlActor(r),
      p = await params;
    return ok(
      await service.recordHoldoutAccess(
        a,
        uuidSchema.parse(p.projectId),
        uuidSchema.parse(p.holdoutId),
        await r.json(),
      ),
      201,
    );
  },
);
export const GET = withRouteErrorHandling(
  async (
    r: Request,
    { params }: { params: Promise<{ projectId: string; holdoutId: string }> },
  ) => {
    const a = await resolveAuthenticatedControlActor(r),
      p = await params;
    return ok(
      await service.assessHoldoutIndependence(
        a,
        uuidSchema.parse(p.projectId),
        uuidSchema.parse(p.holdoutId),
      ),
    );
  },
);
