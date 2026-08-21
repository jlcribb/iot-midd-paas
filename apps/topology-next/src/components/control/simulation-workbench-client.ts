import type { ControlAccessSnapshot } from "@/lib/dto/control-access.dto";
import type { SimulationSession } from "@/lib/dto/simulation-session.dto";
import type { PolicyOperationalView } from "@/lib/dto/control-operations.dto";

interface ApiSuccessResponse<T> { success: true; data: T; }
interface ApiFailureResponse { success: false; error?: { message?: string }; }

export interface SimulationRunView {
  id: string;
  project_id: string;
  session_id: string;
  status: string;
  output_count: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  failure_code?: string | null;
  failure_detail?: string | null;
  result_fingerprint?: string | null;
}

export interface SimulationRunPage { items: SimulationRunView[]; total: number; limit: number; offset: number; }

export interface SimulationResultView {
  experiment_fingerprint: string;
  result_fingerprint: string;
  processed_events: number;
  evaluation_count: number;
  recommendation_count: number;
  actionable_recommendation_count: number;
  recommendation_only_count: number;
  failed_domain_event_count: number;
  first_virtual_timestamp: string | null;
  last_virtual_timestamp: string | null;
  canonical_result_schema_version: number;
}

export interface SimulationTraceItem {
  sequence: number;
  event_id: string;
  virtual_timestamp: string;
  output: Record<string, unknown>;
}
export interface SimulationTracePage { items: SimulationTraceItem[]; total: number; limit: number; offset: number; }

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    cache: "no-store",
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) }
  });
  const payload = await response.json().catch(() => null) as ApiSuccessResponse<T> | ApiFailureResponse | null;
  if (!response.ok || !payload || !payload.success) {
    throw new Error(payload && !payload.success ? payload.error?.message || `HTTP ${response.status}` : `HTTP ${response.status}`);
  }
  return payload.data;
}

function base(projectId: string, sessionId?: string) {
  const project = encodeURIComponent(projectId);
  return `/api/control/simulations/projects/${project}/sessions${sessionId ? `/${encodeURIComponent(sessionId)}` : ""}`;
}

export const simulationWorkbenchClient = {
  getAccess: () => request<ControlAccessSnapshot>("/api/control/access"),
  sessions: (projectId: string) => request<SimulationSession[]>(base(projectId)),
  policies: (projectId: string) => request<{ items: PolicyOperationalView[] }>(`/api/control/operations/projects/${encodeURIComponent(projectId)}/policies?limit=200&offset=0`),
  createSession: (projectId: string) => request<SimulationSession>(base(projectId), { method: "POST", body: JSON.stringify({ metadata: { created_from: "simulation_workbench" } }) }),
  prepare: (projectId: string, sessionId: string, body: unknown) => request<SimulationSession>(`${base(projectId, sessionId)}/prepare`, { method: "POST", body: JSON.stringify(body) }),
  runs: (projectId: string, sessionId: string) => request<SimulationRunPage>(`${base(projectId, sessionId)}/runs?limit=100&offset=0`),
  execute: (projectId: string, sessionId: string) => request<SimulationRunView>(`${base(projectId, sessionId)}/runs`, { method: "POST", body: "{}" }),
  result: (projectId: string, sessionId: string, runId: string) => request<SimulationResultView>(`${base(projectId, sessionId)}/runs/${encodeURIComponent(runId)}/result`),
  trace: (projectId: string, sessionId: string, runId: string, offset: number, limit = 25) => request<SimulationTracePage>(`${base(projectId, sessionId)}/runs/${encodeURIComponent(runId)}/trace?limit=${limit}&offset=${offset}`)
};
