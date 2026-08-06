import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

async function loadAuthOptionsModule() {
  vi.resetModules();
  return import("@/lib/auth/auth-options");
}

describe("auth-options", () => {
  const envSnapshot = { ...process.env };

  afterEach(() => {
    process.env = { ...envSnapshot };
    vi.restoreAllMocks();
  });

  it("preserves jwt sessions and the custom sign-in page", async () => {
    const module = await loadAuthOptionsModule();

    expect(module.authOptions.session?.strategy).toBe("jwt");
    expect(module.authOptions.pages?.signIn).toBe("/login");
  });

  it("registers no providers when credentials are absent or placeholders", async () => {
    process.env.AUTH_GITHUB_ID = "REPLACE_WITH_GITHUB_CLIENT_ID";
    process.env.AUTH_GITHUB_SECRET = "REPLACE_WITH_GITHUB_CLIENT_SECRET";
    process.env.AUTH_GOOGLE_ID = "";
    process.env.AUTH_GOOGLE_SECRET = "";

    const module = await loadAuthOptionsModule();

    expect(module.getConfiguredAuthProviderIds()).toEqual([]);
  });

  it("registers only fully configured providers", async () => {
    process.env.AUTH_GITHUB_ID = "test-github-client-id";
    process.env.AUTH_GITHUB_SECRET = "test-github-client-secret";
    process.env.AUTH_GOOGLE_ID = "test-google-client-id";
    process.env.AUTH_GOOGLE_SECRET = "";

    const module = await loadAuthOptionsModule();

    expect(module.getConfiguredAuthProviderIds()).toEqual(["github"]);
  });

  it("registers both providers when both configurations are complete", async () => {
    process.env.AUTH_GITHUB_ID = "test-github-client-id";
    process.env.AUTH_GITHUB_SECRET = "test-github-client-secret";
    process.env.AUTH_GOOGLE_ID = "test-google-client-id";
    process.env.AUTH_GOOGLE_SECRET = "test-google-client-secret";

    const module = await loadAuthOptionsModule();

    expect(module.getConfiguredAuthProviderIds()).toEqual(["google", "github"]);
  });

  it("uses NEXTAUTH_SECRET before AUTH_SECRET", async () => {
    process.env.NEXTAUTH_SECRET = "test-nextauth-secret";
    process.env.AUTH_SECRET = "legacy-secret";

    const module = await loadAuthOptionsModule();

    expect(module.authOptions.secret).toBe("test-nextauth-secret");
  });
});
