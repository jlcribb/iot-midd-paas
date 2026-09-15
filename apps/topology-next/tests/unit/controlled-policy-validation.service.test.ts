import { describe, expect, it, vi } from "vitest";
import { ForbiddenError, NotFoundError } from "@/lib/errors/domain-errors";
import { ControlledPolicyValidationService } from "@/lib/services/controlled-policy-validation.service";

const projectId = "11111111-1111-4111-8111-111111111111";
const candidateId = "22222222-2222-4222-8222-222222222222";
const validationId = "33333333-3333-4333-8333-333333333333";
const viewer = { actor_id: "viewer", user_id: "viewer", display_name: "Viewer", role: "viewer" as const, all_projects: false, project_ids: [projectId], project_roles: { [projectId]: "viewer" as const }, auth_source: "oauth_session" as const };
const editor = { ...viewer, actor_id: "editor", user_id: "editor", role: "operator" as const, project_roles: { [projectId]: "operator" as const } };

describe("ControlledPolicyValidationService", () => {
  it("allows scoped reads, protects writes, and returns 404 for absent evidence", async () => {
    const repo = { list: vi.fn().mockResolvedValue([]), get: vi.fn().mockResolvedValue(null), createOrGet: vi.fn().mockResolvedValue({ id: validationId }), approve: vi.fn().mockResolvedValue({ id: "approval" }), approval: vi.fn().mockResolvedValue(null) };
    const projects = { findById: vi.fn().mockResolvedValue({ id: projectId }) };
    const service = new ControlledPolicyValidationService(repo as never, projects as never);
    await expect(service.list(viewer, projectId, candidateId)).resolves.toEqual([]);
    await expect(service.create(viewer, projectId, candidateId)).rejects.toBeInstanceOf(ForbiddenError);
    await expect(service.create(editor, projectId, candidateId)).resolves.toEqual({ id: validationId });
    await expect(service.get(viewer, projectId, candidateId, validationId)).rejects.toBeInstanceOf(NotFoundError);
    await expect(service.approve(viewer, projectId, candidateId, validationId, "REJECT", "Evidence requires a documented rejection.")).rejects.toBeInstanceOf(ForbiddenError);
  });
});
