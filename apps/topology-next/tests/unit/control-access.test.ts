import { describe, expect, it } from "vitest";
import {
  assertControlPermission,
  canAccessProject,
  getControlPermissions,
  getControlRoleForProject,
  getScopedProjectIds,
  resolveControlActor
} from "@/lib/auth/control-access";

describe("control-access", () => {
  it("resolves actor identity and scope from request headers", () => {
    const actor = resolveControlActor(new Request("http://localhost/api/control/access", {
      headers: {
        "x-control-user-id": "user-1",
        "x-control-user-name": "Operator Uno",
        "x-control-user-role": "operator",
        "x-control-project-ids": "project-1, project-2"
      }
    }));

    expect(actor.user_id).toBe("user-1");
    expect(actor.role).toBe("operator");
    expect(actor.project_ids).toEqual(["project-1", "project-2"]);
    expect(actor.all_projects).toBe(false);
  });

  it("maps permissions per role", () => {
    expect(getControlPermissions("viewer").edit_policies).toBe(false);
    expect(getControlPermissions("operator").toggle_policies).toBe(true);
    expect(getControlPermissions("admin").delete_policies).toBe(true);
    expect(getControlPermissions("operator").manage_parametric_control).toBe(false);
    expect(getControlPermissions("admin").manage_parametric_control).toBe(true);
  });

  it("uses the persisted role assigned to the requested project", () => {
    const actor = {
      actor_id: "multi-role-1",
      user_id: "multi-role-1",
      display_name: null,
      role: "admin" as const,
      project_ids: ["project-1", "project-2"],
      project_roles: { "project-1": "admin" as const, "project-2": "viewer" as const },
      all_projects: false
    };

    expect(getControlRoleForProject(actor, "project-1")).toBe("admin");
    expect(getControlRoleForProject(actor, "project-2")).toBe("viewer");
    expect(() => assertControlPermission(actor, "manage_parametric_control", "project-2")).toThrow(
      "Role viewer cannot perform manage_parametric_control"
    );
  });

  it("fails closed for an OAuth actor without a persisted project role", () => {
    const actor = {
      actor_id: "legacy-admin-1",
      user_id: "legacy-admin-1",
      display_name: null,
      auth_source: "oauth_session" as const,
      role: "admin" as const,
      project_ids: ["project-1"],
      project_roles: {},
      all_projects: false
    };

    expect(getControlRoleForProject(actor, "project-1")).toBe("viewer");
    expect(() => assertControlPermission(actor, "manage_parametric_control", "project-1")).toThrow(
      "Role viewer cannot perform manage_parametric_control"
    );
  });

  it("checks project scope access", () => {
    const actor = {
      actor_id: "viewer-1",
      user_id: "viewer-1",
      username: "viewer-1",
      display_name: null,
      email: null,
      image: null,
      auth_provider: null,
      provider_account_id: null,
      auth_source: "dev_fallback" as const,
      role: "viewer" as const,
      all_projects: false,
      project_ids: ["project-1"]
    };

    expect(canAccessProject(actor, "project-1")).toBe(true);
    expect(canAccessProject(actor, "project-2")).toBe(false);
    expect(getScopedProjectIds(actor)).toEqual(["project-1"]);
  });

  it("rejects actions outside the role matrix", () => {
    const actor = {
      actor_id: "viewer-1",
      user_id: "viewer-1",
      username: "viewer-1",
      display_name: null,
      email: null,
      image: null,
      auth_provider: null,
      provider_account_id: null,
      auth_source: "dev_fallback" as const,
      role: "viewer" as const,
      all_projects: false,
      project_ids: ["project-1"]
    };

    expect(() => assertControlPermission(actor, "edit_policies", "project-1")).toThrow("Role viewer cannot perform edit_policies");
  });
});
