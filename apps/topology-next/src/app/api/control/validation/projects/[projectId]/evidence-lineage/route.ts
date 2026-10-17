import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssEvidenceCustodyService } from "@/lib/services/gdss-evidence-custody.service";
import { uuidSchema } from "@/lib/validators/common";
const service = new GdssEvidenceCustodyService();
export const POST = withRouteErrorHandling(
  async (
    r: Request,
    { params }: { params: Promise<{ projectId: string }> },
  ) => {
    const a = await resolveAuthenticatedControlActor(r),
      { projectId } = await params;
    return ok(
      await service.linkEvidenceLineage(
        a,
        uuidSchema.parse(projectId),
        await r.json(),
      ),
      201,
    );
  },
);
