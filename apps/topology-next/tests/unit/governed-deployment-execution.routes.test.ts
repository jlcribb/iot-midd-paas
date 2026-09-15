import { describe, expect, it, vi } from "vitest";
import { UnauthorizedError } from "@/lib/errors/domain-errors";

vi.mock("@/lib/auth/control-auth-session", () => ({ resolveAuthenticatedControlActor: vi.fn(async () => { throw new UnauthorizedError("Authentication required"); }) }));

describe("M7.6 execution routes", () => {
  it("denies unauthenticated execution, including forged body actor fields", async () => {
    const executions = await import("@/app/api/control/promotion/projects/[projectId]/policy-version-candidates/[candidateId]/deployment-intents/[intentId]/executions/route");
    const params = { projectId: "11111111-1111-4111-8111-111111111111", candidateId: "22222222-2222-4222-8222-222222222222", intentId: "33333333-3333-4333-8333-333333333333" };
    expect((await executions.POST(new Request("http://localhost", { method: "POST", body: JSON.stringify({ executorId: "forged" }) }), { params: Promise.resolve(params) })).status).toBe(401);
    expect((await executions.GET(new Request("http://localhost"), { params: Promise.resolve(params) })).status).toBe(401);
  });
});
