import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssValidationRunService } from "@/lib/services/gdss-validation-run.service";
import { uuidSchema } from "@/lib/validators/common";
import { pairCreateSchema } from "@/lib/validators/gdss-validation-run.schemas";
const service = new GdssValidationRunService();
export const POST = withRouteErrorHandling(
  async (
    r: Request,
    {
      params,
    }: { params: Promise<{ projectId: string; predictionId: string }> },
  ) => {
    const a = await resolveAuthenticatedControlActor(r),
      p = await params,
      v = pairCreateSchema.parse(await r.json());
    return ok(
      await service.pairPredictionWithObservation(
        a,
        uuidSchema.parse(p.projectId),
        uuidSchema.parse(p.predictionId),
        v.observationReferenceId,
        v.contract,
        v.idempotencyKey,
      ),
      201,
    );
  },
);
