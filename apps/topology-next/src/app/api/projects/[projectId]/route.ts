import { updateProjectSchema } from "@/lib/validators/project.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { ProjectService } from "@/lib/services/project.service";

const projectService = new ProjectService();

interface RouteParams {
  params: {
    projectId: string;
  };
}

export const GET = withRouteErrorHandling(async (_request: Request, { params }: RouteParams) => {
  const project = await projectService.getById(params.projectId);
  return ok(project);
});

export const PATCH = withRouteErrorHandling(async (request: Request, { params }: RouteParams) => {
  const payload = updateProjectSchema.parse(await request.json());
  const updated = await projectService.update(params.projectId, payload);
  return ok(updated);
});
