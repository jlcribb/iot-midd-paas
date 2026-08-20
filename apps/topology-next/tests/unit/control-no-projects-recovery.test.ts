import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { ControlNoProjectsRecovery, ControlSessionIdentity, initialControlProjectScope } from "@/components/control/control-dashboard";

describe("Control Operations no-project recovery", () => {
  it("shows identity and both canonical recovery actions for an authenticated zero-project session", () => {
    const html = renderToStaticMarkup(ControlNoProjectsRecovery({ email: "unauthorized@example.test" }));

    expect(html).toContain("No projects are available in your control scope.");
    expect(html).toContain("Signed in as unauthorized@example.test");
    expect(html).toContain("Change account");
    expect(html).toContain("Sign out");
  });

  it("keeps an authorized project scope outside the no-project recovery state", () => {
    const scope = initialControlProjectScope([{
      id: "allowed-project", name: "Allowed project", description: null, status: "active",
      parametric_control_enabled: true, metadata: {}, created_at: "2026-08-20T00:00:00.000Z", updated_at: "2026-08-20T00:00:00.000Z"
    }]);

    expect(scope.error).toBeNull();
    expect(scope.projectId).toBe("allowed-project");
  });

  it("shows the OAuth email in the authorized dashboard without exposing session internals", () => {
    const html = renderToStaticMarkup(ControlSessionIdentity({ email: "authorized@example.test" }));

    expect(html).toContain("Signed in as authorized@example.test");
    expect(html).not.toContain("providerAccountId");
    expect(html).not.toContain("token");
  });
});
