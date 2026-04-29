import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { SectorService } from "@/lib/services/sector.service";

const sectorService = new SectorService();

interface RouteParams {
  params: {
    projectId: string;
  };
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const sectors = await sectorService.listByProject(params.projectId);
  return ok(sectors);
});
