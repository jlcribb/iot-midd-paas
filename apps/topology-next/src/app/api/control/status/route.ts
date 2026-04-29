import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { ControlObservabilityService } from "@/lib/services/control-observability.service";

const controlObservabilityService = new ControlObservabilityService();

export const GET = withRouteErrorHandling(async () => {
  const status = await controlObservabilityService.getStatus();
  return ok(status);
});
