import type { Project } from "@/lib/dto/project.dto";

export type ControlRole = "viewer" | "operator" | "admin";

export interface ControlActor {
  user_id: string;
  display_name: string | null;
  role: ControlRole;
  project_ids: string[];
  all_projects: boolean;
}

export interface ControlPermissions {
  view_dashboard: boolean;
  view_policies: boolean;
  edit_policies: boolean;
  toggle_policies: boolean;
  delete_policies: boolean;
}

export interface ControlAccessSnapshot {
  actor: ControlActor;
  permissions: ControlPermissions;
  allowed_projects: Project[];
}
