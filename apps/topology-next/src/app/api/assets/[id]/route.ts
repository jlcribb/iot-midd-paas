import { updateAssetSchema } from "@/lib/validators/asset.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { AssetService } from "@/lib/services/asset.service";

const assetService = new AssetService();

interface RouteParams {
  params: {
    id: string;
  };
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const asset = await assetService.getById(params.id);
  return ok(asset);
});

export const PATCH = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const payload = updateAssetSchema.parse(await request.json());
  const updated = await assetService.update(params.id, payload);
  return ok(updated);
});

export const DELETE = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const deleted = await assetService.deleteSafe(params.id);
  return ok(deleted);
});
