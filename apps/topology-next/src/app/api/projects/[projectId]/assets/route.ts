import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { AssetService } from "@/lib/services/asset.service";

const assetService = new AssetService();

interface RouteParams {
  params: {
    projectId: string;
  };
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const assets = await assetService.listByProject(params.projectId);
  return ok(assets);
});
