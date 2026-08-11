export type ControlPolicyType = "proportional" | "threshold";

export interface ControlPolicyBinding {
  asset_id: string;
  variable_key: string;
}

export interface ControlPolicy {
  id: string;
  project_id: string;
  variable: string;
  binding?: ControlPolicyBinding | null;
  context_selector: Record<string, unknown>;
  policy_type: ControlPolicyType;
  params: Record<string, unknown>;
  priority: number;
  enabled: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ControlPolicyConflict {
  type: "selection_tie" | "shadowed_by_enabled_policy" | "shadows_enabled_policy";
  severity: "error" | "warning";
  message: string;
  conflicting_policy_ids: string[];
}

export interface ControlPolicyPreviewCandidate {
  id?: string;
  project_id: string;
  variable: string;
  binding?: ControlPolicyBinding | null;
  policy_type: ControlPolicyType;
  context_selector: Record<string, unknown>;
  params: Record<string, unknown>;
  priority: number;
  enabled: boolean;
  version?: number;
}

export interface ControlPolicyPreviewResponse {
  current_selected_policy: ControlPolicy | null;
  hypothetical_selected_policy: ControlPolicy | null;
  candidate_would_be_selected: boolean;
  matching_policy_ids: string[];
  hypothetical_matching_policy_ids: string[];
  conflicts: ControlPolicyConflict[];
  warnings: string[];
}
