import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ControlledDeploymentPreparationService } from "@/lib/services/controlled-deployment-preparation.service";
import { uuidSchema } from "@/lib/validators/common";
const service = new ControlledDeploymentPreparationService();
export const GET = withRouteErrorHandling(async (request: Request, { params }: any) => { const actor = await resolveAuthenticatedControlActor(request), values = await params; return ok(await service.assessment(actor,uuidSchema.parse(values.projectId),uuidSchema.parse(values.candidateId),uuidSchema.parse(values.preparationId),uuidSchema.parse(values.assessmentId))); });
