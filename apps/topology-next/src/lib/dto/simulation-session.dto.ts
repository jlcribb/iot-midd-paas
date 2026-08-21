export type SimulationSessionStatus = "DRAFT" | "READY" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED";

export interface SimulationSession {
  id: string;
  project_id: string;
  execution_context: "SIMULATION";
  status: SimulationSessionStatus;
  created_by: string;
  snapshot_refs: Record<string, unknown>;
  metadata: Record<string, unknown>;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  prepared_at: string | null;
  policy_snapshot: Record<string, unknown> | null;
  topology_snapshot: Record<string, unknown> | null;
  dataset_snapshot: Record<string, unknown> | null;
  configuration_snapshot: Record<string, unknown> | null;
  policy_snapshot_hash: string | null;
  topology_snapshot_hash: string | null;
  dataset_snapshot_hash: string | null;
  configuration_snapshot_hash: string | null;
  experiment_fingerprint: string | null;
  snapshot_schema_version: number | null;
}

export interface CreateSimulationSessionInput {
  snapshot_refs?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface SimulationTelemetryRecord {
  event_id: string;
  project_id: string;
  variable: string;
  value: number;
  timestamp: string;
  context: Record<string, unknown>;
  metadata: Record<string, unknown>;
  quality: string;
  source: string;
  event_kind: "telemetry.observed";
}

export interface PrepareSimulationSessionInput {
  policy_id: string;
  dataset: {
    source_kind: "historical" | "synthetic";
    records: SimulationTelemetryRecord[];
  };
  configuration: {
    initial_virtual_time?: string;
    random_seed?: number;
    evaluation_options?: { include_trace?: boolean };
  };
}

export interface SimulationReadyMaterial {
  policy_snapshot: Record<string, unknown>;
  topology_snapshot: Record<string, unknown>;
  dataset_snapshot: Record<string, unknown>;
  configuration_snapshot: Record<string, unknown>;
  policy_snapshot_hash: string;
  topology_snapshot_hash: string;
  dataset_snapshot_hash: string;
  configuration_snapshot_hash: string;
  experiment_fingerprint: string;
  snapshot_schema_version: number;
}
