import { updateTopologyViewSchema } from "@/lib/validators/topology-view.schemas";
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
  const view = await topologyViewService.getById(params.id);
  return ok(view);
});

export const PATCH = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const payload = updateTopologyViewSchema.parse(await request.json());
  const updated = await topologyViewService.update(params.id, payload);
  return ok(updated);
});
