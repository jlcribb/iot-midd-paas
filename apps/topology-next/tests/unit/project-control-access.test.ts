import { describe, expect, it } from "vitest";
import { resolveProjectControlUiState } from "@/components/topology/project-control-access";

describe("resolveProjectControlUiState", () => {
  it("enables the control only for an in-scope project with the derived capability", () => {
    expect(resolveProjectControlUiState({
      projectId: "project-1",
      isAccessLoading: false,
      hasAccessSnapshot: true,
      allowedProjectIds: ["project-1"],
      manageableProjectIds: ["project-1"]
    })).toMatchObject({ canManage: true, isAccessLoading: false });
  });

  it.each(["viewer", "operator"])("keeps the control read-only for %s capability snapshots", () => {
    expect(resolveProjectControlUiState({
      projectId: "project-1",
      isAccessLoading: false,
      hasAccessSnapshot: true,
      allowedProjectIds: ["project-1"],
      manageableProjectIds: []
    })).toMatchObject({ canManage: false, message: "Tu rol permite consultar este estado, pero no cambiarlo." });
  });

  it("does not offer a mutation outside the persisted project scope", () => {
    expect(resolveProjectControlUiState({
      projectId: "project-2",
      isAccessLoading: false,
      hasAccessSnapshot: true,
      allowedProjectIds: ["project-1"],
      manageableProjectIds: ["project-1"]
    })).toMatchObject({ canManage: false, message: "Este proyecto está fuera de tu scope de control." });
  });

  it("keeps the control disabled while access is unresolved or anonymous", () => {
    expect(resolveProjectControlUiState({
      projectId: "project-1",
      isAccessLoading: true,
      hasAccessSnapshot: false,
      allowedProjectIds: [],
      manageableProjectIds: []
    })).toMatchObject({ canManage: false, isAccessLoading: true });
    expect(resolveProjectControlUiState({
      projectId: "project-1",
      isAccessLoading: false,
      hasAccessSnapshot: false,
      allowedProjectIds: [],
      manageableProjectIds: []
    })).toMatchObject({ canManage: false, message: "Iniciá sesión para administrar el control paramétrico." });
  });
});
