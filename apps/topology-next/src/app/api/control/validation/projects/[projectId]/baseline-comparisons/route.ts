import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssMetricsUncertaintyService } from "@/lib/services/gdss-metrics-uncertainty.service";
import { uuidSchema } from "@/lib/validators/common";
import { comparisonInput } from "@/lib/validators/gdss-metrics-uncertainty.schemas";
const s = new GdssMetricsUncertaintyService();
export const POST = withRouteErrorHandling(
  async (
    r: Request,
    { params }: { params: Promise<{ projectId: string }> },
  ) => {
    const a = await resolveAuthenticatedControlActor(r),
      p = uuidSchema.parse((await params).projectId),
      v = comparisonInput.parse(await r.json());
    return ok(
      await s.compareModelToBaseline(
        a,
        p,
        v.modelMetricResultId,
        v.baselineMetricResultId,
        v.rule,
        v.idempotencyKey,
      ),
      201,
    );
  },
);
