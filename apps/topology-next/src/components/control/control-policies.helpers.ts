import type {
  ControlPolicy,
  ControlPolicyConflict,
  ControlPolicyPreviewResponse,
  ControlPolicyType
} from "@/lib/dto/control-policy.dto";
import { detectPolicyConflicts } from "@/lib/utils/control-policy-governance";

export interface ControlPolicyDraft {
  binding_asset_id: string;
  actuation_target_asset_id: string;
  actuation_control_point: string;
  actuation_operation: "set" | "increase" | "decrease" | "toggle";
  params_text: string;
  context_selector_text: string;
  priority: string;
  enabled: boolean;
  preview_context_text: string;
  preview_asset_id: string;
}

export interface ControlPolicyCreateFormState extends ControlPolicyDraft {
  project_id: string;
  variable: string;
  policy_type: ControlPolicyType;
}

const defaultParamsByType: Record<ControlPolicyType, Record<string, unknown>> = {
  proportional: {
    variable_name: "Tank Level",
    variable_unit: "units",
    actuator_name: "control_output",
    setpoint_value: 70,
    gain: 1,
    deadband: 0,
    min_action: 0,
    max_action: 10
  },
  threshold: {
    variable_name: "Tank Level",
    variable_unit: "units",
    actuator_name: "control_output",
    setpoint_value: 70,
    tolerance: 2,
    increase_step: 1.5,
    decrease_step: 2,
    hold_signal: 0
  }
};

export function formatPolicyJson(value: Record<string, unknown>) {
  return JSON.stringify(value, null, 2);
}

export function defaultParamsText(policyType: ControlPolicyType) {
  return formatPolicyJson(defaultParamsByType[policyType]);
}

export function createEmptyPolicyFormState(): ControlPolicyCreateFormState {
  return {
    project_id: "",
    variable: "",
    binding_asset_id: "",
    actuation_target_asset_id: "",
    actuation_control_point: "",
    actuation_operation: "set",
    policy_type: "proportional",
    params_text: defaultParamsText("proportional"),
    context_selector_text: "{}",
    priority: "0",
    enabled: true,
    preview_context_text: "{}",
    preview_asset_id: ""
  };
}

export function policyToDraft(policy: ControlPolicy): ControlPolicyDraft {
  return {
    binding_asset_id: policy.binding?.asset_id ?? "",
    actuation_target_asset_id: policy.actuation_binding?.target_asset_id ?? "",
    actuation_control_point: policy.actuation_binding?.control_point ?? "",
    actuation_operation: policy.actuation_binding?.operation ?? "set",
    params_text: formatPolicyJson(policy.params),
    context_selector_text: formatPolicyJson(policy.context_selector),
    priority: String(policy.priority),
    enabled: policy.enabled,
    preview_context_text: formatPolicyJson(policy.context_selector),
    preview_asset_id: policy.binding?.asset_id ?? ""
  };
}

function parseJsonObject(value: string, fieldName: string): Record<string, unknown> {
  const trimmed = value.trim();
  if (!trimmed) {
    return {};
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed);
  } catch {
    throw new Error(`${fieldName} must be valid JSON`);
  }

  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error(`${fieldName} must be a JSON object`);
  }

  return parsed as Record<string, unknown>;
}

function parsePriority(value: string) {
  const trimmed = value.trim();
  if (!trimmed) {
    return 0;
  }

  const parsed = Number(trimmed);
  if (!Number.isInteger(parsed) || parsed < 0) {
    throw new Error("priority must be a non-negative integer");
  }
  return parsed;
}

export function buildCreatePolicyPayload(form: ControlPolicyCreateFormState) {
  const projectId = form.project_id.trim();
  const variable = form.variable.trim();

  if (!projectId) {
    throw new Error("project_id is required");
  }

  if (!variable) {
    throw new Error("variable is required");
  }
  if (!form.binding_asset_id) {
    throw new Error("Debes seleccionar una entidad topológica para el binding");
  }

  const actuationBinding = buildActuationBinding(form);
  return {
    project_id: projectId,
    variable,
    binding: {
      asset_id: form.binding_asset_id,
      variable_key: variable
    },
    policy_type: form.policy_type,
    params: parseJsonObject(form.params_text, "params"),
    context_selector: parseJsonObject(form.context_selector_text, "context_selector"),
    priority: parsePriority(form.priority),
    enabled: form.enabled,
    ...(actuationBinding ? { actuation_binding: actuationBinding } : {})
  };
}

export function buildUpdatePolicyPayload(draft: ControlPolicyDraft, variable: string, hadActuationBinding = false) {
  const actuationBinding = buildActuationBinding(draft);
  return {
    ...(draft.binding_asset_id ? { binding: { asset_id: draft.binding_asset_id, variable_key: variable } } : {}),
    params: parseJsonObject(draft.params_text, "params"),
    context_selector: parseJsonObject(draft.context_selector_text, "context_selector"),
    priority: parsePriority(draft.priority),
    enabled: draft.enabled,
    ...(actuationBinding ? { actuation_binding: actuationBinding } : hadActuationBinding ? { actuation_binding: null } : {})
  };
}

function buildActuationBinding(form: Pick<ControlPolicyDraft, "actuation_target_asset_id" | "actuation_control_point" | "actuation_operation">) {
  const targetAssetId = form.actuation_target_asset_id.trim();
  const controlPoint = form.actuation_control_point.trim();
  if (!targetAssetId && !controlPoint) return null;
  if (!targetAssetId || !controlPoint) {
    throw new Error("Para habilitar delivery simulado debes seleccionar target y control point");
  }
  return {
    target_asset_id: targetAssetId,
    control_point: controlPoint,
    operation: form.actuation_operation
  };
}

export function buildPreviewPayload(args: {
  project_id: string;
  variable: string;
  draft: ControlPolicyDraft;
  policy_type: ControlPolicyType;
  policy_id?: string;
  version?: number;
  binding_asset_id?: string;
}) {
  const bindingAssetId = args.binding_asset_id ?? args.draft.binding_asset_id;
  const previewAssetId = args.draft.preview_asset_id || bindingAssetId;
  return {
    project_id: args.project_id,
    variable: args.variable,
    ...(previewAssetId ? { asset_id: previewAssetId } : {}),
    context: parseJsonObject(args.draft.preview_context_text, "preview.context"),
    candidate_policy: {
      id: args.policy_id,
      project_id: args.project_id,
      variable: args.variable,
      binding: bindingAssetId ? { asset_id: bindingAssetId, variable_key: args.variable } : null,
      policy_type: args.policy_type,
      params: parseJsonObject(args.draft.params_text, "params"),
      context_selector: parseJsonObject(args.draft.context_selector_text, "context_selector"),
      priority: parsePriority(args.draft.priority),
      enabled: args.draft.enabled,
      version: args.version
    }
  };
}

export function collectListWarnings(policy: ControlPolicy, policies: ControlPolicy[]): ControlPolicyConflict[] {
  return detectPolicyConflicts(
    {
      id: policy.id,
      project_id: policy.project_id,
      variable: policy.variable,
      binding: policy.binding,
      policy_type: policy.policy_type,
      context_selector: policy.context_selector,
      params: policy.params,
      priority: policy.priority,
      enabled: policy.enabled,
      version: policy.version
    },
    policies
  );
}

export function previewSummaryText(preview: ControlPolicyPreviewResponse | null) {
  if (!preview) {
    return null;
  }

  if (!preview.hypothetical_selected_policy) {
    return "No habría policy seleccionada para ese contexto.";
  }

  return [
    `Seleccionada: ${preview.hypothetical_selected_policy.variable}`,
    `scope=${JSON.stringify(preview.hypothetical_selected_policy.context_selector)}`,
    `priority=${preview.hypothetical_selected_policy.priority}`,
    `version=${preview.hypothetical_selected_policy.version}`
  ].join(" · ");
}
