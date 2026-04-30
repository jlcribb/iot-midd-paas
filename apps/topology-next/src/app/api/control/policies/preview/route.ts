import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { ControlPolicyService } from "@/lib/services/control-policy.service";
import { previewControlPolicySchema } from "@/lib/validators/control-policy.schemas";

const controlPolicyService = new ControlPolicyService();

export const POST = withRouteErrorHandling(async (request: Request) => {
  const payload = previewControlPolicySchema.parse(await request.json());
  const preview = await controlPolicyService.previewSelection({
    projectId: payload.project_id,
    variable: payload.variable,
    context: payload.context,
    candidatePolicy: payload.candidate_policy
  });

  return ok(preview);
});
