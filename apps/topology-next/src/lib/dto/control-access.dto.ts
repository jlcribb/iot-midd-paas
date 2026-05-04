import type { Project } from "@/lib/dto/project.dto";

export type ControlRole = "viewer" | "operator" | "admin";

export interface ControlActor {
  actor_id?: string;
  user_id: string;
  username?: string | null;
  display_name: string | null;
  email?: string | null;
  image?: string | null;
  auth_provider?: string | null;
  provider_account_id?: string | null;
  auth_source?: "oauth_session" | "dev_fallback";
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
