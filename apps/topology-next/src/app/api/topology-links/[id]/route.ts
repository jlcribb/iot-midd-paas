import { updateTopologyLinkSchema } from "@/lib/validators/topology.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { TopologyService } from "@/lib/services/topology.service";

const topologyService = new TopologyService();

interface RouteParams {
  params: Promise<{
    id: string;
  }>;
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const { id } = await params;
  const topology = await topologyService.getById(id);
  return ok(topology);
});

export const PATCH = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const { id } = await params;
  const payload = updateTopologyLinkSchema.parse(await request.json());
  const updated = await topologyService.update(id, payload);
  return ok(updated);
});

export const DELETE = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const { id } = await params;
  await topologyService.delete(id);
  return ok({ deleted: true });
});
