import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

async function loadOauthProviderConfig() {
  vi.resetModules();
  return import("@/lib/auth/oauth-provider-config");
}

describe("oauth-provider-config", () => {
  const envSnapshot = { ...process.env };

  afterEach(() => {
    process.env = { ...envSnapshot };
    vi.restoreAllMocks();
  });

  it("treats non-empty non-placeholder values as configured credentials", async () => {
    const module = await loadOauthProviderConfig();

    expect(module.hasConfiguredCredential("test-github-client-id")).toBe(true);
    expect(module.hasConfiguredCredential(" test-google-client-secret ")).toBe(true);
  });

  it("treats placeholders and blank values as absent credentials", async () => {
    const module = await loadOauthProviderConfig();

    expect(module.hasConfiguredCredential("")).toBe(false);
    expect(module.hasConfiguredCredential("   ")).toBe(false);
    expect(module.hasConfiguredCredential("REPLACE_WITH_GITHUB_CLIENT_ID")).toBe(false);
    expect(module.hasConfiguredCredential("replace-with-long-random-secret")).toBe(false);
  });

  it("detects fully configured and partial provider states", async () => {
    const module = await loadOauthProviderConfig();

    expect(module.getProviderConfiguration("test-github-client-id", "test-github-client-secret")).toEqual({
      configured: true,
      partial: false
    });
    expect(module.getProviderConfiguration("test-github-client-id", undefined)).toEqual({
      configured: false,
      partial: true
    });
    expect(module.getProviderConfiguration(undefined, "test-github-client-secret")).toEqual({
      configured: false,
      partial: true
    });
    expect(module.getProviderConfiguration("REPLACE_WITH_GITHUB_CLIENT_ID", "REPLACE_WITH_GITHUB_CLIENT_SECRET")).toEqual({
      configured: false,
      partial: false
    });
  });

  it("builds the aggregate oauth status without exposing values", async () => {
    process.env.AUTH_GITHUB_ID = "test-github-client-id";
    process.env.AUTH_GITHUB_SECRET = "test-github-client-secret";
    process.env.AUTH_GOOGLE_ID = "test-google-client-id";
    process.env.AUTH_GOOGLE_SECRET = "REPLACE_WITH_GOOGLE_CLIENT_SECRET";
    process.env.NEXTAUTH_SECRET = "test-nextauth-secret";

    const module = await loadOauthProviderConfig();
    expect(module.getOAuthConfigurationStatus()).toEqual({
      github: {
        configured: true,
        partial: false
      },
      google: {
        configured: false,
        partial: true
      },
      nextAuthSecretConfigured: true
    });
  });

  it("prefers NEXTAUTH values over legacy AUTH values", async () => {
    process.env.NEXTAUTH_URL = "http://127.0.0.1:3000";
    process.env.AUTH_URL = "http://localhost:3000";
    process.env.NEXTAUTH_SECRET = "test-nextauth-secret";
    process.env.AUTH_SECRET = "legacy-secret";

    const module = await loadOauthProviderConfig();

    expect(module.getResolvedNextAuthUrl()).toBe("http://127.0.0.1:3000");
    expect(module.getResolvedNextAuthSecret()).toBe("test-nextauth-secret");
  });

  it("falls back to legacy AUTH values when NEXTAUTH values are absent", async () => {
    delete process.env.NEXTAUTH_URL;
    delete process.env.NEXTAUTH_SECRET;
    process.env.AUTH_URL = "http://localhost:3000";
    process.env.AUTH_SECRET = "test-nextauth-secret";

    const module = await loadOauthProviderConfig();

    expect(module.getResolvedNextAuthUrl()).toBe("http://localhost:3000");
    expect(module.getResolvedNextAuthSecret()).toBe("test-nextauth-secret");
  });
});
