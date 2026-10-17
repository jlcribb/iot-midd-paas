import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssCapabilityClaimsService } from "@/lib/services/gdss-capability-claims.service";
import { uuidSchema } from "@/lib/validators/common";
import { claimIdentityInputSchema } from "@/lib/validators/gdss-capability-claims.schemas";
const service = new GdssCapabilityClaimsService();
export const POST = withRouteErrorHandling(async (request: Request, { params }: { params: Promise<{ projectId: string }> }) => {
  const actor = await resolveAuthenticatedControlActor(request), projectId = uuidSchema.parse((await params).projectId);
  return ok(await service.createPredictiveClaimIdentity(actor, projectId, claimIdentityInputSchema.parse(await request.json())), 201);
});
