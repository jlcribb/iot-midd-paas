import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { ControlAuthenticationRequired, CONTROL_OAUTH_CALLBACK_URL } from "@/components/control/control-authentication-required";
import { initialControlProjectScope, NO_PROJECTS_IN_SCOPE_MESSAGE } from "@/components/control/control-dashboard";

describe("Control authentication entry point", () => {
  it("renders an explicit sign-in CTA for an unauthenticated Control Operations visitor", () => {
    const html = renderToStaticMarkup(createElement(ControlAuthenticationRequired, { availableProviders: ["google", "github"] }));
    expect(html).toContain("Authentication required");
    expect(html).toContain("Sign in to access Control Operations");
    expect(html).toContain("Continue with Google");
    expect(html).toContain("Continue with GitHub");
  });

  it("renders Google as the direct OAuth entry point without requiring the generic login link", () => {
    const html = renderToStaticMarkup(createElement(ControlAuthenticationRequired, { availableProviders: ["google"] }));
    expect(CONTROL_OAUTH_CALLBACK_URL).toBe("/control");
    expect(html).toContain("Continue with Google");
    expect(html).toContain("Continue with GitHub");
    expect(html).not.toContain('href="/login?callbackUrl=%2Fcontrol"');
  });

  it("keeps the authenticated-without-projects state explicit and safe", () => {
    expect(initialControlProjectScope([])).toEqual({ projectId: "", error: NO_PROJECTS_IN_SCOPE_MESSAGE });
    expect(initialControlProjectScope([{
      id: "allowed-project", name: "Allowed project", description: null, status: "active",
      parametric_control_enabled: true, metadata: {}, created_at: "2026-08-20T00:00:00.000Z", updated_at: "2026-08-20T00:00:00.000Z"
    }])).toEqual({ projectId: "allowed-project", error: null });
  });
});
