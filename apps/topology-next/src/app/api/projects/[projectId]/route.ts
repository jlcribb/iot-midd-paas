import { updateProjectSchema } from "@/lib/validators/project.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { ProjectService } from "@/lib/services/project.service";

const projectService = new ProjectService();

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
  const updated = await projectService.update(projectId, payload);
  return ok(updated);
});
