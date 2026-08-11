import type {
  ControlPolicy,
  ControlPolicyConflict,
  ControlPolicyPreviewCandidate,
  ControlPolicyPreviewResponse
} from "@/lib/dto/control-policy.dto";

type PolicyLike = Pick<
  ControlPolicy,
  "id" | "project_id" | "variable" | "binding" | "context_selector" | "priority" | "enabled" | "version" | "created_at" | "updated_at"
>;

function normalizeJsonValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(normalizeJsonValue);
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, nestedValue]) => [key, normalizeJsonValue(nestedValue)])
    );
  }
  return value;
}

export function stableJsonStringify(value: unknown): string {
  return JSON.stringify(normalizeJsonValue(value));
}

export function hasExactContextSelector(left: Record<string, unknown>, right: Record<string, unknown>) {
  return stableJsonStringify(left) === stableJsonStringify(right);
}

export function matchesRequiredContext(required: Record<string, unknown>, actual: Record<string, unknown>) {
  return Object.entries(required).every(([key, value]) => actual[key] === value);
}

export function hasSameStructuralBinding(
  left: Pick<ControlPolicy, "binding">,
  right: Pick<ControlPolicy, "binding">
) {
  return left.binding?.asset_id === right.binding?.asset_id;
}

export function selectBindingEligiblePolicies(policies: ControlPolicy[], assetId?: string) {
  const bound = assetId
    ? policies.filter((policy) => policy.binding?.asset_id === assetId)
    : [];
  return bound.length > 0 ? bound : policies.filter((policy) => !policy.binding);
}

function compareSelectionRank(left: PolicyLike, right: PolicyLike) {
  if (left.priority !== right.priority) {
    return left.priority - right.priority;
  }
  return left.version - right.version;
}

function compareSelectionRankValues(left: { priority: number; version: number }, right: { priority: number; version: number }) {
  if (left.priority !== right.priority) {
    return left.priority - right.priority;
  }
  return left.version - right.version;
}

function compareSourceOrder(left: PolicyLike, right: PolicyLike) {
  if (left.priority !== right.priority) {
    return right.priority - left.priority;
  }
  if (left.version !== right.version) {
    return right.version - left.version;
  }
  if (left.updated_at !== right.updated_at) {
    return right.updated_at.localeCompare(left.updated_at);
  }
  if (left.created_at !== right.created_at) {
    return right.created_at.localeCompare(left.created_at);
  }
  return left.id.localeCompare(right.id);
}

export function toPreviewPolicy(
  candidate: ControlPolicyPreviewCandidate,
  timestamps?: { created_at?: string; updated_at?: string }
): ControlPolicy {
  const now = timestamps?.updated_at ?? new Date().toISOString();
  return {
    id: candidate.id ?? "preview-candidate",
    project_id: candidate.project_id,
    variable: candidate.variable,
    binding: candidate.binding ?? null,
    context_selector: candidate.context_selector,
    policy_type: candidate.policy_type,
    params: candidate.params,
    priority: candidate.priority,
    enabled: candidate.enabled,
    version: candidate.version ?? 1,
    created_at: timestamps?.created_at ?? now,
    updated_at: now
  };
}

export function detectPolicyConflicts(
  candidate: ControlPolicyPreviewCandidate,
  existingPolicies: ControlPolicy[]
): ControlPolicyConflict[] {
  if (!candidate.enabled) {
    return [];
  }

  const exactPeers = existingPolicies.filter((policy) => (
    policy.enabled &&
    policy.project_id === candidate.project_id &&
    policy.variable === candidate.variable &&
    hasSameStructuralBinding(policy, candidate) &&
    policy.id !== candidate.id &&
    hasExactContextSelector(policy.context_selector, candidate.context_selector)
  ));

  if (exactPeers.length === 0) {
    return [];
  }

  const conflicts: ControlPolicyConflict[] = [];
  const candidateRank = { priority: candidate.priority, version: candidate.version ?? 1 };
  const selectionTies = exactPeers.filter((policy) => (
    policy.priority === candidateRank.priority &&
    policy.version === candidateRank.version
  ));

  if (selectionTies.length > 0) {
    conflicts.push({
      type: "selection_tie",
      severity: "error",
      message: "Existe al menos una policy enabled con mismo project_id, variable, context_selector, priority y version.",
      conflicting_policy_ids: selectionTies.map((policy) => policy.id)
    });
  }

  const higherRanked = exactPeers.filter((policy) => compareSelectionRankValues(policy, candidateRank) > 0);
  if (higherRanked.length > 0) {
    conflicts.push({
      type: "shadowed_by_enabled_policy",
      severity: "warning",
      message: "La policy candidata quedaría sombreada por otra policy enabled de mismo scope exacto con mayor priority/version.",
      conflicting_policy_ids: higherRanked.map((policy) => policy.id)
    });
  }

  const lowerRanked = exactPeers.filter((policy) => compareSelectionRankValues(policy, candidateRank) < 0);
  if (lowerRanked.length > 0) {
    conflicts.push({
      type: "shadows_enabled_policy",
      severity: "warning",
      message: "La policy candidata desplazaría a otras policies enabled de mismo scope exacto con menor priority/version.",
      conflicting_policy_ids: lowerRanked.map((policy) => policy.id)
    });
  }

  return conflicts;
}

export function selectPolicyForContext(
  policies: ControlPolicy[],
  context: Record<string, unknown>,
  assetId?: string
) {
  const matchingCandidates = selectBindingEligiblePolicies(policies, assetId)
    .filter((policy) => policy.enabled)
    .filter((policy) => matchesRequiredContext(policy.context_selector, context));

  const sourceOrdered = [...matchingCandidates].sort(compareSourceOrder);

  let selected: ControlPolicy | null = null;
  let selectedKey: [number, number, number] | null = null;

  for (const policy of sourceOrdered) {
    const candidateKey: [number, number, number] = [
      Object.keys(policy.context_selector).length,
      policy.priority,
      policy.version
    ];

    if (
      !selectedKey ||
      candidateKey[0] > selectedKey[0] ||
      (candidateKey[0] === selectedKey[0] && candidateKey[1] > selectedKey[1]) ||
      (candidateKey[0] === selectedKey[0] && candidateKey[1] === selectedKey[1] && candidateKey[2] > selectedKey[2])
    ) {
      selected = policy;
      selectedKey = candidateKey;
    }
  }

  return {
    selected,
    matchingCandidates: sourceOrdered
  };
}

export function buildPreviewResponse(args: {
  project_id: string;
  variable: string;
  context: Record<string, unknown>;
  asset_id?: string;
  existingPolicies: ControlPolicy[];
  candidate?: ControlPolicyPreviewCandidate;
}): ControlPolicyPreviewResponse {
  const scopedPolicies = args.existingPolicies.filter((policy) => (
    policy.project_id === args.project_id &&
    policy.variable === args.variable
  ));

  const currentSelection = selectPolicyForContext(scopedPolicies, args.context, args.asset_id);
  const conflicts = args.candidate ? detectPolicyConflicts(args.candidate, scopedPolicies) : [];

  const hypotheticalPolicies = args.candidate
    ? [
        ...scopedPolicies.filter((policy) => policy.id !== args.candidate?.id),
        toPreviewPolicy(args.candidate)
      ]
    : scopedPolicies;

  const hypotheticalSelection = selectPolicyForContext(hypotheticalPolicies, args.context, args.asset_id);

  const warnings = conflicts.map((conflict) => conflict.message);
  if (args.candidate?.enabled && hypotheticalSelection.selected?.id !== (args.candidate.id ?? "preview-candidate")) {
    warnings.push("La policy candidata no sería seleccionada para este contexto de preview.");
  }

  return {
    current_selected_policy: currentSelection.selected,
    hypothetical_selected_policy: hypotheticalSelection.selected,
    candidate_would_be_selected: hypotheticalSelection.selected?.id === (args.candidate?.id ?? "preview-candidate"),
    matching_policy_ids: currentSelection.matchingCandidates.map((policy) => policy.id),
    hypothetical_matching_policy_ids: hypotheticalSelection.matchingCandidates.map((policy) => policy.id),
    conflicts,
    warnings
  };
}
