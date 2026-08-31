import { canonicalClone, experimentFingerprint, sha256Canonical } from "@/lib/simulation/canonical";
import type { ControlStrategyCandidate } from "@/lib/dto/strategy-candidate.dto";
import type { ExperimentBatchItemStatus, ExperimentBatchStatus } from "@/lib/dto/experiment-batch.dto";
import type { SimulationReadyMaterial, SimulationSession } from "@/lib/dto/simulation-session.dto";
import { ConflictError, ValidationError } from "@/lib/errors/domain-errors";

export function deriveBatchStatus(items: Array<{ status: ExperimentBatchItemStatus }>): ExperimentBatchStatus {
  const statuses = items.map((item) => item.status); if (statuses.includes("RUNNING")) return "RUNNING";
  if (statuses.includes("PENDING")) return "READY";
  const failed = statuses.filter((status) => status === "FAILED").length;
  if (failed === statuses.length) return "FAILED";
  if (failed > 0) return "PARTIALLY_FAILED";
  if (statuses.some((status) => status === "COMPLETED_WITH_WARNINGS" || status === "NOT_EVALUABLE")) return "COMPLETED_WITH_WARNINGS";
  return "COMPLETED";
}
export function batchHash(input: { projectId: string; searchSpaceHash: string; candidateHashes: string[]; baseFingerprint: string; evaluationProfile: { id: string; version: number } | null }): string {
  return sha256Canonical({ schema_version: 1, orchestrator_version: "experiment-batch-orchestrator:v1", project_id: input.projectId, search_space_hash: input.searchSpaceHash, candidate_hashes: input.candidateHashes, base_experiment_fingerprint: input.baseFingerprint, evaluation_profile: input.evaluationProfile });
}
export function candidateToExperimentConfiguration(base: SimulationSession, candidate: ControlStrategyCandidate): SimulationReadyMaterial {
  if (base.status !== "READY" || !base.policy_snapshot || !base.topology_snapshot || !base.dataset_snapshot || !base.configuration_snapshot || !base.experiment_fingerprint) throw new ConflictError("Batch base session must be a complete READY simulation session");
  const policy = base.policy_snapshot.policy;
  if (!policy || typeof policy !== "object" || Array.isArray(policy) || (policy as Record<string, unknown>).policy_type !== candidate.strategy_type) throw new ValidationError("CANDIDATE_INVALID: strategy is incompatible with frozen simulation controller");
  const policyRecord = policy as Record<string, unknown>; const params = policyRecord.params;
  if (!params || typeof params !== "object" || Array.isArray(params)) throw new ValidationError("CANDIDATE_INVALID: frozen policy parameters are missing");
  const allowed = candidate.strategy_type === "proportional" ? ["gain", "setpoint_value", "deadband", "min_action", "max_action"] : ["tolerance", "increase_step", "decrease_step", "hold_signal"];
  if (Object.keys(candidate.parameters).some((key) => !allowed.includes(key))) throw new ValidationError("CANDIDATE_INVALID: unsupported parameter for frozen controller");
  const policy_snapshot = canonicalClone({ ...base.policy_snapshot, policy: { ...policyRecord, params: { ...(params as Record<string, unknown>), ...candidate.parameters } } });
  const topology_snapshot = canonicalClone(base.topology_snapshot); const dataset_snapshot = canonicalClone(base.dataset_snapshot); const configuration_snapshot = canonicalClone(base.configuration_snapshot);
  const policy_snapshot_hash = sha256Canonical(policy_snapshot); const topology_snapshot_hash = sha256Canonical(topology_snapshot); const dataset_snapshot_hash = sha256Canonical(dataset_snapshot); const configuration_snapshot_hash = sha256Canonical(configuration_snapshot);
  return { policy_snapshot, topology_snapshot, dataset_snapshot, configuration_snapshot, policy_snapshot_hash, topology_snapshot_hash, dataset_snapshot_hash, configuration_snapshot_hash, experiment_fingerprint: experimentFingerprint({ policy_snapshot_hash, topology_snapshot_hash, dataset_snapshot_hash, configuration_snapshot_hash }), snapshot_schema_version: 1 };
}
