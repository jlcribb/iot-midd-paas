import { createTopologyLinkSchema } from "@/lib/validators/topology.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { TopologyService } from "@/lib/services/topology.service";

const topologyService = new TopologyService();

export const POST = withRouteErrorHandling(async (request: Request) => {
  const payload = createTopologyLinkSchema.parse(await request.json());
  const created = await topologyService.create(payload);
  return ok(created, 201);
});
