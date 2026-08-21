import { assertControlPermission } from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import type { CreateSimulationSessionInput, PrepareSimulationSessionInput, SimulationReadyMaterial, SimulationSession, SimulationTelemetryRecord } from "@/lib/dto/simulation-session.dto";
import { ConflictError, NotFoundError, ValidationError } from "@/lib/errors/domain-errors";
import type { IProjectRepository } from "@/lib/repositories/contracts";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import { SimulationSessionRepository, type SimulationSnapshotSource } from "@/lib/repositories/simulation-session.repository";
import { canonicalClone, experimentFingerprint, normalizeTimestamp, sha256Canonical } from "@/lib/simulation/canonical";

interface SimulationSessionServiceDeps {
  sessionRepo?: Pick<SimulationSessionRepository, "create" | "findByProjectAndId" | "listByProject" | "prepare">;
  projectRepo?: Pick<IProjectRepository, "findById">;
}

export class SimulationSessionService {
  private readonly sessionRepo: Pick<SimulationSessionRepository, "create" | "findByProjectAndId" | "listByProject" | "prepare">;
  private readonly projectRepo: Pick<IProjectRepository, "findById">;

  constructor(deps: SimulationSessionServiceDeps = {}) {
    this.sessionRepo = deps.sessionRepo ?? new SimulationSessionRepository();
    this.projectRepo = deps.projectRepo ?? new ProjectRepository();
  }

  async create(actor: ControlActor, projectId: string, input: CreateSimulationSessionInput): Promise<SimulationSession> {
    await this.authorize(actor, projectId, "edit_policies");
    return this.sessionRepo.create(projectId, actor.actor_id ?? actor.user_id, input);
  }

  async get(actor: ControlActor, projectId: string, sessionId: string): Promise<SimulationSession> {
    await this.authorize(actor, projectId, "view_dashboard");
    const session = await this.sessionRepo.findByProjectAndId(projectId, sessionId);
    if (!session) throw new NotFoundError("Simulation session not found");
    return session;
  }

  async list(actor: ControlActor, projectId: string): Promise<SimulationSession[]> {
    await this.authorize(actor, projectId, "view_dashboard");
    return this.sessionRepo.listByProject(projectId);
  }

  async prepare(actor: ControlActor, projectId: string, sessionId: string, input: PrepareSimulationSessionInput): Promise<SimulationSession> {
    await this.authorize(actor, projectId, "edit_policies");
    const normalizedRecords = this.normalizeRecords(projectId, input.dataset.records);
    return this.sessionRepo.prepare(projectId, sessionId, input.policy_id, actor.actor_id ?? actor.user_id, (source) => {
      if (source.project_id !== projectId) throw new NotFoundError("Control policy not found in project scope");
      if (!source.source_asset_id) throw new ConflictError("Control policy has no project-scoped source asset");
      if (normalizedRecords.some((record) => record.variable !== source.variable)) {
        throw new ValidationError("Dataset variables must match the prepared control policy variable");
      }
      return this.buildReadyMaterial(source, input, normalizedRecords);
    });
  }

  private normalizeRecords(projectId: string, records: SimulationTelemetryRecord[]): SimulationTelemetryRecord[] {
    const eventIds = new Set<string>();
    const normalized = records.map((record) => {
      if (record.project_id !== projectId) throw new ValidationError("Dataset event belongs to a different project");
      if (eventIds.has(record.event_id)) throw new ValidationError("Dataset event_id must be unique within a snapshot");
      eventIds.add(record.event_id);
      return { ...record, timestamp: normalizeTimestamp(record.timestamp) };
    });
    return normalized.sort((left, right) => left.timestamp.localeCompare(right.timestamp) || left.event_id.localeCompare(right.event_id));
  }

  private buildReadyMaterial(
    source: SimulationSnapshotSource,
    input: PrepareSimulationSessionInput,
    records: SimulationTelemetryRecord[]
  ): SimulationReadyMaterial {
    const policySnapshot = {
      schema_version: 1,
      policy: {
        id: source.policy_id, project_id: source.project_id, variable: source.variable,
        context_selector: source.context_selector, policy_type: source.policy_type, params: source.params,
        priority: source.priority, enabled: source.enabled, version: source.policy_version,
        source_asset_id: source.source_asset_id
      }
    };
    const topologySnapshot = {
      schema_version: 1,
      source_asset: {
        id: source.source_asset_id, asset_type: source.source_asset_type, status: source.source_asset_status,
        metadata: source.source_asset_metadata
      },
      actuation_binding: source.binding_id ? {
        id: source.binding_id, enabled: source.binding_enabled, version: source.binding_version,
        target_asset_id: source.target_asset_id, control_point: source.control_point, operation: source.operation
      } : null,
      target_asset: source.target_asset_id ? {
        id: source.target_asset_id, asset_type: source.target_asset_type, status: source.target_asset_status,
        metadata: source.target_asset_metadata
      } : null
    };
    const datasetSnapshot = {
      schema_version: 1,
      source_kind: input.dataset.source_kind,
      ordering: "timestamp_ascending_event_id",
      records
    };
    const configurationSnapshot = {
      schema_version: 1,
      execution_context: "SIMULATION",
      engine: { name: "parametric-control-engine", version: "0.1.0" },
      clock: {
        model_type: "SIMULATION_CLOCK", model_version: "1",
        initial_virtual_time: normalizeTimestamp(input.configuration.initial_virtual_time ?? records[0].timestamp)
      },
      evaluation_options: { include_trace: input.configuration.evaluation_options?.include_trace ?? true },
      random_seed: input.configuration.random_seed ?? null,
      operational_side_effects: { outbox: false, transport: false, physical_effects: false }
    };
    const snapshots = {
      policy_snapshot: canonicalClone(policySnapshot), topology_snapshot: canonicalClone(topologySnapshot),
      dataset_snapshot: canonicalClone(datasetSnapshot), configuration_snapshot: canonicalClone(configurationSnapshot)
    };
    const componentHashes = {
      policy_snapshot_hash: sha256Canonical(snapshots.policy_snapshot),
      topology_snapshot_hash: sha256Canonical(snapshots.topology_snapshot),
      dataset_snapshot_hash: sha256Canonical(snapshots.dataset_snapshot),
      configuration_snapshot_hash: sha256Canonical(snapshots.configuration_snapshot)
    };
    return {
      ...snapshots, ...componentHashes,
      experiment_fingerprint: experimentFingerprint(componentHashes), snapshot_schema_version: 1
    };
  }

  private async authorize(actor: ControlActor, projectId: string, permission: "edit_policies" | "view_dashboard") {
    assertControlPermission(actor, permission, projectId);
    if (!await this.projectRepo.findById(projectId)) throw new NotFoundError("Project not found");
  }
}
