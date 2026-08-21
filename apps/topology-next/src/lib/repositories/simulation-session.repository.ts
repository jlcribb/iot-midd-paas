import type { QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";
import { withTransaction, type SqlExecutor, type TransactionRunner } from "@/lib/db/tx";
import { ConflictError, NotFoundError } from "@/lib/errors/domain-errors";
import type { CreateSimulationSessionInput, SimulationReadyMaterial, SimulationSession } from "@/lib/dto/simulation-session.dto";

function asObject(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

export interface SimulationSnapshotSource {
  policy_id: string;
  project_id: string;
  variable: string;
  context_selector: Record<string, unknown>;
  policy_type: string;
  params: Record<string, unknown>;
  priority: number;
  enabled: boolean;
  policy_version: number;
  source_asset_id: string | null;
  source_asset_type: string | null;
  source_asset_status: string | null;
  source_asset_metadata: Record<string, unknown>;
  binding_id: string | null;
  binding_enabled: boolean | null;
  binding_version: number | null;
  target_asset_id: string | null;
  target_asset_type: string | null;
  target_asset_status: string | null;
  target_asset_metadata: Record<string, unknown>;
  control_point: string | null;
  operation: string | null;
}

function mapSession(row: QueryResultRow): SimulationSession {
  return {
    id: String(row.id),
    project_id: String(row.project_id),
    execution_context: "SIMULATION",
    status: row.status as SimulationSession["status"],
    created_by: String(row.created_by),
    snapshot_refs: (row.snapshot_refs ?? {}) as Record<string, unknown>,
    metadata: (row.metadata ?? {}) as Record<string, unknown>,
    created_at: String(row.created_at),
    started_at: row.started_at ? String(row.started_at) : null,
    completed_at: row.completed_at ? String(row.completed_at) : null,
    prepared_at: row.prepared_at ? String(row.prepared_at) : null,
    policy_snapshot: row.policy_snapshot ? asObject(row.policy_snapshot) : null,
    topology_snapshot: row.topology_snapshot ? asObject(row.topology_snapshot) : null,
    dataset_snapshot: row.dataset_snapshot ? asObject(row.dataset_snapshot) : null,
    configuration_snapshot: row.configuration_snapshot ? asObject(row.configuration_snapshot) : null,
    policy_snapshot_hash: row.policy_snapshot_hash ? String(row.policy_snapshot_hash) : null,
    topology_snapshot_hash: row.topology_snapshot_hash ? String(row.topology_snapshot_hash) : null,
    dataset_snapshot_hash: row.dataset_snapshot_hash ? String(row.dataset_snapshot_hash) : null,
    configuration_snapshot_hash: row.configuration_snapshot_hash ? String(row.configuration_snapshot_hash) : null,
    experiment_fingerprint: row.experiment_fingerprint ? String(row.experiment_fingerprint) : null,
    snapshot_schema_version: row.snapshot_schema_version === null || row.snapshot_schema_version === undefined ? null : Number(row.snapshot_schema_version)
  };
}

export class SimulationSessionRepository {
  constructor(
    private readonly db: SqlExecutor = pool,
    private readonly transaction: TransactionRunner = withTransaction
  ) {}

  async create(projectId: string, createdBy: string, input: CreateSimulationSessionInput): Promise<SimulationSession> {
    const result = await this.db.query(
      `INSERT INTO public.control_simulation_sessions
        (project_id, execution_context, status, created_by, snapshot_refs, metadata)
       VALUES ($1::uuid, 'SIMULATION', 'DRAFT', $2, $3::jsonb, $4::jsonb)
       RETURNING *`,
      [projectId, createdBy, JSON.stringify(input.snapshot_refs ?? {}), JSON.stringify(input.metadata ?? {})]
    );
    return mapSession(result.rows[0]);
  }

  async findByProjectAndId(projectId: string, sessionId: string): Promise<SimulationSession | null> {
    const result = await this.db.query(
      "SELECT * FROM public.control_simulation_sessions WHERE project_id = $1::uuid AND id = $2::uuid",
      [projectId, sessionId]
    );
    return result.rows[0] ? mapSession(result.rows[0]) : null;
  }

  async listByProject(projectId: string): Promise<SimulationSession[]> {
    const result = await this.db.query(
      "SELECT * FROM public.control_simulation_sessions WHERE project_id = $1::uuid ORDER BY created_at DESC, id DESC",
      [projectId]
    );
    return result.rows.map(mapSession);
  }

  async prepare(
    projectId: string,
    sessionId: string,
    policyId: string,
    preparedBy: string,
    buildMaterial: (source: SimulationSnapshotSource) => SimulationReadyMaterial
  ): Promise<SimulationSession> {
    return this.transaction(async (tx) => {
      const sessionResult = await tx.query(
        "SELECT * FROM public.control_simulation_sessions WHERE project_id = $1::uuid AND id = $2::uuid FOR UPDATE",
        [projectId, sessionId]
      );
      if (!sessionResult.rows[0]) throw new NotFoundError("Simulation session not found");
      const session = mapSession(sessionResult.rows[0]);
      if (session.status === "READY") return session;
      if (session.status !== "DRAFT") throw new ConflictError("Only DRAFT simulation sessions may be prepared");

      const sourceResult = await tx.query(`
        SELECT p.id::text AS policy_id, p.project_id::text, p.variable, p.context_selector, p.policy_type,
          p.params, p.priority, p.enabled, p.version AS policy_version,
          source.id::text AS source_asset_id, source.asset_type::text AS source_asset_type,
          source.status::text AS source_asset_status, source.metadata AS source_asset_metadata,
          binding.id::text AS binding_id, binding.enabled AS binding_enabled, binding.version AS binding_version,
          binding.target_asset_id::text, target.asset_type::text AS target_asset_type,
          target.status::text AS target_asset_status, target.metadata AS target_asset_metadata,
          binding.control_point, binding.operation
        FROM public.project_control_policies p
        LEFT JOIN public.project_control_policy_actuation_bindings binding
          ON binding.policy_id = p.id AND binding.project_id = p.project_id
        LEFT JOIN public.assets source ON source.id = p.bound_asset_id AND source.project_id = p.project_id
        LEFT JOIN public.assets target ON target.id = binding.target_asset_id AND target.project_id = p.project_id
        WHERE p.project_id = $1::uuid AND p.id = $2::uuid
        FOR SHARE OF p
      `, [projectId, policyId]);
      if (!sourceResult.rows[0]) throw new NotFoundError("Control policy not found in project scope");
      const row = sourceResult.rows[0];
      const source: SimulationSnapshotSource = {
        policy_id: String(row.policy_id), project_id: String(row.project_id), variable: String(row.variable),
        context_selector: asObject(row.context_selector), policy_type: String(row.policy_type), params: asObject(row.params),
        priority: Number(row.priority), enabled: Boolean(row.enabled), policy_version: Number(row.policy_version),
        source_asset_id: row.source_asset_id ? String(row.source_asset_id) : null,
        source_asset_type: row.source_asset_type ? String(row.source_asset_type) : null,
        source_asset_status: row.source_asset_status ? String(row.source_asset_status) : null,
        source_asset_metadata: asObject(row.source_asset_metadata), binding_id: row.binding_id ? String(row.binding_id) : null,
        binding_enabled: row.binding_enabled === null || row.binding_enabled === undefined ? null : Boolean(row.binding_enabled),
        binding_version: row.binding_version === null || row.binding_version === undefined ? null : Number(row.binding_version),
        target_asset_id: row.target_asset_id ? String(row.target_asset_id) : null,
        target_asset_type: row.target_asset_type ? String(row.target_asset_type) : null,
        target_asset_status: row.target_asset_status ? String(row.target_asset_status) : null,
        target_asset_metadata: asObject(row.target_asset_metadata), control_point: row.control_point ? String(row.control_point) : null,
        operation: row.operation ? String(row.operation) : null
      };
      const material = buildMaterial(source);
      const result = await tx.query(`
        UPDATE public.control_simulation_sessions
        SET status = 'READY', prepared_at = NOW(),
          policy_snapshot = $3::jsonb, topology_snapshot = $4::jsonb, dataset_snapshot = $5::jsonb,
          configuration_snapshot = $6::jsonb, policy_snapshot_hash = $7, topology_snapshot_hash = $8,
          dataset_snapshot_hash = $9, configuration_snapshot_hash = $10, experiment_fingerprint = $11,
          snapshot_schema_version = $12
        WHERE project_id = $1::uuid AND id = $2::uuid AND status = 'DRAFT'
        RETURNING *
      `, [projectId, sessionId, JSON.stringify(material.policy_snapshot), JSON.stringify(material.topology_snapshot),
        JSON.stringify(material.dataset_snapshot), JSON.stringify(material.configuration_snapshot), material.policy_snapshot_hash,
        material.topology_snapshot_hash, material.dataset_snapshot_hash, material.configuration_snapshot_hash,
        material.experiment_fingerprint, material.snapshot_schema_version]);
      if (!result.rows[0]) throw new ConflictError("Simulation session changed during preparation");
      await tx.query(
        `INSERT INTO iot_schema.auditoria (entidad, entidad_id, accion, cambios, contexto)
         VALUES ('control_simulation_sessions', $1::uuid, 'SIMULATION_SESSION_PREPARED', $2::jsonb, $3::jsonb)`,
        [sessionId, JSON.stringify({
          status: "READY", snapshot_schema_version: material.snapshot_schema_version,
          experiment_fingerprint: material.experiment_fingerprint,
          component_hashes: {
            policy: material.policy_snapshot_hash, topology: material.topology_snapshot_hash,
            dataset: material.dataset_snapshot_hash, configuration: material.configuration_snapshot_hash
          }
        }), JSON.stringify({
          subsystem: "apps/topology-next", capability: "simulation-preparation", project_id: projectId,
          actor_id: preparedBy, execution_context: "SIMULATION", physical_effects: false
        })]
      );
      return mapSession(result.rows[0]);
    });
  }
}
