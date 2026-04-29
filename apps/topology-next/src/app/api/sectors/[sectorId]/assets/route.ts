import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { AssetService } from "@/lib/services/asset.service";

const assetService = new AssetService();

interface RouteParams {
  params: {
    sectorId: string;
  };
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const assets = await assetService.listBySector(params.sectorId);
  return ok(assets);
});
