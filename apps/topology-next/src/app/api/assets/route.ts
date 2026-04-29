import { createAssetSchema } from "@/lib/validators/asset.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { AssetService } from "@/lib/services/asset.service";

const assetService = new AssetService();

export const POST = withRouteErrorHandling(async (request: Request) => {
  const payload = createAssetSchema.parse(await request.json());
  const created = await assetService.create(payload);
  return ok(created, 201);
});
