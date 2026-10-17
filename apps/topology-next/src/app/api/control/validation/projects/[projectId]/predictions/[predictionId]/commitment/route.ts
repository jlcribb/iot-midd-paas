import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssValidationRunService } from "@/lib/services/gdss-validation-run.service";
import { uuidSchema } from "@/lib/validators/common";
import { z } from "zod";
const service = new GdssValidationRunService(),
  schema = z
    .object({ idempotencyKey: z.string().trim().min(1).max(256) })
    .strict();
export const POST = withRouteErrorHandling(
  async (
    r: Request,
    {
      params,
    }: { params: Promise<{ projectId: string; predictionId: string }> },
  ) => {
    const a = await resolveAuthenticatedControlActor(r),
      p = await params,
      v = schema.parse(await r.json());
    return ok(
      await service.commitPrediction(
        a,
        uuidSchema.parse(p.projectId),
        uuidSchema.parse(p.predictionId),
        v.idempotencyKey,
      ),
      201,
    );
  },
);
