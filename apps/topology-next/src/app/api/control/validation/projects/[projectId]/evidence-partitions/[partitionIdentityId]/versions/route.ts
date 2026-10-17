import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { GdssEvidenceCustodyService } from "@/lib/services/gdss-evidence-custody.service";
import { uuidSchema } from "@/lib/validators/common";
import { partitionDraftSchema } from "@/lib/validators/gdss-evidence-custody.schemas";
const service = new GdssEvidenceCustodyService();
export const POST = withRouteErrorHandling(
  async (
    r: Request,
    {
      params,
    }: { params: Promise<{ projectId: string; partitionIdentityId: string }> },
  ) => {
    const a = await resolveAuthenticatedControlActor(r),
      p = await params,
      v = partitionDraftSchema.parse(await r.json());
    return ok(
      await service.createPartitionPlanDraft(
        a,
        uuidSchema.parse(p.projectId),
        uuidSchema.parse(p.partitionIdentityId),
        v.content,
        v.predecessorVersionId,
      ),
      201,
    );
  },
);
