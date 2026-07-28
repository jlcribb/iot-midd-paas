import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { TopologyService } from "@/lib/services/topology.service";

const topologyService = new TopologyService();

interface RouteParams {
  params: Promise<{
    projectId: string;
  }>;
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const { projectId } = await params;
  const topology = await topologyService.getProjectTopology(projectId);
  return ok(topology);
});
