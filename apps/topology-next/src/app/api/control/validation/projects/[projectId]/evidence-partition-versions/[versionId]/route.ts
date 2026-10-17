import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssEvidenceCustodyService } from "@/lib/services/gdss-evidence-custody.service";
import { uuidSchema } from "@/lib/validators/common";
import { contentSchema } from "@/lib/validators/gdss-evidence-custody.schemas";
const service = new GdssEvidenceCustodyService();
export const PATCH = withRouteErrorHandling(
  async (
    r: Request,
    { params }: { params: Promise<{ projectId: string; versionId: string }> },
  ) => {
    const a = await resolveAuthenticatedControlActor(r),
      p = await params,
      v = contentSchema.parse(await r.json());
    return ok(
      await service.updatePartitionPlanDraft(
        a,
        uuidSchema.parse(p.projectId),
        uuidSchema.parse(p.versionId),
        v.content,
      ),
    );
  },
);
