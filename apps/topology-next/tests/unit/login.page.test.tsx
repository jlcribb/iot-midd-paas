import { afterEach, describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { Session } from "next-auth";

vi.mock("server-only", () => ({}));

const getServerSessionMock = vi.fn<() => Promise<Session | null>>();
const redirectMock = vi.fn((url: string) => {
  throw new Error(`REDIRECT:${url}`);
});

vi.mock("next-auth/next", () => ({
  getServerSession: getServerSessionMock
}));

vi.mock("next/navigation", () => ({
  redirect: redirectMock
}));

async function loadLoginPageModule() {
  vi.resetModules();
  return import("@/app/login/page");
}

describe("login page", () => {
  const envSnapshot = { ...process.env };

  afterEach(() => {
    process.env = { ...envSnapshot };
    getServerSessionMock.mockReset();
    redirectMock.mockClear();
  });

  it("renders disabled buttons and provider-specific messages without exposing env names", async () => {
    getServerSessionMock.mockResolvedValue(null);
    process.env.AUTH_GITHUB_ID = "REPLACE_WITH_GITHUB_CLIENT_ID";
    process.env.AUTH_GITHUB_SECRET = "REPLACE_WITH_GITHUB_CLIENT_SECRET";
    process.env.AUTH_GOOGLE_ID = "REPLACE_WITH_GOOGLE_CLIENT_ID";
    process.env.AUTH_GOOGLE_SECRET = "REPLACE_WITH_GOOGLE_CLIENT_SECRET";

    const module = await loadLoginPageModule();
    const element = await module.default({
      searchParams: Promise.resolve({
        callbackUrl: "/control"
      })
    });

    const html = renderToStaticMarkup(element);

    expect(html).toContain("Entrar con Google");
    expect(html).toContain("Entrar con GitHub");
    expect(html).toContain("Google no est");
    expect(html).toContain("GitHub no est");
    expect(html).not.toContain("AUTH_GOOGLE");
    expect(html).not.toContain("AUTH_GITHUB");
    expect(html).toContain("disabled");
  });

  it("renders enabled links when providers are fully configured and preserves callbackUrl", async () => {
    getServerSessionMock.mockResolvedValue(null);
    process.env.AUTH_GITHUB_ID = "test-github-client-id";
    process.env.AUTH_GITHUB_SECRET = "test-github-client-secret";
    process.env.AUTH_GOOGLE_ID = "test-google-client-id";
    process.env.AUTH_GOOGLE_SECRET = "test-google-client-secret";

    const module = await loadLoginPageModule();
    const element = await module.default({
      searchParams: Promise.resolve({
        callbackUrl: "/control/policies"
      })
    });

    const html = renderToStaticMarkup(element);

    expect(html).toContain("/api/auth/signin/google?callbackUrl=%2Fcontrol%2Fpolicies");
    expect(html).toContain("/api/auth/signin/github?callbackUrl=%2Fcontrol%2Fpolicies");
    expect(html).not.toContain("Google no est");
    expect(html).not.toContain("GitHub no est");
  });

  it("redirects authenticated users to the resolved callbackUrl", async () => {
    getServerSessionMock.mockResolvedValue({
      expires: "2026-12-31T00:00:00.000Z",
      user: {
        email: "operator@example.com"
      }
    } as Session);

    const module = await loadLoginPageModule();

    await expect(module.default({
      searchParams: Promise.resolve({
        callbackUrl: "/control"
      })
    })).rejects.toThrow("REDIRECT:/control");
  });
});
