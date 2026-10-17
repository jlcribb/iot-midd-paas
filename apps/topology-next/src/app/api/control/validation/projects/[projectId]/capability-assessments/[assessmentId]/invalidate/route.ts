import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssCapabilityClaimsService } from "@/lib/services/gdss-capability-claims.service";
import { uuidSchema } from "@/lib/validators/common";
import { capabilityInvalidationInputSchema } from "@/lib/validators/gdss-capability-claims.schemas";
const service = new GdssCapabilityClaimsService();
export const POST = withRouteErrorHandling(async (request: Request, { params }: { params: Promise<{ projectId: string; assessmentId: string }> }) => {
  const actor = await resolveAuthenticatedControlActor(request), values = await params, assessmentId = uuidSchema.parse(values.assessmentId);
  const body = capabilityInvalidationInputSchema.omit({ assessmentId: true }).parse(await request.json());
  return ok(await service.invalidatePredictiveCapability(actor, uuidSchema.parse(values.projectId), { ...body, assessmentId }), 201);
});
