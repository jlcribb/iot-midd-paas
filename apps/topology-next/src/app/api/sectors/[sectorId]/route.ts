import { updateSectorSchema } from "@/lib/validators/sector.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { SectorService } from "@/lib/services/sector.service";

const sectorService = new SectorService();

interface RouteParams {
  params: {
    sectorId: string;
  };
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const sector = await sectorService.getById(params.sectorId);
  return ok(sector);
});

export const PATCH = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const payload = updateSectorSchema.parse(await request.json());
  const updated = await sectorService.update(params.sectorId, payload);
  return ok(updated);
});

export const DELETE = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const deleted = await sectorService.softDelete(params.sectorId);
  return ok(deleted);
});
