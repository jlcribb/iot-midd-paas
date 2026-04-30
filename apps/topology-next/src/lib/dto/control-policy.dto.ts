export type ControlPolicyType = "proportional" | "threshold";

export interface ControlPolicy {
  id: string;
  project_id: string;
  variable: string;
  context_selector: Record<string, unknown>;
  policy_type: ControlPolicyType;
  params: Record<string, unknown>;
  priority: number;
  enabled: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}
