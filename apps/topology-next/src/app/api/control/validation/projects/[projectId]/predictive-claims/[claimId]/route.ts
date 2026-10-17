import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssCapabilityClaimsService } from "@/lib/services/gdss-capability-claims.service";
import { uuidSchema } from "@/lib/validators/common";
import { claimDraftUpdateInputSchema } from "@/lib/validators/gdss-capability-claims.schemas";
const service = new GdssCapabilityClaimsService();
const ids = async (params: Promise<{ projectId: string; claimId: string }>) => { const value = await params; return { projectId: uuidSchema.parse(value.projectId), claimId: uuidSchema.parse(value.claimId) }; };
export const GET = withRouteErrorHandling(async (request: Request, { params }: { params: Promise<{ projectId: string; claimId: string }> }) => {
  const actor = await resolveAuthenticatedControlActor(request), value = await ids(params);
  return ok(await service.getClaimCurrentness(actor, value.projectId, value.claimId));
});
export const PATCH = withRouteErrorHandling(async (request: Request, { params }: { params: Promise<{ projectId: string; claimId: string }> }) => {
  const actor = await resolveAuthenticatedControlActor(request), value = await ids(params);
  return ok(await service.updatePredictiveClaimDraft(actor, value.projectId, value.claimId, claimDraftUpdateInputSchema.parse(await request.json())));
});
