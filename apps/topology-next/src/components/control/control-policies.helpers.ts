import type { ControlPolicy, ControlPolicyType } from "@/lib/dto/control-policy.dto";

export interface ControlPolicyDraft {
  params_text: string;
  context_selector_text: string;
  priority: string;
  enabled: boolean;
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
    policy_type: "proportional",
    params_text: defaultParamsText("proportional"),
    context_selector_text: "{}",
    priority: "0",
    enabled: true
  };
}

export function policyToDraft(policy: ControlPolicy): ControlPolicyDraft {
  return {
    params_text: formatPolicyJson(policy.params),
    context_selector_text: formatPolicyJson(policy.context_selector),
    priority: String(policy.priority),
    enabled: policy.enabled
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

  return {
    project_id: projectId,
    variable,
    policy_type: form.policy_type,
    params: parseJsonObject(form.params_text, "params"),
    context_selector: parseJsonObject(form.context_selector_text, "context_selector"),
    priority: parsePriority(form.priority),
    enabled: form.enabled
  };
}

export function buildUpdatePolicyPayload(draft: ControlPolicyDraft) {
  return {
    params: parseJsonObject(draft.params_text, "params"),
    context_selector: parseJsonObject(draft.context_selector_text, "context_selector"),
    priority: parsePriority(draft.priority),
    enabled: draft.enabled
  };
}
