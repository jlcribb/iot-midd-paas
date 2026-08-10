import type { ControlRole } from "@/lib/dto/control-access.dto";

export interface ProjectControlMembership {
  actor_email: string;
  project_id: string;
  role: ControlRole;
  enabled: boolean;
}

export interface PersistedProjectControlAccess {
  role: ControlRole;
  projectIds: string[];
  projectRoles: Record<string, ControlRole>;
  allProjects: false;
}
