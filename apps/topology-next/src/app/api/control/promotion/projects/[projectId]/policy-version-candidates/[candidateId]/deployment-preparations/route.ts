import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ControlledDeploymentPreparationService } from "@/lib/services/controlled-deployment-preparation.service";
import { uuidSchema } from "@/lib/validators/common";
import { createControlledDeploymentPreparationSchema } from "@/lib/validators/controlled-deployment-preparation.schemas";
const service = new ControlledDeploymentPreparationService();
export const GET = withRouteErrorHandling(async (request: Request, { params }: any) => { const actor = await resolveAuthenticatedControlActor(request), values = await params; return ok(await service.list(actor,uuidSchema.parse(values.projectId),uuidSchema.parse(values.candidateId))); });
export const POST = withRouteErrorHandling(async (request: Request, { params }: any) => { const actor = await resolveAuthenticatedControlActor(request), values = await params, input = createControlledDeploymentPreparationSchema.parse(await request.json()); return ok(await service.create(actor,uuidSchema.parse(values.projectId),uuidSchema.parse(values.candidateId),input.targetAssetId),201); });
