import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssPredictiveEvidenceService } from "@/lib/services/gdss-predictive-evidence.service";
import { uuidSchema } from "@/lib/validators/common";
const service = new GdssPredictiveEvidenceService();
export const POST = withRouteErrorHandling(
  async (
    request: Request,
    {
      params,
    }: { params: Promise<{ projectId: string; evidenceSetId: string }> },
  ) => {
    const actor = await resolveAuthenticatedControlActor(request),
      values = await params;
    return ok(
      await service.deriveEvidenceStrengthProfile(
        actor,
        uuidSchema.parse(values.projectId),
        uuidSchema.parse(values.evidenceSetId),
      ),
      201,
    );
  },
);
