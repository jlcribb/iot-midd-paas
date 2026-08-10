import { afterEach, describe, expect, it, vi } from "vitest";
import type { Session } from "next-auth";
import {
  buildAuthenticatedControlActorFromSession,
  isDevFallbackEnabled,
  resolveAuthenticatedControlActorFromSources
} from "@/lib/auth/control-auth-session";
import { resolveRoleFromEmail } from "@/lib/auth/control-access";

vi.mock("server-only", () => ({}));

function makeSession(partial?: Partial<Session>): Session {
  return {
    expires: "2026-12-31T00:00:00.000Z",
    user: {
      email: "viewer@example.com",
      name: "Viewer Uno",
      image: "https://example.com/avatar.png",
      ...(partial?.user ?? {})
    },
    control: partial?.control
  };
}

describe("control-auth-session", () => {
  const envSnapshot = { ...process.env };

  afterEach(() => {
    process.env = { ...envSnapshot };
    vi.restoreAllMocks();
  });

  it("maps authenticated emails to explicit roles", () => {
    process.env.CONTROL_AUTH_ADMIN_EMAILS = "admin@example.com";
    process.env.CONTROL_AUTH_OPERATOR_EMAILS = "operator@example.com";
    process.env.CONTROL_AUTH_VIEWER_EMAILS = "viewer@example.com";

    expect(resolveRoleFromEmail("admin@example.com")).toBe("admin");
    expect(resolveRoleFromEmail("operator@example.com")).toBe("operator");
    expect(resolveRoleFromEmail("viewer@example.com")).toBe("viewer");
    expect(resolveRoleFromEmail("unknown@example.com")).toBe("viewer");
  });

  it("builds an authenticated control actor from the OAuth session", () => {
    const actor = buildAuthenticatedControlActorFromSession(makeSession({
      user: {
        email: "operator@example.com",
        name: "Operator Uno"
      },
      control: {
        actorId: "operator@example.com",
        role: "operator",
        provider: "google",
        providerAccountId: "google-account-1",
        allProjects: true,
        projectIds: [],
        projectRoles: {}
      }
    }));

    expect(actor.user_id).toBe("operator@example.com");
    expect(actor.auth_source).toBe("oauth_session");
    expect(actor.role).toBe("operator");
    expect(actor.auth_provider).toBe("google");
    expect(actor.provider_account_id).toBe("google-account-1");
    expect(actor.all_projects).toBe(false);
  });

  it("returns 401 when no session is present and dev fallback is disabled", async () => {
    process.env.CONTROL_RBAC_ALLOW_DEV_FALLBACK = "false";

    await expect(resolveAuthenticatedControlActorFromSources({
      session: null,
      request: new Request("http://localhost/api/control/access")
    })).rejects.toMatchObject({
      status: 401
    });
  });

  it("keeps the fallback disabled when the flag is absent", async () => {
    delete process.env.CONTROL_RBAC_ALLOW_DEV_FALLBACK;

    expect(isDevFallbackEnabled()).toBe(false);

    await expect(resolveAuthenticatedControlActorFromSources({
      session: null,
      request: new Request("http://localhost/api/control/access")
    })).rejects.toMatchObject({
      status: 401
    });
  });

  it("uses dev fallback only when explicitly enabled", async () => {
    process.env.CONTROL_RBAC_ALLOW_DEV_FALLBACK = "true";
    process.env.CONTROL_RBAC_DEFAULT_ROLE = "operator";
    process.env.CONTROL_RBAC_DEFAULT_USER_ID = "fallback-operator";

    expect(isDevFallbackEnabled()).toBe(true);

    const actor = await resolveAuthenticatedControlActorFromSources({
      session: null,
      request: new Request("http://localhost/api/control/access", {
        headers: {
          "x-control-project-ids": "project-1"
        }
      })
    });

    expect(actor.user_id).toBe("fallback-operator");
    expect(actor.auth_source).toBe("dev_fallback");
    expect(actor.role).toBe("operator");
  });

  it("prefers an OAuth session over the enabled development fallback", async () => {
    process.env.CONTROL_RBAC_ALLOW_DEV_FALLBACK = "true";

    const actor = await resolveAuthenticatedControlActorFromSources({
      session: makeSession({
        control: {
          actorId: "viewer@example.com",
          role: "viewer",
          provider: "github",
        providerAccountId: "github-account-1",
        allProjects: true,
        projectIds: [],
        projectRoles: {}
        }
      }),
      request: new Request("http://localhost/api/control/access")
    });

    expect(actor.auth_source).toBe("oauth_session");
    expect(actor.auth_provider).toBe("github");
  });
});
