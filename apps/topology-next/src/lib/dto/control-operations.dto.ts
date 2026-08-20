import type { Project } from "@/lib/dto/project.dto";

export type ControlOperationalStatus =
  | "HEALTHY"
  | "INACTIVE"
  | "RECOMMENDATION_ONLY"
  | "PENDING"
  | "PUBLISHED"
  | "ACKNOWLEDGED"
  | "RETRYING"
  | "FAILED"
  | "EXPIRED"
  | "MISCONFIGURED";

export type ControlAttentionSeverity = "warning" | "error";

export interface ControlOperationsPage<T> {
  items: T[];
  limit: number;
  offset: number;
}

export interface BindingOperationalView {
  binding_id: string;
  policy_id: string;
  source_asset_id: string | null;
  source_asset_name: string | null;
  target_asset_id: string | null;
  target_asset_name: string | null;
  control_point: string;
  operation: string;
  target_capabilities: Record<string, unknown>[];
  valid: boolean;
  actionable: boolean;
  reason_code: string | null;
  reason: string | null;
}

export interface PolicyOperationalView {
  policy_id: string;
  project_id: string;
  variable: string;
  enabled: boolean;
  configured_status: "ENABLED" | "DISABLED";
  effective_status: ControlOperationalStatus;
  reason_code: string | null;
  reason: string | null;
  source_asset_id: string | null;
  source_asset_name: string | null;
  target_asset_id: string | null;
  target_asset_name: string | null;
  operation: string | null;
  binding_status: "NONE" | "VALID" | "INVALID";
  actionability: "ACTIONABLE" | "RECOMMENDATION_ONLY" | "MISCONFIGURED" | "INACTIVE";
  recommendation_only: boolean;
  recommendation_only_reason: string | null;
  last_evaluation_at: string | null;
  last_recommendation_at: string | null;
}

export interface RecommendationOperationalView {
  audit_id: string;
  recommendation_id: string | null;
  correlation_id: string | null;
  project_id: string;
  policy_id: string | null;
  source_asset_id: string | null;
  target_asset_id: string | null;
  created_at: string;
  status: "RECOMMENDED";
  delivery_intent_id: string | null;
  command_id: string | null;
  summary: string | null;
}

export interface DeliveryOperationalView {
  delivery_intent_id: string;
  command_id: string;
  recommendation_id: string;
  correlation_id: string;
  project_id: string;
  policy_id: string;
  source_asset_id: string | null;
  target_asset_id: string | null;
  target_name: string | null;
  operation: string;
  intent_status: ControlOperationalStatus;
  outbox_status: ControlOperationalStatus | null;
  ack_status: "ACKNOWLEDGED" | null;
  retry_count: number;
  last_error: string | null;
  event_id: string | null;
  created_at: string;
  updated_at: string;
  expires_at: string;
}

export interface OperationalAttentionItem {
  severity: ControlAttentionSeverity;
  category: "BINDING" | "DELIVERY" | "OUTBOX";
  entity_type: "policy" | "binding" | "delivery" | "outbox";
  entity_id: string;
  message: string;
  detected_at: string;
  action_hint: string;
}

export interface ProjectControlOperationsSummary {
  project: Pick<Project, "id" | "name" | "parametric_control_enabled">;
  control_enabled: boolean;
  control_mode: "SIMULATED" | "INACTIVE";
  policy_summary: { total: number; enabled: number; actionable: number; recommendation_only: number; misconfigured: number };
  binding_summary: { total: number; actionable: number; invalid: number };
  recommendation_summary: { total: number; last_at: string | null };
  delivery_summary: Record<ControlOperationalStatus, number>;
  attention_summary: { total: number; warnings: number; errors: number };
  last_activity_at: string | null;
}
