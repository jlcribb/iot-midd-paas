import { updateSectorSchema } from "@/lib/validators/sector.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { SectorService } from "@/lib/services/sector.service";

const sectorService = new SectorService();

interface RouteParams {
  params: Promise<{
    sectorId: string;
  }>;
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const { sectorId } = await params;
  const sector = await sectorService.getById(sectorId);
  return ok(sector);
});

export const PATCH = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const { sectorId } = await params;
  const payload = updateSectorSchema.parse(await request.json());
  const updated = await sectorService.update(sectorId, payload);
  return ok(updated);
});

export const DELETE = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const { sectorId } = await params;
  const deleted = await sectorService.softDelete(sectorId);
  return ok(deleted);
});
