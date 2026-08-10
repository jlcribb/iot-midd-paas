import type { ControlRole } from "@/lib/dto/control-access.dto";
import type { PersistedProjectControlAccess, ProjectControlMembership } from "@/lib/dto/project-control-membership.dto";
import { ProjectControlMembershipRepository } from "@/lib/repositories/project-control-membership.repository";

type MembershipLookup = Pick<ProjectControlMembershipRepository, "findActiveByActorEmail">;

const ROLE_RANK: Record<ControlRole, number> = {
  viewer: 1,
  operator: 2,
  admin: 3
};

function emptyAccess(): PersistedProjectControlAccess {
  return {
    role: "viewer",
    projectIds: [],
    projectRoles: {},
    allProjects: false
  };
}

export function buildPersistedProjectControlAccess(memberships: ProjectControlMembership[]): PersistedProjectControlAccess {
  if (memberships.length === 0) {
    return emptyAccess();
  }

  const projectRoles: Record<string, ControlRole> = {};
  let highestRole: ControlRole = "viewer";

  for (const membership of memberships) {
    if (!membership.enabled) continue;
    projectRoles[membership.project_id] = membership.role;
    if (ROLE_RANK[membership.role] > ROLE_RANK[highestRole]) {
      highestRole = membership.role;
    }
  }

  return {
    role: highestRole,
    projectIds: Object.keys(projectRoles).sort(),
    projectRoles,
    allProjects: false
  };
}

export async function resolvePersistedProjectControlAccess(
  email: string | null | undefined,
  repository: MembershipLookup = new ProjectControlMembershipRepository()
): Promise<PersistedProjectControlAccess> {
  const normalizedEmail = email?.trim().toLowerCase();
  if (!normalizedEmail) {
    return emptyAccess();
  }

  try {
    return buildPersistedProjectControlAccess(await repository.findActiveByActorEmail(normalizedEmail));
  } catch {
    return emptyAccess();
  }
}
