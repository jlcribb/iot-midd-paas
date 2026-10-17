import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssMetricsUncertaintyService } from "@/lib/services/gdss-metrics-uncertainty.service";
import { uuidSchema } from "@/lib/validators/common";
import { versionInput } from "@/lib/validators/gdss-metrics-uncertainty.schemas";
const s = new GdssMetricsUncertaintyService();
export const POST = withRouteErrorHandling(
  async (
    r: Request,
    { params }: { params: Promise<{ projectId: string; identityId: string }> },
  ) => {
    const a = await resolveAuthenticatedControlActor(r),
      p = await params,
      v = versionInput.parse(await r.json());
    return ok(
      await s.createMetricDefinitionVersion(
        a,
        uuidSchema.parse(p.projectId),
        uuidSchema.parse(p.identityId),
        v.content,
      ),
      201,
    );
  },
);
