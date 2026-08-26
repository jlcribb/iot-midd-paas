import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";
import { ok } from "@/lib/http/response";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { EvaluationProfileService } from "@/lib/services/evaluation-profile.service";
import { uuidSchema } from "@/lib/validators/common";
import { createEvaluationProfileSchema } from "@/lib/validators/evaluation-profile.schemas";

const service = new EvaluationProfileService();
interface RouteParams { params: Promise<{ projectId: string }>; }

export const GET = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const { projectId: rawProjectId } = await params;
  return ok(await service.listProfiles(actor, uuidSchema.parse(rawProjectId)));
});

export const POST = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const actor = await resolveAuthenticatedControlActor(request);
  const { projectId: rawProjectId } = await params;
  const profile = await service.createProfile(actor, uuidSchema.parse(rawProjectId), createEvaluationProfileSchema.parse(await request.json()));
  return ok(profile, 201);
});
