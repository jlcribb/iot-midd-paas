import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssCapabilityClaimsService } from "@/lib/services/gdss-capability-claims.service";
import { uuidSchema } from "@/lib/validators/common";
const service = new GdssCapabilityClaimsService();
export const GET = withRouteErrorHandling(async (request: Request, { params }: { params: Promise<{ projectId: string; claimId: string }> }) => { const actor = await resolveAuthenticatedControlActor(request), p = await params; return ok(await service.auditPredictiveClaim(actor, uuidSchema.parse(p.projectId), uuidSchema.parse(p.claimId))); });
