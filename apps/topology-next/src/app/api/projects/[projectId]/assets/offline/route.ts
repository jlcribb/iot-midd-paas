import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { ValidationError } from "@/lib/errors/domain-errors";
import { AssetService } from "@/lib/services/asset.service";

const assetService = new AssetService();

interface RouteParams {
  params: {
    projectId: string;
  };
}

export const GET = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const { searchParams } = new URL(request.url);
  const minutesParam = searchParams.get("minutes");
  let minutes = 15;
  if (minutesParam !== null) {
    const parsed = Number(minutesParam);
    if (!Number.isFinite(parsed) || parsed <= 0 || !Number.isInteger(parsed)) {
      throw new ValidationError("minutes must be a positive integer");
    }
    minutes = parsed;
  }
  const assets = await assetService.getOfflineAssets(params.projectId, minutes);
  return ok(assets);
});
