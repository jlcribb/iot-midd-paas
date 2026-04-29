import { createSectorSchema } from "@/lib/validators/sector.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { SectorService } from "@/lib/services/sector.service";

const sectorService = new SectorService();

export const POST = withRouteErrorHandling(async (request: Request) => {
  const payload = createSectorSchema.parse(await request.json());
  const created = await sectorService.create(payload);
  return ok(created, 201);
});
