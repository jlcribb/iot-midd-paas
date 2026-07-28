import { updateLocationSchema } from "@/lib/validators/location.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { LocationService } from "@/lib/services/location.service";

const locationService = new LocationService();

interface RouteParams {
  params: Promise<{
    id: string;
  }>;
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const { id } = await params;
  const location = await locationService.getById(id);
  return ok(location);
});

export const PATCH = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const { id } = await params;
  const payload = updateLocationSchema.parse(await request.json());
  const updated = await locationService.update(id, payload);
  return ok(updated);
});
