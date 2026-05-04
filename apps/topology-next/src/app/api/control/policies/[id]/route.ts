import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ControlPolicyService } from "@/lib/services/control-policy.service";
import { updateControlPolicySchema } from "@/lib/validators/control-policy.schemas";

const controlPolicyService = new ControlPolicyService();

interface RouteParams {
  params: {
    id: string;
  };
}

export const PATCH = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const payload = updateControlPolicySchema.parse(await request.json());
  const updated = await controlPolicyService.update(actor, params.id, payload);
  return ok(updated);
});

export const DELETE = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const disabled = await controlPolicyService.disable(actor, params.id);
  return ok(disabled);
});
