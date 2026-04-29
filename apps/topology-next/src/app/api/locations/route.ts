import { createLocationSchema } from "@/lib/validators/location.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { LocationService } from "@/lib/services/location.service";

const locationService = new LocationService();

export const POST = withRouteErrorHandling(async (request: Request) => {
  const payload = createLocationSchema.parse(await request.json());
  const created = await locationService.create(payload);
  return ok(created, 201);
});

export const GET = withRouteErrorHandling(async (_request: Request) => {
  const locations = await locationService.list();
  return ok(locations);
});
