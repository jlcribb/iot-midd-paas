import { createTopologyViewSchema } from "@/lib/validators/topology-view.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { TopologyViewService } from "@/lib/services/topology-view.service";
import { ValidationError } from "@/lib/errors/domain-errors";

const topologyViewService = new TopologyViewService();

interface RouteParams {
  params: {
    projectId: string;
  };
}

export const GET = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const { searchParams } = new URL(request.url);
  const viewTypeParam = searchParams.get("view_type");

  if (viewTypeParam && !["logical", "physical", "geographic"].includes(viewTypeParam)) {
    throw new ValidationError("Invalid view_type query parameter");
  }

  const views = await topologyViewService.listByProject(
    params.projectId,
    (viewTypeParam as "logical" | "physical" | "geographic" | null) ?? undefined
  );
  return ok(views);
});

export const POST = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const payload = createTopologyViewSchema.parse(await request.json());
  const created = await topologyViewService.create(params.projectId, payload);
  return ok(created, 201);
});
