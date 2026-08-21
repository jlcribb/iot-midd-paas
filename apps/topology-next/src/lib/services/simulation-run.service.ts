import { assertControlPermission } from "@/lib/auth/control-access";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { ConflictError, InternalError, NotFoundError } from "@/lib/errors/domain-errors";

export interface SimulationRunSummary { id: string; project_id: string; session_id: string; status: string; output_count: number; [key: string]: unknown; }

export class SimulationRunService {
  private readonly endpoint = process.env.SIMULATION_REPLAY_RUNNER_URL ?? "http://simulation-replay-runner:8010";
  async execute(actor: ControlActor, projectId: string, sessionId: string): Promise<SimulationRunSummary> {
    assertControlPermission(actor, "edit_policies", projectId);
    return this.request("/internal/simulation-runs", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ project_id: projectId, session_id: sessionId, created_by: actor.actor_id ?? actor.user_id }) });
  }
  async get(actor: ControlActor, projectId: string, sessionId: string, runId: string): Promise<SimulationRunSummary> {
    assertControlPermission(actor, "view_dashboard", projectId);
    return this.request(`/internal/simulation-runs/${projectId}/${sessionId}/${runId}`);
  }
  private async request(path: string, init?: RequestInit): Promise<SimulationRunSummary> {
    let response: Response;
    try { response = await fetch(`${this.endpoint}${path}`, init); } catch { throw new InternalError("Simulation replay runner is unavailable"); }
    const body = await response.json().catch(() => ({}));
    if (response.status === 404) throw new NotFoundError("Simulation run not found");
    if (response.status === 409) throw new ConflictError(String(body.detail ?? "Simulation run rejected"));
    if (!response.ok) throw new InternalError("Simulation replay runner failed");
    return body as SimulationRunSummary;
  }
}
