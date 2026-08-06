import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

const getServerSessionMock = vi.fn();
const redirectMock = vi.fn((url: string) => {
  throw new Error(`REDIRECT:${url}`);
});
const resolveAuthenticatedControlActorFromSourcesMock = vi.fn();
const buildServerContextRequestMock = vi.fn(async () => new Request("http://localhost/control"));

vi.mock("next-auth/next", () => ({
  getServerSession: getServerSessionMock
}));

vi.mock("next/navigation", () => ({
  redirect: redirectMock
}));

vi.mock("@/lib/auth/control-auth-session", () => ({
  resolveAuthenticatedControlActorFromSources: resolveAuthenticatedControlActorFromSourcesMock,
  buildServerContextRequest: buildServerContextRequestMock
}));

vi.mock("@/components/control/control-dashboard", () => ({
  ControlDashboard: () => null
}));

async function loadControlPageModule() {
  vi.resetModules();
  return import("@/app/control/page");
}

describe("control page auth gate", () => {
  afterEach(() => {
    getServerSessionMock.mockReset();
    redirectMock.mockClear();
    resolveAuthenticatedControlActorFromSourcesMock.mockReset();
    buildServerContextRequestMock.mockClear();
  });

  it("redirects unauthenticated access to /login with callbackUrl", async () => {
    getServerSessionMock.mockResolvedValue(null);
    resolveAuthenticatedControlActorFromSourcesMock.mockRejectedValue(new Error("Authentication required"));

    const module = await loadControlPageModule();

    await expect(module.default()).rejects.toThrow("REDIRECT:/login?callbackUrl=%2Fcontrol");
  });
});
