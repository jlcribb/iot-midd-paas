import { assertControlPermission } from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import type {
  BindingOperationalView, ControlOperationsPage, ControlOperationalStatus, DeliveryOperationalView,
  OperationalAttentionItem, PolicyOperationalView, ProjectControlOperationsSummary,
  RecommendationOperationalView
} from "@/lib/dto/control-operations.dto";
import { NotFoundError, ValidationError } from "@/lib/errors/domain-errors";
import type { IProjectRepository } from "@/lib/repositories/contracts";
import {
  ControlOperationsRepository, type ControlOperationsDeliveryRecord, type ControlOperationsPolicyRecord,
  type ControlOperationsRecommendationRecord
} from "@/lib/repositories/control-operations.repository";
import { ProjectRepository } from "@/lib/repositories/project.repository";

const MAX_LIMIT = 100;

interface ControlOperationsServiceDeps {
  operationsRepo?: Pick<ControlOperationsRepository, "findPolicies" | "findRecommendations" | "findDeliveries" | "getMetrics">;
  projectRepo?: Pick<IProjectRepository, "findById">;
}

export interface OperationsPageInput { limit?: number; offset?: number; }

function page(input: OperationsPageInput = {}) {
  const limit = input.limit ?? 25;
  const offset = input.offset ?? 0;
  if (!Number.isInteger(limit) || limit < 1 || limit > MAX_LIMIT) throw new ValidationError(`limit must be an integer between 1 and ${MAX_LIMIT}`);
  if (!Number.isInteger(offset) || offset < 0) throw new ValidationError("offset must be a non-negative integer");
  return { limit, offset };
}

function capabilities(metadata: Record<string, unknown> | null): Record<string, unknown>[] {
  const values = metadata?.control_capabilities;
  return Array.isArray(values) ? values.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object" && !Array.isArray(item)) : [];
}

function bindingView(row: ControlOperationsPolicyRecord): BindingOperationalView | null {
  if (!row.binding_id || !row.control_point || !row.operation) return null;
  const targetCapabilities = capabilities(row.target_metadata);
  if (!row.binding_enabled) return { binding_id: row.binding_id, policy_id: row.policy_id, source_asset_id: row.bound_asset_id, source_asset_name: row.source_name, target_asset_id: row.target_asset_id, target_asset_name: row.target_name, control_point: row.control_point, operation: row.operation, target_capabilities: targetCapabilities, valid: false, actionable: false, reason_code: "BINDING_DISABLED", reason: "Actuation binding is disabled" };
  if (!row.target_asset_id || !row.target_name) return { binding_id: row.binding_id, policy_id: row.policy_id, source_asset_id: row.bound_asset_id, source_asset_name: row.source_name, target_asset_id: row.target_asset_id, target_asset_name: row.target_name, control_point: row.control_point, operation: row.operation, target_capabilities: targetCapabilities, valid: false, actionable: false, reason_code: "TARGET_NOT_FOUND", reason: "Bound target is not available in this project" };
  if (!row.target_type || !["actuator", "relay_module", "programmable_node"].includes(row.target_type) || row.target_status === "retired") return { binding_id: row.binding_id, policy_id: row.policy_id, source_asset_id: row.bound_asset_id, source_asset_name: row.source_name, target_asset_id: row.target_asset_id, target_asset_name: row.target_name, control_point: row.control_point, operation: row.operation, target_capabilities: targetCapabilities, valid: false, actionable: false, reason_code: "TARGET_NOT_ELIGIBLE", reason: "Target is not an eligible active simulated actuation target" };
  if (row.bound_asset_id === row.target_asset_id && row.target_type !== "programmable_node") return { binding_id: row.binding_id, policy_id: row.policy_id, source_asset_id: row.bound_asset_id, source_asset_name: row.source_name, target_asset_id: row.target_asset_id, target_asset_name: row.target_name, control_point: row.control_point, operation: row.operation, target_capabilities: targetCapabilities, valid: false, actionable: false, reason_code: "SELF_TARGET_NOT_ALLOWED", reason: "Only programmable nodes can be both policy source and actuation target" };
  const capability = targetCapabilities.find((item) => item.key === row.control_point);
  const operations = capability?.operations;
  if (!capability || !Array.isArray(operations) || !operations.includes(row.operation)) return { binding_id: row.binding_id, policy_id: row.policy_id, source_asset_id: row.bound_asset_id, source_asset_name: row.source_name, target_asset_id: row.target_asset_id, target_asset_name: row.target_name, control_point: row.control_point, operation: row.operation, target_capabilities: targetCapabilities, valid: false, actionable: false, reason_code: "UNSUPPORTED_TARGET_CAPABILITY", reason: "Target control point does not support the bound operation" };
  return { binding_id: row.binding_id, policy_id: row.policy_id, source_asset_id: row.bound_asset_id, source_asset_name: row.source_name, target_asset_id: row.target_asset_id, target_asset_name: row.target_name, control_point: row.control_point, operation: row.operation, target_capabilities: targetCapabilities, valid: true, actionable: true, reason_code: null, reason: null };
}

function deliveryStatus(status: string): ControlOperationalStatus {
  if (["received", "validated", "ready_to_dispatch", "dispatched"].includes(status)) return "PENDING";
  if (status === "retry_pending") return "RETRYING";
  if (status === "acknowledged") return "ACKNOWLEDGED";
  if (status === "expired") return "EXPIRED";
  if (["failed_final", "rejected"].includes(status)) return "FAILED";
  return "PENDING";
}

function outboxStatus(status: string | null): ControlOperationalStatus | null {
  if (!status) return null;
  if (status === "published") return "PUBLISHED";
  if (status === "failed") return "FAILED";
  return "PENDING";
}

export class ControlOperationsService {
  private readonly operationsRepo: Pick<ControlOperationsRepository, "findPolicies" | "findRecommendations" | "findDeliveries" | "getMetrics">;
  private readonly projectRepo: Pick<IProjectRepository, "findById">;

  constructor(deps: ControlOperationsServiceDeps = {}) {
    this.operationsRepo = deps.operationsRepo ?? new ControlOperationsRepository();
    this.projectRepo = deps.projectRepo ?? new ProjectRepository();
  }

  async getSummary(actor: ControlActor, projectId: string): Promise<ProjectControlOperationsSummary> {
    const project = await this.authorize(actor, projectId);
    const [policyRows, metrics, attentionDeliveries] = await Promise.all([
      this.operationsRepo.findPolicies(projectId), this.operationsRepo.getMetrics(projectId),
      this.operationsRepo.findDeliveries(projectId, { limit: MAX_LIMIT, offset: 0 })
    ]);
    const policies = policyRows.map((row) => this.toPolicy(row, project.parametric_control_enabled, []));
    const bindings = policyRows.map(bindingView).filter((item): item is BindingOperationalView => item !== null);
    const attention = this.attention(policies, bindings, attentionDeliveries);
    const deliverySummary = this.emptyDeliverySummary();
    for (const [status, count] of Object.entries(metrics.delivery_counts)) deliverySummary[deliveryStatus(status)] += Number(count);
    return {
      project: { id: project.id, name: project.name, parametric_control_enabled: project.parametric_control_enabled },
      control_enabled: project.parametric_control_enabled,
      control_mode: project.parametric_control_enabled ? "SIMULATED" : "INACTIVE",
      policy_summary: { total: policies.length, enabled: policies.filter((item) => item.enabled).length, actionable: policies.filter((item) => item.actionability === "ACTIONABLE").length, recommendation_only: policies.filter((item) => item.recommendation_only).length, misconfigured: policies.filter((item) => item.actionability === "MISCONFIGURED").length },
      binding_summary: { total: bindings.length, actionable: bindings.filter((item) => item.actionable).length, invalid: bindings.filter((item) => !item.valid).length },
      recommendation_summary: { total: metrics.recommendation_total, last_at: metrics.last_recommendation_at },
      delivery_summary: deliverySummary,
      attention_summary: { total: attention.length, warnings: attention.filter((item) => item.severity === "warning").length, errors: attention.filter((item) => item.severity === "error").length },
      last_activity_at: metrics.last_activity_at
    };
  }

  async listPolicies(actor: ControlActor, projectId: string, input: OperationsPageInput = {}): Promise<ControlOperationsPage<PolicyOperationalView>> {
    const project = await this.authorize(actor, projectId);
    const pagination = page(input);
    const [rows, recommendations] = await Promise.all([this.operationsRepo.findPolicies(projectId, pagination), this.operationsRepo.findRecommendations(projectId, { limit: MAX_LIMIT, offset: 0 })]);
    return { ...pagination, items: rows.map((row) => this.toPolicy(row, project.parametric_control_enabled, recommendations)) };
  }

  async listBindings(actor: ControlActor, projectId: string, input: OperationsPageInput = {}): Promise<ControlOperationsPage<BindingOperationalView>> {
    await this.authorize(actor, projectId);
    const pagination = page(input);
    return { ...pagination, items: (await this.operationsRepo.findPolicies(projectId, pagination)).map(bindingView).filter((item): item is BindingOperationalView => item !== null) };
  }

  async listRecommendations(actor: ControlActor, projectId: string, input: OperationsPageInput & { policyId?: string; correlationId?: string }): Promise<ControlOperationsPage<RecommendationOperationalView>> {
    await this.authorize(actor, projectId);
    const pagination = page(input);
    const rows = await this.operationsRepo.findRecommendations(projectId, { ...pagination, policyId: input.policyId, correlationId: input.correlationId });
    const deliveries = await this.operationsRepo.findDeliveries(projectId, { limit: MAX_LIMIT, offset: 0 });
    return { ...pagination, items: rows.map((row) => this.toRecommendation(row, deliveries)) };
  }

  async listDeliveries(actor: ControlActor, projectId: string, input: OperationsPageInput & { status?: string; recommendationId?: string; commandId?: string; correlationId?: string }): Promise<ControlOperationsPage<DeliveryOperationalView>> {
    await this.authorize(actor, projectId);
    const pagination = page(input);
    const rows = await this.operationsRepo.findDeliveries(projectId, { ...pagination, status: input.status, recommendationId: input.recommendationId, commandId: input.commandId, correlationId: input.correlationId });
    return { ...pagination, items: rows.map(this.toDelivery) };
  }

  async listAttention(actor: ControlActor, projectId: string): Promise<OperationalAttentionItem[]> {
    const project = await this.authorize(actor, projectId);
    const [rows, deliveries] = await Promise.all([this.operationsRepo.findPolicies(projectId), this.operationsRepo.findDeliveries(projectId, { limit: MAX_LIMIT, offset: 0 })]);
    const policies = rows.map((row) => this.toPolicy(row, project.parametric_control_enabled, []));
    const bindings = rows.map(bindingView).filter((item): item is BindingOperationalView => item !== null);
    return this.attention(policies, bindings, deliveries);
  }

  private async authorize(actor: ControlActor, projectId: string) {
    assertControlPermission(actor, "view_dashboard", projectId);
    const project = await this.projectRepo.findById(projectId);
    if (!project) throw new NotFoundError("Project not found");
    return project;
  }

  private toPolicy(row: ControlOperationsPolicyRecord, controlEnabled: boolean, recommendations: ControlOperationsRecommendationRecord[]): PolicyOperationalView {
    const binding = bindingView(row);
    const lastRecommendation = recommendations.find((item) => item.policy_id === row.policy_id)?.created_at ?? null;
    if (!controlEnabled || !row.enabled) return { policy_id: row.policy_id, project_id: row.project_id, variable: row.variable, enabled: row.enabled, configured_status: row.enabled ? "ENABLED" : "DISABLED", effective_status: "INACTIVE", reason_code: !controlEnabled ? "PROJECT_CONTROL_DISABLED" : "POLICY_DISABLED", reason: !controlEnabled ? "Project control is disabled" : "Policy is disabled", source_asset_id: row.bound_asset_id, source_asset_name: row.source_name, target_asset_id: binding?.target_asset_id ?? null, target_asset_name: binding?.target_asset_name ?? null, operation: binding?.operation ?? null, binding_status: binding ? (binding.valid ? "VALID" : "INVALID") : "NONE", actionability: "INACTIVE", recommendation_only: false, recommendation_only_reason: null, last_evaluation_at: null, last_recommendation_at: lastRecommendation };
    if (!binding) return { policy_id: row.policy_id, project_id: row.project_id, variable: row.variable, enabled: true, configured_status: "ENABLED", effective_status: "RECOMMENDATION_ONLY", reason_code: "NO_VALID_ACTUATION_TARGET", reason: "Policy has no actuation binding and remains recommendation-only", source_asset_id: row.bound_asset_id, source_asset_name: row.source_name, target_asset_id: null, target_asset_name: null, operation: null, binding_status: "NONE", actionability: "RECOMMENDATION_ONLY", recommendation_only: true, recommendation_only_reason: "NO_VALID_ACTUATION_TARGET", last_evaluation_at: null, last_recommendation_at: lastRecommendation };
    if (!binding.valid) return { policy_id: row.policy_id, project_id: row.project_id, variable: row.variable, enabled: true, configured_status: "ENABLED", effective_status: "MISCONFIGURED", reason_code: binding.reason_code, reason: binding.reason, source_asset_id: row.bound_asset_id, source_asset_name: row.source_name, target_asset_id: binding.target_asset_id, target_asset_name: binding.target_asset_name, operation: binding.operation, binding_status: "INVALID", actionability: "MISCONFIGURED", recommendation_only: false, recommendation_only_reason: null, last_evaluation_at: null, last_recommendation_at: lastRecommendation };
    return { policy_id: row.policy_id, project_id: row.project_id, variable: row.variable, enabled: true, configured_status: "ENABLED", effective_status: "HEALTHY", reason_code: null, reason: null, source_asset_id: row.bound_asset_id, source_asset_name: row.source_name, target_asset_id: binding.target_asset_id, target_asset_name: binding.target_asset_name, operation: binding.operation, binding_status: "VALID", actionability: "ACTIONABLE", recommendation_only: false, recommendation_only_reason: null, last_evaluation_at: null, last_recommendation_at: lastRecommendation };
  }

  private toRecommendation = (row: ControlOperationsRecommendationRecord, deliveries: ControlOperationsDeliveryRecord[]): RecommendationOperationalView => {
    const delivery = deliveries.find((item) => (row.recommendation_id && item.recommendation_id === row.recommendation_id) || (!row.recommendation_id && row.correlation_id && item.correlation_id === row.correlation_id));
    return { ...row, audit_id: row.audit_id, recommendation_id: row.recommendation_id, correlation_id: row.correlation_id, project_id: row.project_id, policy_id: row.policy_id, source_asset_id: row.source_asset_id, target_asset_id: row.target_asset_id, created_at: row.created_at, status: "RECOMMENDED", delivery_intent_id: delivery?.delivery_intent_id ?? null, command_id: delivery?.command_id ?? null, summary: row.summary };
  };

  private toDelivery = (row: ControlOperationsDeliveryRecord): DeliveryOperationalView => ({ ...row, intent_status: deliveryStatus(row.intent_status), outbox_status: outboxStatus(row.outbox_status), ack_status: row.intent_status === "acknowledged" ? "ACKNOWLEDGED" : null, event_id: row.event_id });

  private attention(policies: PolicyOperationalView[], bindings: BindingOperationalView[], deliveries: ControlOperationsDeliveryRecord[]): OperationalAttentionItem[] {
    const items: OperationalAttentionItem[] = [];
    for (const binding of bindings.filter((item) => !item.valid)) items.push({ severity: "error", category: "BINDING", entity_type: "binding", entity_id: binding.binding_id, message: binding.reason ?? "Invalid actuation binding", detected_at: new Date().toISOString(), action_hint: "Correct the target capability or binding configuration" });
    for (const policy of policies.filter((item) => item.effective_status === "MISCONFIGURED" && !item.reason_code?.includes("BINDING"))) items.push({ severity: "error", category: "BINDING", entity_type: "policy", entity_id: policy.policy_id, message: policy.reason ?? "Policy is misconfigured", detected_at: new Date().toISOString(), action_hint: "Review the policy source and target binding" });
    for (const delivery of deliveries) {
      const status = deliveryStatus(delivery.intent_status);
      if (status === "RETRYING" || status === "FAILED" || status === "EXPIRED") items.push({ severity: status === "RETRYING" ? "warning" : "error", category: "DELIVERY", entity_type: "delivery", entity_id: delivery.delivery_intent_id, message: status === "RETRYING" ? "Delivery is retrying" : `Delivery is ${status.toLowerCase()}`, detected_at: delivery.updated_at, action_hint: status === "RETRYING" ? "Observe the bounded retry lifecycle" : "Review delivery error and audited recovery procedure" });
      if (delivery.outbox_status === "failed") items.push({ severity: "error", category: "OUTBOX", entity_type: "outbox", entity_id: delivery.event_id ?? delivery.command_id, message: "Outbox publication failed", detected_at: delivery.updated_at, action_hint: "Review broker condition and reset only through the audited recovery procedure" });
    }
    return items;
  }

  private emptyDeliverySummary(): Record<ControlOperationalStatus, number> { return { HEALTHY: 0, INACTIVE: 0, RECOMMENDATION_ONLY: 0, PENDING: 0, PUBLISHED: 0, ACKNOWLEDGED: 0, RETRYING: 0, FAILED: 0, EXPIRED: 0, MISCONFIGURED: 0 }; }
}
