import { describe, expect, it, vi } from "vitest";
import { UnauthorizedError } from "@/lib/errors/domain-errors";

vi.mock("@/lib/auth/control-auth-session", () => ({ resolveAuthenticatedControlActor: vi.fn(async () => { throw new UnauthorizedError("Authentication required"); }) }));

describe("M7.3 controlled policy validation routes", () => {
  it("returns 401 for an unauthenticated validation creation request", async () => {
    const route = await import("@/app/api/control/promotion/projects/[projectId]/policy-version-candidates/[candidateId]/validations/route");
    const response = await route.POST(new Request("http://localhost", { method: "POST", body: "{}" }), { params: Promise.resolve({ projectId: "11111111-1111-4111-8111-111111111111", candidateId: "22222222-2222-4222-8222-222222222222" }) });
    expect(response.status).toBe(401);
  });
});
