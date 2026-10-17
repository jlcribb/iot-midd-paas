import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssMetricsUncertaintyService } from "@/lib/services/gdss-metrics-uncertainty.service";
import { uuidSchema } from "@/lib/validators/common";
import { baselineGenerationInput } from "@/lib/validators/gdss-metrics-uncertainty.schemas";
const s = new GdssMetricsUncertaintyService();
export const POST = withRouteErrorHandling(
  async (
    r: Request,
    { params }: { params: Promise<{ projectId: string; versionId: string }> },
  ) => {
    const a = await resolveAuthenticatedControlActor(r),
      p = await params,
      v = baselineGenerationInput.parse(await r.json());
    return ok(
      await s.generateBaselinePredictions(
        a,
        uuidSchema.parse(p.projectId),
        uuidSchema.parse(p.versionId),
        v.pairSetId,
      ),
      201,
    );
  },
);
