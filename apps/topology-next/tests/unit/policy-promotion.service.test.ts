import { describe, expect, it, vi } from "vitest";
import { ForbiddenError } from "@/lib/errors/domain-errors";
import { PolicyPromotionService } from "@/lib/services/policy-promotion.service";

const projectId = "11111111-1111-4111-8111-111111111111";
const viewer = { actor_id: "viewer", user_id: "viewer", display_name: "Viewer", role: "viewer" as const, all_projects: false, project_ids: [projectId], project_roles: { [projectId]: "viewer" as const }, auth_source: "oauth_session" as const };
const editor = { ...viewer, actor_id: "editor", user_id: "editor", role: "operator" as const, project_roles: { [projectId]: "operator" as const } };

describe("PolicyPromotionService", () => {
  it("allows viewer reads and rejects viewer mutations while allowing edit_policies", async () => {
    const repo = { list: vi.fn().mockResolvedValue([]), get: vi.fn(), assessments: vi.fn(), assessment: vi.fn(), loadEvidence: vi.fn(), createOrGet: vi.fn(), assess: vi.fn() };
    const projects = { findById: vi.fn().mockResolvedValue({ id: projectId }) };
    const service = new PolicyPromotionService(repo as never, projects as never);
    await expect(service.list(viewer, projectId)).resolves.toEqual([]);
    await expect(service.create(viewer, projectId, "22222222-2222-4222-8222-222222222222")).rejects.toBeInstanceOf(ForbiddenError);
    await expect(service.assess(viewer, projectId, "33333333-3333-4333-8333-333333333333")).rejects.toBeInstanceOf(ForbiddenError);
    repo.loadEvidence.mockResolvedValue({ project_id: projectId }); repo.createOrGet.mockResolvedValue({ id: "proposal" });
    await expect(service.create(editor, projectId, "22222222-2222-4222-8222-222222222222")).resolves.toEqual({ id: "proposal" });
  });
});
