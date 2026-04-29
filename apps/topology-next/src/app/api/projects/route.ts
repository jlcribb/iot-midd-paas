import { createProjectSchema } from "@/lib/validators/project.schemas";
import { withRouteErrorHandling } from "@/lib/http/route-handler";
import { ok } from "@/lib/http/response";
import { ProjectService } from "@/lib/services/project.service";
import { ValidationError } from "@/lib/errors/domain-errors";

const projectService = new ProjectService();

export const POST = withRouteErrorHandling(async (request: Request) => {
  const payload = createProjectSchema.parse(await request.json());
  const created = await projectService.create(payload);
  return ok(created, 201);
});

export const GET = withRouteErrorHandling(async (request: Request) => {
  const { searchParams } = new URL(request.url);
  const statusParam = searchParams.get("status");
  const allowedStatuses = ["draft", "active", "inactive", "archived"] as const;
  if (statusParam && !allowedStatuses.includes(statusParam as (typeof allowedStatuses)[number])) {
    throw new ValidationError("Invalid status query parameter");
  }
  const status = statusParam
    ? (statusParam as "draft" | "active" | "inactive" | "archived")
    : undefined;
  const projects = await projectService.list(status);
  return ok(projects);
});
