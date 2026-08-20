import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { OAuthLoginPanel } from "@/components/auth/oauth-login-panel";

describe("OAuthLoginPanel", () => {
  it("renders the reusable configured-provider controls", () => {
    const html = renderToStaticMarkup(
      OAuthLoginPanel({
      callbackUrl: "/control",
      availableProviders: ["google", "github"]
      })
    );

    expect(html).toContain("Entrar con Google");
    expect(html).toContain("Entrar con GitHub");
  });

  it("renders provider-specific messages when a provider is unavailable", () => {
    const html = renderToStaticMarkup(
      OAuthLoginPanel({
        callbackUrl: "/control",
        availableProviders: ["github"]
      })
    );

    expect(html).toContain("Entrar con Google");
    expect(html).toContain("Entrar con GitHub");
    expect(html).toContain("disabled");
    expect(html).toContain("Google no est");
    expect(html).not.toContain("GitHub no est");
  });
});
