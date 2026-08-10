import { updateProjectSchema } from "@/lib/validators/project.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { ProjectService } from "@/lib/services/project.service";
import { ProjectControlGovernanceService } from "@/lib/services/project-control-governance.service";
import { resolveAuthenticatedControlActor } from "@/lib/auth/control-auth-session";

const projectService = new ProjectService();
const projectControlGovernanceService = new ProjectControlGovernanceService();

interface RouteParams {
  params: Promise<{
    projectId: string;
  }>;
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const { projectId } = await params;
  const project = await projectService.getById(projectId);
  return ok(project);
});

export const PATCH = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const { projectId } = await params;
  const payload = updateProjectSchema.parse(await request.json());
  if (payload.parametric_control_enabled !== undefined) {
    const actor = await resolveAuthenticatedControlActor(request);
    const updated = await projectControlGovernanceService.updateProjectWithParametricControl(
      actor,
      projectId,
      payload,
      request.headers.get("x-request-id")
    );
    return ok(updated);
  }
  const updated = await projectService.update(projectId, payload);
  return ok(updated);
});
