import { updateAssetSchema } from "@/lib/validators/asset.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { AssetService } from "@/lib/services/asset.service";

const assetService = new AssetService();

interface RouteParams {
  params: Promise<{
    id: string;
  }>;
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const { id } = await params;
  const asset = await assetService.getById(id);
  return ok(asset);
});

export const PATCH = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const { id } = await params;
  const payload = updateAssetSchema.parse(await request.json());
  const updated = await assetService.update(id, payload);
  return ok(updated);
});

export const DELETE = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const { id } = await params;
  const deleted = await assetService.deleteSafe(id);
  return ok(deleted);
});
