import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssPredictiveEvidenceService } from "@/lib/services/gdss-predictive-evidence.service";
import { uuidSchema } from "@/lib/validators/common";
import { evidenceSetInputSchema } from "@/lib/validators/gdss-predictive-evidence.schemas";
const service = new GdssPredictiveEvidenceService();
export const POST = withRouteErrorHandling(
  async (
    request: Request,
    { params }: { params: Promise<{ projectId: string }> },
  ) => {
    const actor = await resolveAuthenticatedControlActor(request),
      projectId = uuidSchema.parse((await params).projectId);
    return ok(
      await service.materializePredictiveEvidenceSet(
        actor,
        projectId,
        evidenceSetInputSchema.parse(await request.json()),
      ),
      201,
    );
  },
);
