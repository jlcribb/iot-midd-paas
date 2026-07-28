import { saveTopologyViewLayoutSchema } from "@/lib/validators/topology-view.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { TopologyViewService } from "@/lib/services/topology-view.service";

const topologyViewService = new TopologyViewService();

interface RouteParams {
  params: Promise<{
    id: string;
  }>;
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const { id } = await params;
  const layout = await topologyViewService.getLayout(id);
  return ok(layout);
});

export const PUT = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const { id } = await params;
  const payload = saveTopologyViewLayoutSchema.parse(await request.json());
  const saved = await topologyViewService.saveLayout(id, payload);
  return ok(saved);
});
