import { describe, expect, it } from "vitest";
import {
  assertControlPermission,
  canAccessProject,
  getControlPermissions,
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
  });

  it("checks project scope access", () => {
    const actor = {
      user_id: "viewer-1",
      display_name: null,
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
      user_id: "viewer-1",
      display_name: null,
      role: "viewer" as const,
      all_projects: false,
      project_ids: ["project-1"]
    };

    expect(() => assertControlPermission(actor, "edit_policies", "project-1")).toThrow("Role viewer cannot perform edit_policies");
  });
});
