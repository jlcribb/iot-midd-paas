import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { ControlPolicyService } from "@/lib/services/control-policy.service";
import { updateControlPolicySchema } from "@/lib/validators/control-policy.schemas";

const controlPolicyService = new ControlPolicyService();

interface RouteParams {
  params: {
    id: string;
  };
}

export const PATCH = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const payload = updateControlPolicySchema.parse(await request.json());
  const updated = await controlPolicyService.update(params.id, payload);
  return ok(updated);
});

export const DELETE = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const disabled = await controlPolicyService.disable(params.id);
  return ok(disabled);
});
