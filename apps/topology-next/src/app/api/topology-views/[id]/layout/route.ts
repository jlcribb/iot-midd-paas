import { saveTopologyViewLayoutSchema } from "@/lib/validators/topology-view.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { TopologyViewService } from "@/lib/services/topology-view.service";

const topologyViewService = new TopologyViewService();

interface RouteParams {
  params: {
    id: string;
  };
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const layout = await topologyViewService.getLayout(params.id);
  return ok(layout);
});

export const PUT = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const payload = saveTopologyViewLayoutSchema.parse(await request.json());
  const saved = await topologyViewService.saveLayout(params.id, payload);
  return ok(saved);
});
