import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { TopologyService } from "@/lib/services/topology.service";

const topologyService = new TopologyService();

interface RouteParams {
  params: {
    projectId: string;
  };
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const topology = await topologyService.getProjectTopology(params.projectId);
  return ok(topology);
});
