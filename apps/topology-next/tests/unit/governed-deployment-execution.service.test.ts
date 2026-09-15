import { afterEach, describe, expect, it, vi } from "vitest";
import { ForbiddenError } from "@/lib/errors/domain-errors";
import { GovernedDeploymentExecutionService } from "@/lib/services/governed-deployment-execution.service";

const projectId = "11111111-1111-4111-8111-111111111111", candidateId = "22222222-2222-4222-8222-222222222222", intentId = "33333333-3333-4333-8333-333333333333";
const viewer = { actor_id: "viewer", user_id: "viewer", display_name: "Viewer", role: "viewer" as const, all_projects: false, project_ids: [projectId], project_roles: { [projectId]: "viewer" as const }, auth_source: "oauth_session" as const };
const editor = { ...viewer, actor_id: "oauth-executor", user_id: "oauth-executor", role: "operator" as const, project_roles: { [projectId]: "operator" as const } };

afterEach(() => { delete process.env.CONTROL_RBAC_ALLOW_DEV_FALLBACK; });

describe("GovernedDeploymentExecutionService", () => {
  it("uses session actor, edit permission, and rejects development fallback", async () => {
    const repo = { execute: vi.fn().mockResolvedValue({ id: "execution" }), list: vi.fn(), get: vi.fn() };
    const projects = { findById: vi.fn().mockResolvedValue({ id: projectId }) };
    const service = new GovernedDeploymentExecutionService(repo as never, projects as never);
    await expect(service.execute(viewer, projectId, candidateId, intentId)).rejects.toBeInstanceOf(ForbiddenError);
    await service.execute(editor, projectId, candidateId, intentId);
    expect(repo.execute).toHaveBeenCalledWith(projectId, candidateId, intentId, "oauth-executor");
    process.env.CONTROL_RBAC_ALLOW_DEV_FALLBACK = "true";
    await expect(service.execute(editor, projectId, candidateId, intentId)).rejects.toBeInstanceOf(ForbiddenError);
  });
});
