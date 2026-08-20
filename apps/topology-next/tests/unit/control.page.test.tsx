import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

const {
  getServerSessionMock,
  resolveAuthenticatedControlActorFromSourcesMock,
  buildServerContextRequestMock,
  getOAuthConfigurationStatusMock,
  controlAuthenticationRequiredMock
} = vi.hoisted(() => ({
  getServerSessionMock: vi.fn(),
  resolveAuthenticatedControlActorFromSourcesMock: vi.fn(),
  buildServerContextRequestMock: vi.fn(async () => new Request("http://localhost/control")),
  getOAuthConfigurationStatusMock: vi.fn(),
  controlAuthenticationRequiredMock: vi.fn(() => null)
}));

vi.mock("next-auth/next", () => ({
  getServerSession: getServerSessionMock
}));

vi.mock("@/lib/auth/control-auth-session", () => ({
  resolveAuthenticatedControlActorFromSources: resolveAuthenticatedControlActorFromSourcesMock,
  buildServerContextRequest: buildServerContextRequestMock
}));

vi.mock("@/components/control/control-dashboard", () => ({
  ControlDashboard: () => null
}));

vi.mock("@/components/control/control-authentication-required", () => ({
  ControlAuthenticationRequired: controlAuthenticationRequiredMock
}));

vi.mock("@/lib/auth/oauth-provider-config", () => ({
  getOAuthConfigurationStatus: getOAuthConfigurationStatusMock,
  getResolvedNextAuthSecret: () => "test-secret",
  getResolvedNextAuthUrl: () => "http://localhost:3000"
}));

async function loadControlPageModule() {
  vi.resetModules();
  return import("@/app/control/page");
}

describe("control page auth gate", () => {
  afterEach(() => {
    getServerSessionMock.mockReset();
    resolveAuthenticatedControlActorFromSourcesMock.mockReset();
    buildServerContextRequestMock.mockClear();
    getOAuthConfigurationStatusMock.mockReset();
    controlAuthenticationRequiredMock.mockClear();
  });

  it("renders configured direct OAuth controls for unauthenticated access", async () => {
    getServerSessionMock.mockResolvedValue(null);
    resolveAuthenticatedControlActorFromSourcesMock.mockRejectedValue(new Error("Authentication required"));
    getOAuthConfigurationStatusMock.mockReturnValue({
      google: { configured: true, partial: false },
      github: { configured: true, partial: false },
      nextAuthSecretConfigured: true
    });

    const module = await loadControlPageModule();
    const page = await module.default();

    expect(page.type).toBe(controlAuthenticationRequiredMock);
    expect(page.props.availableProviders).toEqual(["google", "github"]);
  });
});
