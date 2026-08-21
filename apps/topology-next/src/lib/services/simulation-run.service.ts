import { assertControlPermission } from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { ConflictError, InternalError, NotFoundError } from "@/lib/errors/domain-errors";

export interface SimulationRunSummary { id: string; project_id: string; session_id: string; status: string; output_count: number; [key: string]: unknown; }
export interface SimulationRunPage { items: SimulationRunSummary[]; total: number; limit: number; offset: number; }

export class SimulationRunService {
  private readonly endpoint = process.env.SIMULATION_REPLAY_RUNNER_URL ?? "http://simulation-replay-runner:8010";
  async execute(actor: ControlActor, projectId: string, sessionId: string): Promise<SimulationRunSummary> {
    assertControlPermission(actor, "edit_policies", projectId);
    return this.request("/internal/simulation-runs", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ project_id: projectId, session_id: sessionId, created_by: actor.actor_id ?? actor.user_id }) });
  }
  async list(actor: ControlActor, projectId: string, sessionId: string, limit = 100, offset = 0): Promise<SimulationRunPage> {
    assertControlPermission(actor, "view_dashboard", projectId);
    return this.request<SimulationRunPage>(`/internal/simulation-runs/${projectId}/${sessionId}?limit=${limit}&offset=${offset}`);
  }
  async get(actor: ControlActor, projectId: string, sessionId: string, runId: string): Promise<SimulationRunSummary> {
    assertControlPermission(actor, "view_dashboard", projectId);
    return this.request(`/internal/simulation-runs/${projectId}/${sessionId}/${runId}`);
  }
  async result(actor: ControlActor, projectId: string, sessionId: string, runId: string): Promise<SimulationRunSummary> {
    assertControlPermission(actor, "view_dashboard", projectId);
    return this.request(`/internal/simulation-runs/${projectId}/${sessionId}/${runId}/result`);
  }
  async trace(actor: ControlActor, projectId: string, sessionId: string, runId: string, limit: number, offset: number): Promise<SimulationRunSummary> {
    assertControlPermission(actor, "view_dashboard", projectId);
    return this.request(`/internal/simulation-runs/${projectId}/${sessionId}/${runId}/trace?limit=${limit}&offset=${offset}`);
  }
  private async request<T = SimulationRunSummary>(path: string, init?: RequestInit): Promise<T> {
    let response: Response;
    try { response = await fetch(`${this.endpoint}${path}`, init); } catch { throw new InternalError("Simulation replay runner is unavailable"); }
    const body = await response.json().catch(() => ({}));
    if (response.status === 404) throw new NotFoundError("Simulation run not found");
    if (response.status === 409) throw new ConflictError(String(body.detail ?? "Simulation run rejected"));
    if (!response.ok) throw new InternalError("Simulation replay runner failed");
    return body as T;
  }
}
