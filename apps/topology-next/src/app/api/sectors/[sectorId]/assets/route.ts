import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { AssetService } from "@/lib/services/asset.service";

const assetService = new AssetService();

interface RouteParams {
  params: Promise<{
    sectorId: string;
  }>;
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const { sectorId } = await params;
  const assets = await assetService.listBySector(sectorId);
  return ok(assets);
});
