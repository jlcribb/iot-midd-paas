import type { ControlActor, ControlPermissions, ControlRole } from "@/lib/dto/control-access.dto";
import { ForbiddenError, ValidationError } from "@/lib/errors/domain-errors";

const DEFAULT_DEV_ROLE: ControlRole = "admin";
const DEFAULT_DEV_SCOPE = "*";
const DEFAULT_DEV_USER_ID = "local-control-admin";
const DEFAULT_DEV_DISPLAY_NAME = "Local Control Admin";

const ROLE_VALUES = new Set<ControlRole>(["viewer", "operator", "admin"]);

const PERMISSIONS_BY_ROLE: Record<ControlRole, ControlPermissions> = {
  viewer: {
    view_dashboard: true,
    view_policies: true,
    edit_policies: false,
    toggle_policies: false,
    delete_policies: false
  },
  operator: {
    view_dashboard: true,
    view_policies: true,
    edit_policies: true,
    toggle_policies: true,
    delete_policies: false
  },
  admin: {
    view_dashboard: true,
    view_policies: true,
    edit_policies: true,
    toggle_policies: true,
    delete_policies: true
  }
};

type ControlPermissionName = keyof ControlPermissions;

function isDevelopmentRuntime() {
  return process.env.NODE_ENV !== "production";
}

function parseCookieHeader(cookieHeader: string | null): Map<string, string> {
  if (!cookieHeader) {
    return new Map();
  }

  return new Map(
    cookieHeader
      .split(";")
      .map((part) => part.trim())
      .filter(Boolean)
      .map((part) => {
        const separatorIndex = part.indexOf("=");
        if (separatorIndex < 0) {
          return [part, ""];
        }
        return [part.slice(0, separatorIndex), decodeURIComponent(part.slice(separatorIndex + 1))];
      })
  );
}

function readRequestValue(request: Request, headerName: string, cookieName: string): string | null {
  const headerValue = request.headers.get(headerName);
  if (headerValue !== null && headerValue.trim()) {
    return headerValue.trim();
  }

  const cookies = parseCookieHeader(request.headers.get("cookie"));
  const cookieValue = cookies.get(cookieName);
  if (cookieValue !== undefined && cookieValue.trim()) {
    return cookieValue.trim();
  }

  return null;
}

function parseRole(value: string): ControlRole {
  const normalized = value.trim().toLowerCase();
  if (!ROLE_VALUES.has(normalized as ControlRole)) {
    throw new ValidationError("Invalid control role");
  }
  return normalized as ControlRole;
}

function parseProjectScope(value: string | null, role: ControlRole): { all_projects: boolean; project_ids: string[] } {
  const defaultRaw = process.env.CONTROL_RBAC_DEFAULT_PROJECT_SCOPE
    ?? (isDevelopmentRuntime() ? DEFAULT_DEV_SCOPE : "");
  const raw = value ?? defaultRaw;
  if (!raw.trim()) {
    return {
      all_projects: role === "admin",
      project_ids: []
    };
  }

  if (raw === "*" || raw.toLowerCase() === "all") {
    return {
      all_projects: true,
      project_ids: []
    };
  }

  const projectIds = raw
    .split(",")
    .map((projectId) => projectId.trim())
    .filter(Boolean);

  return {
    all_projects: false,
    project_ids: [...new Set(projectIds)]
  };
}

export function resolveControlActor(request: Request): ControlActor {
  const roleRaw = readRequestValue(request, "x-control-user-role", "control_user_role")
    ?? process.env.CONTROL_RBAC_DEFAULT_ROLE
    ?? (isDevelopmentRuntime() ? DEFAULT_DEV_ROLE : "viewer");
  const role = parseRole(roleRaw);
  const userId = readRequestValue(request, "x-control-user-id", "control_user_id")
    ?? process.env.CONTROL_RBAC_DEFAULT_USER_ID
    ?? (isDevelopmentRuntime() ? DEFAULT_DEV_USER_ID : "anonymous-control-user");
  const displayName = readRequestValue(request, "x-control-user-name", "control_user_name")
    ?? process.env.CONTROL_RBAC_DEFAULT_USER_NAME
    ?? (isDevelopmentRuntime() ? DEFAULT_DEV_DISPLAY_NAME : null);
  const scope = parseProjectScope(readRequestValue(request, "x-control-project-ids", "control_project_ids"), role);

  return {
    user_id: userId,
    display_name: displayName,
    role,
    all_projects: scope.all_projects || role === "admin",
    project_ids: scope.project_ids
  };
}

export function getControlPermissions(role: ControlRole): ControlPermissions {
  return PERMISSIONS_BY_ROLE[role];
}

export function canAccessProject(actor: ControlActor, projectId: string) {
  return actor.all_projects || actor.project_ids.includes(projectId);
}

export function assertControlPermission(
  actor: ControlActor,
  permission: ControlPermissionName,
  projectId?: string
) {
  const permissions = getControlPermissions(actor.role);
  if (!permissions[permission]) {
    throw new ForbiddenError(`Role ${actor.role} cannot perform ${permission}`);
  }
  if (projectId && !canAccessProject(actor, projectId)) {
    throw new ForbiddenError("Project is outside the user's operational scope");
  }
}

export function getScopedProjectIds(actor: ControlActor, requestedProjectId?: string): string[] | undefined {
  if (requestedProjectId) {
    if (!canAccessProject(actor, requestedProjectId)) {
      throw new ForbiddenError("Project is outside the user's operational scope");
    }
    return [requestedProjectId];
  }

  if (actor.all_projects) {
    return undefined;
  }

  return actor.project_ids;
}

export function filterProjectsByScope<T extends { id: string }>(actor: ControlActor, projects: T[]): T[] {
  if (actor.all_projects) {
    return projects;
  }
  const allowed = new Set(actor.project_ids);
  return projects.filter((project) => allowed.has(project.id));
}
