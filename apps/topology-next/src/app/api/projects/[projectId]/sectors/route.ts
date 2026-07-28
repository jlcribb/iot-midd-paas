import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { SectorService } from "@/lib/services/sector.service";

const sectorService = new SectorService();

interface RouteParams {
  params: Promise<{
    projectId: string;
  }>;
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const { projectId } = await params;
  const sectors = await sectorService.listByProject(projectId);
  return ok(sectors);
});
