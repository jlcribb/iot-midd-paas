export interface ControlRecommendationView {
  audit_id: string;
  observed_at: string;
  project_id: string | null;
  variable_id: string | null;
  event_id: string | null;
  recommendation_kind: string | null;
  action_label: string | null;
  actuator_name: string | null;
  command_value: number | null;
  summary: string | null;
  measurement_value: number | null;
  setpoint_value: number | null;
  error: number | null;
  evaluator_name: string | null;
  policy_id: string | null;
  policy_type: string | null;
  policy_version: number | null;
  policy_priority: number | null;
}

export interface ControlAuditView {
  id: number;
  ts: string;
  action: string;
  project_id: string | null;
  status: "processed" | "skipped" | "error";
  variable_id: string | null;
  event_id: string | null;
  policy_id: string | null;
  policy_type: string | null;
  policy_version: number | null;
  policy_priority: number | null;
  summary: string | null;
  envelope: Record<string, unknown>;
}

export interface ControlStatusView {
  activity_status: "active" | "idle" | "stale";
  latest_audit_at: string | null;
  latest_recommendation_at: string | null;
  latest_skipped_at: string | null;
  enabled_projects: number;
  enabled_policies: number;
  projects_with_policies: number;
  audits_last_24h: number;
  recommendations_last_24h: number;
  skipped_last_24h: number;
  errors_last_24h: number;
}
