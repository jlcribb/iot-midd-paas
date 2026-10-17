import { describe, expect, it, vi } from "vitest";
import type { ControlActor } from "@/lib/dto/control-access.dto";

const projectId = "11111111-1111-4111-8111-111111111111";
const resourceId = "22222222-2222-4222-8222-222222222222";
const hash = "a".repeat(64);
const aiAdmin: ControlActor = {
  user_id: "ai:admin",
  actor_id: "ai:admin",
  display_name: "AI admin",
  auth_provider: "ai",
  auth_source: "oauth_session",
  role: "admin",
  project_ids: [projectId],
  project_roles: { [projectId]: "admin" },
  all_projects: false,
};
vi.mock("@/lib/auth/control-auth-session", () => ({
  resolveAuthenticatedControlActor: vi.fn(async () => aiAdmin),
}));

describe("P024-R3 AI authority API boundary", () => {
  it("returns stable 403 denial for AI holdout opening without repository execution", async () => {
    const route = await import("@/app/api/control/validation/projects/[projectId]/holdouts/[holdoutId]/[action]/route");
    const response = await route.POST(
      new Request("http://localhost", { method: "POST", body: JSON.stringify({ evaluationReference: "evaluation-1", reason: "verify", idempotencyKey: "ai-open" }) }),
      { params: Promise.resolve({ projectId, holdoutId: resourceId, action: "open" }) },
    );
    expect(response.status).toBe(403);
    expect(await response.json()).toMatchObject({ success: false, error: { code: "AI_AUTHORITY_FORBIDDEN" } });
  });

  it("returns stable 403 denial for AI evidence assembly before materialization", async () => {
    const route = await import("@/app/api/control/validation/projects/[projectId]/predictive-evidence-sets/route");
    const body = {
      semanticVersion: "GDSS_PREDICTIVE_EVIDENCE_SET_V1",
      modelVersionId: resourceId, modelHash: hash,
      protocolVersionId: resourceId, protocolHash: hash,
      validityDomainVersionId: resourceId, validityDomainHash: hash,
      partitionPlanVersionId: resourceId, partitionPlanHash: hash,
      snapshotId: resourceId, snapshotHash: hash,
      targetKey: "level", horizonKey: "h1",
      validationRunIds: [resourceId], pairSetIds: [resourceId],
      domainAssessmentIds: [resourceId], positionAssessmentIds: [resourceId],
      idempotencyKey: "ai-evidence",
    };
    const response = await route.POST(
      new Request("http://localhost", { method: "POST", body: JSON.stringify(body) }),
      { params: Promise.resolve({ projectId }) },
    );
    expect(response.status).toBe(403);
    expect(await response.json()).toMatchObject({ success: false, error: { code: "AI_AUTHORITY_FORBIDDEN" } });
  });
});
