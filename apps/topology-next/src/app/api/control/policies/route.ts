import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { ValidationError } from "@/lib/errors/domain-errors";
import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ControlPolicyService } from "@/lib/services/control-policy.service";
import { createControlPolicySchema } from "@/lib/validators/control-policy.schemas";

const controlPolicyService = new ControlPolicyService();

function parseEnabledParam(value: string | null): boolean | undefined {
  if (value === null) {
    return undefined;
  }
  if (value === "true") {
    return true;
  }
  if (value === "false") {
    return false;
  }
  throw new ValidationError("enabled must be true or false");
}

export const GET = withRouteErrorHandling(async (request: Request) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const { searchParams } = new URL(request.url);
  const projectId = searchParams.get("projectId") ?? undefined;
  const variable = searchParams.get("variable")?.trim() || undefined;
  const enabled = parseEnabledParam(searchParams.get("enabled"));

  const policies = await controlPolicyService.list(actor, {
    projectId,
    variable,
    enabled
  });

  return ok(policies);
});

export const POST = withRouteErrorHandling(async (request: Request) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const payload = createControlPolicySchema.parse(await request.json());
  const created = await controlPolicyService.create(actor, payload);
  return ok(created, 201);
});
