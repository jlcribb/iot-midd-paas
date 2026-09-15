import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GovernedDeploymentExecutionService } from "@/lib/services/governed-deployment-execution.service";
import { uuidSchema } from "@/lib/validators/common";

const service = new GovernedDeploymentExecutionService();

export const GET = withRouteErrorHandling(async (request: Request, { params }: any) => {
  const actor = await resolveAuthenticatedControlActor(request), values = await params;
  return ok(await service.get(actor, uuidSchema.parse(values.projectId), uuidSchema.parse(values.candidateId), uuidSchema.parse(values.intentId), uuidSchema.parse(values.executionId)));
});
