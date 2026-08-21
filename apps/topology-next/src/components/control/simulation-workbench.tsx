"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";
import Link from "next/link";
import { LogoutButton } from "@/components/auth/logout-button";
import { formatControlTimestamp } from "@/components/control/control-dashboard.helpers";
import { ControlNoProjectsRecovery, ControlSessionIdentity, initialControlProjectScope } from "@/components/control/control-dashboard";
import { simulationWorkbenchClient, type SimulationResultView, type SimulationRunView, type SimulationTracePage } from "@/components/control/simulation-workbench-client";
import { reproducibilityEvidence } from "@/components/control/simulation-workbench.helpers";
import type { ControlAccessSnapshot } from "@/lib/dto/control-access.dto";
import type { PolicyOperationalView } from "@/lib/dto/control-operations.dto";
import type { SimulationSession } from "@/lib/dto/simulation-session.dto";

const TRACE_PAGE_SIZE = 25;

function shortFingerprint(value: string | null | undefined) { return value ? `${value.slice(0, 12)}…` : "Not materialized"; }
function updateLocation(projectId: string, sessionId: string, runId: string) {
  const query = new URLSearchParams();
  if (projectId) query.set("project", projectId);
  if (sessionId) query.set("session", sessionId);
  if (runId) query.set("run", runId);
  window.history.replaceState(null, "", `/control/simulations${query.size ? `?${query.toString()}` : ""}`);
}
function errorMessage(error: unknown) { return error instanceof Error ? error.message : "The simulation workbench request could not be completed."; }

export function SimulationWorkbench() {
  const [access, setAccess] = useState<ControlAccessSnapshot | null>(null);
  const [projectId, setProjectId] = useState("");
  const [sessions, setSessions] = useState<SimulationSession[]>([]);
  const [policies, setPolicies] = useState<PolicyOperationalView[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [runs, setRuns] = useState<SimulationRunView[]>([]);
  const [runId, setRunId] = useState("");
  const [result, setResult] = useState<SimulationResultView | null>(null);
  const [trace, setTrace] = useState<SimulationTracePage | null>(null);
  const [traceOffset, setTraceOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [policyId, setPolicyId] = useState("");
  const [sourceKind, setSourceKind] = useState<"historical" | "synthetic">("synthetic");
  const [recordsText, setRecordsText] = useState("[]");
  const [randomSeed, setRandomSeed] = useState("");

  const selectedSession = sessions.find((session) => session.id === sessionId) ?? null;
  const selectedRun = runs.find((run) => run.id === runId) ?? null;
  const canMutate = Boolean(access?.permissions.edit_policies);
  const reproducibility = useMemo(() => reproducibilityEvidence(runs), [runs]);
  const hasProjectScope = (access?.allowed_projects.length ?? 0) > 0;

  async function loadRuns(nextProjectId: string, nextSessionId: string, preferredRunId = "") {
    if (!nextProjectId || !nextSessionId) { setRuns([]); setRunId(""); setResult(null); setTrace(null); return; }
    const page = await simulationWorkbenchClient.runs(nextProjectId, nextSessionId);
    setRuns(page.items);
    const nextRun = page.items.some((item) => item.id === preferredRunId) ? preferredRunId : page.items[0]?.id ?? "";
    setRunId(nextRun);
    updateLocation(nextProjectId, nextSessionId, nextRun);
    if (nextRun) await loadRunEvidence(nextProjectId, nextSessionId, nextRun, 0, page.items.find((item) => item.id === nextRun)?.status);
    else { setResult(null); setTrace(null); }
  }

  async function loadRunEvidence(nextProjectId: string, nextSessionId: string, nextRunId: string, offset: number, knownStatus?: string) {
    const run = runs.find((item) => item.id === nextRunId);
    setTraceOffset(offset);
    const status = knownStatus ?? run?.status;
    if (status === "FAILED" || status === "CANCELLED") { setResult(null); setTrace(null); return; }
    try {
      const [nextResult, nextTrace] = await Promise.all([
        simulationWorkbenchClient.result(nextProjectId, nextSessionId, nextRunId),
        simulationWorkbenchClient.trace(nextProjectId, nextSessionId, nextRunId, offset, TRACE_PAGE_SIZE)
      ]);
      setResult(nextResult); setTrace(nextTrace);
    } catch (loadError) {
      setResult(null); setTrace(null);
      if (status === "COMPLETED") setError(errorMessage(loadError));
    }
  }

  async function loadProject(nextProjectId: string, preferredSessionId = "", preferredRunId = "") {
    setLoading(true);
    try {
      const [nextSessions, policyPage] = await Promise.all([simulationWorkbenchClient.sessions(nextProjectId), simulationWorkbenchClient.policies(nextProjectId)]);
      setSessions(nextSessions); setPolicies(policyPage.items);
      const nextSession = nextSessions.some((item) => item.id === preferredSessionId) ? preferredSessionId : nextSessions[0]?.id ?? "";
      setSessionId(nextSession); setError(null);
      await loadRuns(nextProjectId, nextSession, preferredRunId);
    } catch (loadError) {
      setSessions([]); setPolicies([]); setRuns([]); setResult(null); setTrace(null); setError(errorMessage(loadError));
    } finally { setLoading(false); }
  }

  useEffect(() => {
    let cancelled = false;
    async function initialize() {
      try {
        const nextAccess = await simulationWorkbenchClient.getAccess();
        if (cancelled) return;
        setAccess(nextAccess);
        const requested = new URLSearchParams(window.location.search);
        const initial = initialControlProjectScope(nextAccess.allowed_projects);
        const requestedProject = requested.get("project") ?? "";
        const nextProject = nextAccess.allowed_projects.some((project) => project.id === requestedProject) ? requestedProject : initial.projectId;
        setProjectId(nextProject);
        if (!nextProject) { setError(initial.error); setLoading(false); return; }
        await loadProject(nextProject, requested.get("session") ?? "", requested.get("run") ?? "");
      } catch (loadError) { if (!cancelled) { setError(errorMessage(loadError)); setLoading(false); } }
    }
    void initialize();
    return () => { cancelled = true; };
  // The URL is recovered once on entry; subsequent changes are explicit user choices.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function selectSession(nextSessionId: string, preferredRunId = "") {
    setSessionId(nextSessionId); setError(null); setResult(null); setTrace(null);
    try { await loadRuns(projectId, nextSessionId, preferredRunId); } catch (loadError) { setError(errorMessage(loadError)); }
  }

  function selectProject(nextProjectId: string) {
    setProjectId(nextProjectId); setSessionId(""); setRunId(""); setResult(null); setTrace(null); updateLocation(nextProjectId, "", "");
    void loadProject(nextProjectId);
  }

  async function createDraft() {
    setBusy("create"); setError(null); setNotice(null);
    try {
      const created = await simulationWorkbenchClient.createSession(projectId);
      setNotice("Draft simulation session created. It has no operational delivery path.");
      await loadProject(projectId, created.id);
    } catch (createError) { setError(errorMessage(createError)); } finally { setBusy(null); }
  }

  async function prepareDraft(event: FormEvent) {
    event.preventDefault();
    if (!selectedSession) return;
    let records: unknown;
    try { records = JSON.parse(recordsText); } catch { setError("Dataset records must be a valid JSON array; the backend will validate the canonical contract."); return; }
    if (!Array.isArray(records)) { setError("Dataset records must be a JSON array."); return; }
    setBusy("prepare"); setError(null); setNotice(null);
    try {
      const prepared = await simulationWorkbenchClient.prepare(projectId, selectedSession.id, {
        policy_id: policyId, dataset: { source_kind: sourceKind, records },
        configuration: { ...(randomSeed.trim() ? { random_seed: Number(randomSeed) } : {}), evaluation_options: { include_trace: true } }
      });
      setNotice("Experiment prepared. The persisted snapshot and fingerprints are now immutable.");
      await loadProject(projectId, prepared.id);
    } catch (prepareError) { setError(errorMessage(prepareError)); } finally { setBusy(null); }
  }

  async function executeReady() {
    if (!selectedSession) return;
    setBusy("run"); setError(null); setNotice(null);
    try {
      const created = await simulationWorkbenchClient.execute(projectId, selectedSession.id);
      setNotice("Replay run completed through the isolated simulation runner.");
      await loadRuns(projectId, selectedSession.id, created.id);
    } catch (executeError) { setError(errorMessage(executeError)); } finally { setBusy(null); }
  }

  function selectRun(nextRunId: string) {
    setRunId(nextRunId); updateLocation(projectId, sessionId, nextRunId);
    void loadRunEvidence(projectId, sessionId, nextRunId, 0);
  }

  const noProjectRecovery = Boolean(access && !loading && !hasProjectScope);
  return <main className="control-dashboard simulation-workbench">
    <section className="control-header">
      <div className="control-header-main"><span className="control-eyebrow">Midd IOT / Simulation & Replay</span><h1>Simulation Workbench</h1><p>Project-scoped, authenticated replay evidence. This workspace is separated from operational delivery and physical effects.</p></div>
      <div className="control-header-meta">
        <label className="control-project-picker"><span>Project</span><select value={projectId} onChange={(event) => selectProject(event.target.value)} disabled={!access || loading}>{(access?.allowed_projects ?? []).map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</select></label>
        <button className="btn btn-primary" type="button" onClick={() => void loadProject(projectId, sessionId, runId)} disabled={!projectId || loading}>Refresh</button>
        <Link className="control-nav-link" href="/control">Control operations</Link><LogoutButton /><ControlSessionIdentity email={access?.actor.email} />
      </div>
    </section>
    <section className="simulation-safety-banner" role="status"><strong>Simulation & Replay — isolated execution context</strong><span>No operational transport, outbox, publisher, or physical effect is available from this workbench.</span></section>
    {error ? <section className="control-alert control-alert-error" role="alert"><strong>Workbench request could not be completed.</strong><span>{error}</span></section> : null}
    {notice ? <section className="control-alert" role="status">{notice}</section> : null}
    {loading ? <section className="control-alert" aria-live="polite"><strong>Loading authenticated project scope…</strong></section> : null}
    {noProjectRecovery ? <ControlNoProjectsRecovery email={access?.actor.email} /> : null}
    {!loading && hasProjectScope ? <div className="simulation-workbench-grid">
      <section className="control-panel simulation-session-list" aria-labelledby="simulation-sessions-title">
        <div className="control-panel-heading"><div><span className="panel-kicker">Master</span><h2 id="simulation-sessions-title">Experiment sessions</h2></div>{canMutate ? <button className="btn btn-primary" type="button" onClick={() => void createDraft()} disabled={busy !== null}>New Draft</button> : null}</div>
        {!canMutate ? <p className="control-empty">Read-only access: persisted experiments, runs, results, and traces remain visible.</p> : null}
        {!sessions.length ? <p className="control-empty">No simulation sessions exist in this project yet.</p> : <div className="simulation-item-list">{sessions.map((session) => <button key={session.id} type="button" className={`simulation-item ${session.id === sessionId ? "simulation-item-selected" : ""}`} onClick={() => void selectSession(session.id)}><strong>{session.status}</strong><span>{formatControlTimestamp(session.created_at)}</span><code>{shortFingerprint(session.experiment_fingerprint)}</code></button>)}</div>}
      </section>
      <section className="control-panel simulation-detail" aria-labelledby="simulation-detail-title">
        <div className="control-panel-heading"><div><span className="panel-kicker">Detail</span><h2 id="simulation-detail-title">{selectedSession ? `Session ${selectedSession.status}` : "Select an experiment"}</h2></div>{selectedSession ? <code>{selectedSession.id}</code> : null}</div>
        {!selectedSession ? <p className="control-empty">Create a Draft or select an existing project-scoped session.</p> : null}
        {selectedSession?.status === "DRAFT" ? <form className="control-form-grid" onSubmit={prepareDraft}>
          <p className="control-recommendation-only control-field-wide">Draft inputs are sent to the server unchanged apart from JSON parsing. The server owns snapshotting, validation, ordering, hashes, and the experiment fingerprint.</p>
          <label className="control-field"><span>Control policy</span><select value={policyId} onChange={(event) => setPolicyId(event.target.value)} required disabled={!canMutate || busy !== null}><option value="">Select a policy</option>{policies.map((policy) => <option key={policy.policy_id} value={policy.policy_id}>{policy.variable} · {policy.policy_id.slice(0, 8)} · {policy.actionability}</option>)}</select></label>
          <label className="control-field"><span>Dataset source</span><select value={sourceKind} onChange={(event) => setSourceKind(event.target.value as "historical" | "synthetic")} disabled={!canMutate || busy !== null}><option value="synthetic">Synthetic materialized records</option><option value="historical">Historical materialized records</option></select></label>
          <label className="control-field"><span>Random seed (optional)</span><input value={randomSeed} onChange={(event) => setRandomSeed(event.target.value)} inputMode="numeric" disabled={!canMutate || busy !== null} /></label>
          <label className="control-field control-field-wide"><span>Materialized telemetry records (JSON array)</span><textarea className="control-textarea" value={recordsText} onChange={(event) => setRecordsText(event.target.value)} disabled={!canMutate || busy !== null} aria-describedby="dataset-contract" /><small id="dataset-contract">Each record must satisfy the persisted API contract, including event_id, project_id, variable, value, and timestamp. No live telemetry is read by this UI.</small></label>
          {canMutate ? <div className="control-actions control-field-wide"><button className="btn btn-primary" type="submit" disabled={busy !== null}>{busy === "prepare" ? "Preparing…" : "Prepare immutable experiment"}</button></div> : null}
        </form> : null}
        {selectedSession?.status === "READY" ? <>
          <section className="simulation-fingerprint-grid" aria-label="Immutable experiment evidence"><div><span>Experiment fingerprint</span><code>{selectedSession.experiment_fingerprint}</code></div><div><span>Policy hash</span><code>{selectedSession.policy_snapshot_hash}</code></div><div><span>Topology hash</span><code>{selectedSession.topology_snapshot_hash}</code></div><div><span>Dataset hash</span><code>{selectedSession.dataset_snapshot_hash}</code></div><div><span>Configuration hash</span><code>{selectedSession.configuration_snapshot_hash}</code></div><div><span>Engine / clock</span><code>{String((selectedSession.configuration_snapshot?.engine as Record<string, unknown> | undefined)?.version ?? "persisted")} / {String((selectedSession.configuration_snapshot?.clock as Record<string, unknown> | undefined)?.model_version ?? "persisted")}</code></div></section>
          <p className="control-recommendation-only">READY evidence is immutable in the UI. Running it creates a separate run; it never mutates this experiment.</p>
          {canMutate ? <div className="control-actions"><button className="btn btn-primary" type="button" onClick={() => void executeReady()} disabled={busy !== null}>{busy === "run" ? "Running…" : "Run prepared experiment"}</button></div> : null}
        </> : null}
        {selectedSession && !["DRAFT", "READY"].includes(selectedSession.status) ? <p className="control-empty">This persisted session is {selectedSession.status}. Its existing evidence is read-only.</p> : null}
      </section>
      <section className="control-panel simulation-runs" aria-labelledby="simulation-runs-title">
        <div className="control-panel-heading"><div><span className="panel-kicker">Runs</span><h2 id="simulation-runs-title">Replay history</h2></div><span className="status-badge status-inactive">{runs.length} visible</span></div>
        {!selectedSession ? <p className="control-empty">Select a session to see its runs.</p> : !runs.length ? <p className="control-empty">No run has been created for this experiment.</p> : <div className="simulation-item-list">{runs.map((run) => <button key={run.id} type="button" className={`simulation-item ${run.id === runId ? "simulation-item-selected" : ""}`} onClick={() => selectRun(run.id)}><strong>{run.status}</strong><span>{formatControlTimestamp(run.completed_at ?? run.created_at)} · outputs {run.output_count}</span><code>{shortFingerprint(run.result_fingerprint)}</code></button>)}</div>}
        {runs.length ? <p className="control-empty">Reproducibility indicator: {reproducibility.status === "CONSISTENT" ? `consistent opaque result fingerprint across ${reproducibility.count} runs` : reproducibility.status === "PENDING" ? "awaiting two materialized completed results" : "result fingerprints differ; inspect persisted evidence"}. This is string equality only, not a client-side replay or semantic comparison.</p> : null}
      </section>
      <section className="control-panel simulation-evidence" aria-labelledby="simulation-evidence-title">
        <div className="control-panel-heading"><div><span className="panel-kicker">Result & trace</span><h2 id="simulation-evidence-title">{selectedRun ? selectedRun.status : "Select a run"}</h2></div>{selectedRun ? <code>{selectedRun.id}</code> : null}</div>
        {selectedRun?.status === "FAILED" || selectedRun?.status === "CANCELLED" ? <section className="control-alert control-alert-error"><strong>Run failed safely; no result is presented.</strong><span>{selectedRun.failure_code ?? "No result materialized for this terminal run."}</span></section> : null}
        {result ? <><section className="simulation-result-grid"><div><span>Result fingerprint</span><code>{result.result_fingerprint}</code></div><div><span>Experiment fingerprint</span><code>{result.experiment_fingerprint}</code></div><div><span>Processed events</span><strong>{result.processed_events}</strong></div><div><span>Evaluations</span><strong>{result.evaluation_count}</strong></div><div><span>Recommendations</span><strong>{result.recommendation_count}</strong></div><div><span>Actionable recommendations</span><strong>{result.actionable_recommendation_count}</strong></div><div><span>Recommendation-only</span><strong>{result.recommendation_only_count}</strong></div><div><span>Failed domain events</span><strong>{result.failed_domain_event_count}</strong></div></section><p className="control-recommendation-only">Recommendation-only and actionable counts are canonical result fields supplied by the backend; this UI does not infer their meaning from trace output.</p></> : null}
        {trace ? <><div className="control-table-wrap"><table className="control-table"><thead><tr><th>Sequence</th><th>Virtual time</th><th>Event</th><th>Persisted trace output</th></tr></thead><tbody>{trace.items.map((item) => <tr key={`${item.sequence}:${item.event_id}`}><td>{item.sequence}</td><td>{formatControlTimestamp(item.virtual_timestamp)}</td><td><code>{item.event_id}</code></td><td><code className="simulation-json">{JSON.stringify(item.output)}</code></td></tr>)}</tbody></table></div><div className="control-page-controls"><span>{trace.items.length} of {trace.total} trace items</span><button className="btn btn-secondary" type="button" onClick={() => void loadRunEvidence(projectId, sessionId, runId, Math.max(0, traceOffset - TRACE_PAGE_SIZE))} disabled={traceOffset === 0}>Previous</button><button className="btn btn-secondary" type="button" onClick={() => void loadRunEvidence(projectId, sessionId, runId, traceOffset + TRACE_PAGE_SIZE)} disabled={traceOffset + TRACE_PAGE_SIZE >= trace.total}>Next</button></div></> : null}
        {selectedRun && !result && !trace && selectedRun.status !== "FAILED" && selectedRun.status !== "CANCELLED" ? <p className="control-empty">Evidence is not materialized yet.</p> : null}
      </section>
    </div> : null}
  </main>;
}
