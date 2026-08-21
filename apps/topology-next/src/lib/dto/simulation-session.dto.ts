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
}

export interface CreateSimulationSessionInput {
  snapshot_refs?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}
