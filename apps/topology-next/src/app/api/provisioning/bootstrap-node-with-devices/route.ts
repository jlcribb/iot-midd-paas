import { bootstrapNodeWithDevicesSchema } from "@/lib/validators/topology.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { ProvisioningService } from "@/lib/services/provisioning.service";

const provisioningService = new ProvisioningService();

export const POST = withRouteErrorHandling(async (request: Request) => {
  const payload = bootstrapNodeWithDevicesSchema.parse(await request.json());
  const result = await provisioningService.bootstrapNodeWithDevices(payload);
  return ok(result, 201);
});
