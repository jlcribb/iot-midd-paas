import { describe, expect, it, vi } from "vitest";
import {
  buildPersistedProjectControlAccess,
  resolvePersistedProjectControlAccess
} from "@/lib/services/project-control-membership.service";

describe("project-control-membership.service", () => {
  it("builds an explicit project scope without implicit global access", () => {
    const access = buildPersistedProjectControlAccess([
      { actor_email: "admin@example.com", project_id: "project-b", role: "viewer", enabled: true },
      { actor_email: "admin@example.com", project_id: "project-a", role: "admin", enabled: true }
    ]);

    expect(access).toEqual({
      role: "admin",
      projectIds: ["project-a", "project-b"],
      projectRoles: { "project-b": "viewer", "project-a": "admin" },
      allProjects: false
    });
  });

  it("keeps disabled and different-project memberships out of an actor's scope", () => {
    const access = buildPersistedProjectControlAccess([
      { actor_email: "authorized@example.test", project_id: "allowed-project", role: "viewer", enabled: true },
      { actor_email: "authorized@example.test", project_id: "disabled-project", role: "admin", enabled: false }
    ]);

    expect(access).toEqual({
      role: "viewer",
      projectIds: ["allowed-project"],
      projectRoles: { "allowed-project": "viewer" },
      allProjects: false
    });
    expect(access.projectIds).not.toContain("disabled-project");
    expect(access.projectIds).not.toContain("different-project");
  });

  it("fails closed when the actor has no persisted membership", async () => {
    const findActiveByActorEmail = vi.fn().mockResolvedValue([]);
    const access = await resolvePersistedProjectControlAccess("viewer@example.com", { findActiveByActorEmail });

    expect(access).toEqual({ role: "viewer", projectIds: [], projectRoles: {}, allProjects: false });
    expect(findActiveByActorEmail).toHaveBeenCalledWith("viewer@example.com");
  });

  it("fails closed when membership lookup cannot be resolved", async () => {
    const access = await resolvePersistedProjectControlAccess("viewer@example.com", {
      findActiveByActorEmail: vi.fn().mockRejectedValue(new Error("database unavailable"))
    });

    expect(access).toEqual({ role: "viewer", projectIds: [], projectRoles: {}, allProjects: false });
  });
});
