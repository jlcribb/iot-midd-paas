"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { LogoutButton } from "@/components/auth/logout-button";
import { formatControlTimestamp } from "@/components/control/control-dashboard.helpers";
import {
  controlOperationsClient,
  type DeliveryQuery,
  type RecommendationQuery
} from "@/components/control/control-operations-client";
import {
  canLoadNextPage,
  getOperationalStatusBadgeClass,
  operationErrorMessage
} from "@/components/control/control-operations.helpers";
import type { ControlAccessSnapshot } from "@/lib/dto/control-access.dto";
import type {
  BindingOperationalView,
  ControlOperationsPage,
  DeliveryOperationalView,
  OperationalAttentionItem,
  PolicyOperationalView,
  ProjectControlOperationsSummary,
  RecommendationOperationalView
} from "@/lib/dto/control-operations.dto";

const PAGE_SIZE = 8;

interface OperationsSnapshot {
  summary: ProjectControlOperationsSummary;
  policies: ControlOperationsPage<PolicyOperationalView>;
  bindings: ControlOperationsPage<BindingOperationalView>;
  recommendations: ControlOperationsPage<RecommendationOperationalView>;
  deliveries: ControlOperationsPage<DeliveryOperationalView>;
  attention: OperationalAttentionItem[];
}

function PageControls({ label, page, onPrevious, onNext }: {
  label: string;
  page: ControlOperationsPage<unknown>;
  onPrevious: () => void;
  onNext: () => void;
}) {
  return (
    <div className="control-page-controls" aria-label={`${label} pagination`}>
      <span>{page.items.length} shown · offset {page.offset}</span>
      <button className="btn btn-secondary" type="button" onClick={onPrevious} disabled={page.offset === 0}>Previous</button>
      <button className="btn btn-secondary" type="button" onClick={onNext} disabled={!canLoadNextPage(page.items.length, page.limit)}>Next</button>
    </div>
  );
}

function TechnicalDetails({ values }: { values: Record<string, string | null | undefined> }) {
  const available = Object.entries(values).filter(([, value]) => value);
  if (!available.length) return null;
  return (
    <details className="control-details">
      <summary>Diagnostic identifiers</summary>
      <dl>{available.map(([label, value]) => <div key={label}><dt>{label}</dt><dd><code>{value}</code></dd></div>)}</dl>
    </details>
  );
}

export function ControlDashboard() {
  const [access, setAccess] = useState<ControlAccessSnapshot | null>(null);
  const [projectId, setProjectId] = useState("");
  const [snapshot, setSnapshot] = useState<OperationsSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadedAt, setLoadedAt] = useState<string | null>(null);
  const [recommendationQuery, setRecommendationQuery] = useState<RecommendationQuery>({ limit: PAGE_SIZE, offset: 0 });
  const [deliveryQuery, setDeliveryQuery] = useState<DeliveryQuery>({ limit: PAGE_SIZE, offset: 0 });

  async function loadProject(nextProjectId: string, nextRecommendationQuery = recommendationQuery, nextDeliveryQuery = deliveryQuery) {
    if (!nextProjectId) return;
    setLoading(true);
    try {
      const configurationPage = { limit: 25, offset: 0 };
      const [summary, policies, bindings, recommendations, deliveries, attention] = await Promise.all([
        controlOperationsClient.getSummary(nextProjectId),
        controlOperationsClient.getPolicies(nextProjectId, configurationPage),
        controlOperationsClient.getBindings(nextProjectId, configurationPage),
        controlOperationsClient.getRecommendations(nextProjectId, nextRecommendationQuery),
        controlOperationsClient.getDeliveries(nextProjectId, nextDeliveryQuery),
        controlOperationsClient.getAttention(nextProjectId)
      ]);
      setSnapshot({ summary, policies, bindings, recommendations, deliveries, attention });
      setError(null);
      setLoadedAt(new Date().toISOString());
    } catch (loadError) {
      setSnapshot(null);
      setError(operationErrorMessage(loadError));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    async function initialize() {
      try {
        const nextAccess = await controlOperationsClient.getAccess();
        const initialProjectId = nextAccess.allowed_projects[0]?.id ?? "";
        if (cancelled) return;
        setAccess(nextAccess);
        setProjectId(initialProjectId);
        if (!initialProjectId) {
          setLoading(false);
          setError("No projects are available in your control scope.");
          return;
        }
        await loadProject(initialProjectId, { limit: PAGE_SIZE, offset: 0 }, { limit: PAGE_SIZE, offset: 0 });
      } catch (loadError) {
        if (!cancelled) {
          setLoading(false);
          setError(operationErrorMessage(loadError));
        }
      }
    }
    void initialize();
    return () => { cancelled = true; };
  // Initial authorization and project selection intentionally run once.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function selectProject(nextProjectId: string) {
    const nextRecommendationQuery = { limit: PAGE_SIZE, offset: 0 };
    const nextDeliveryQuery = { limit: PAGE_SIZE, offset: 0 };
    setProjectId(nextProjectId);
    setRecommendationQuery(nextRecommendationQuery);
    setDeliveryQuery(nextDeliveryQuery);
    void loadProject(nextProjectId, nextRecommendationQuery, nextDeliveryQuery);
  }

  function refresh() {
    void loadProject(projectId);
  }

  function updateRecommendations(next: Partial<RecommendationQuery>) {
    const query = { ...recommendationQuery, ...next, limit: PAGE_SIZE };
    setRecommendationQuery(query);
    void loadProject(projectId, query, deliveryQuery);
  }

  function updateDeliveries(next: Partial<DeliveryQuery>) {
    const query = { ...deliveryQuery, ...next, limit: PAGE_SIZE };
    setDeliveryQuery(query);
    void loadProject(projectId, recommendationQuery, query);
  }

  return (
    <main className="control-dashboard control-operations-center">
      <section className="control-header">
        <div className="control-header-main">
          <span className="control-eyebrow">Midd IOT / Governed control</span>
          <h1>Control Operations</h1>
          <p>Project-scoped operational view of policies, recommendations, simulated delivery, and attention conditions.</p>
        </div>
        <div className="control-header-meta">
          <label className="control-project-picker"><span>Project</span><select value={projectId} onChange={(event) => selectProject(event.target.value)} disabled={!access || loading}>
            {(access?.allowed_projects ?? []).map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}
          </select></label>
          <button className="btn btn-primary" type="button" onClick={refresh} disabled={!projectId || loading}>Refresh data</button>
          <Link className="control-nav-link" href="/control/policies">Manage policies</Link>
          <LogoutButton />
          <Link className="control-nav-link" href="/">Back to topology</Link>
          <span className="control-loaded-at">Last refreshed: {formatControlTimestamp(loadedAt)}</span>
        </div>
      </section>

      {error ? <section className="control-alert control-alert-error" role="alert"><strong>Control Operations is unavailable.</strong><span>{error}</span><button className="btn btn-secondary" type="button" onClick={refresh} disabled={!projectId || loading}>Try again</button></section> : null}
      {loading ? <section className="control-alert" aria-live="polite"><strong>Loading operational control data…</strong><span>Project-scoped contracts are being queried.</span></section> : null}

      {snapshot && !loading ? <>
        <section className="control-status-grid">
          <article className="control-panel control-hero-panel">
            <div className="control-panel-heading"><div><span className="panel-kicker">Project control</span><h2>{snapshot.summary.project.name}</h2></div><span className={snapshot.summary.control_enabled ? "status-badge status-active" : "status-badge status-inactive"}>Control {snapshot.summary.control_enabled ? "ENABLED" : "DISABLED"}</span></div>
            <p className="control-status-copy">{snapshot.summary.control_enabled ? "Simulated governed control is enabled for this project." : "Control is disabled for this project; policies remain visible but inactive."}</p>
            <div className="control-hero-metrics"><div className="control-stat-card"><span className="control-stat-label">Last control activity</span><strong>{formatControlTimestamp(snapshot.summary.last_activity_at)}</strong></div><div className="control-stat-card"><span className="control-stat-label">Recommendations</span><strong>{snapshot.summary.recommendation_summary.total}</strong></div><div className="control-stat-card"><span className="control-stat-label">Attention</span><strong>{snapshot.summary.attention_summary.total}</strong></div></div>
          </article>
          <article className="control-panel"><div className="control-panel-heading"><div><span className="panel-kicker">Operational summary</span><h2>Policies & bindings</h2></div></div><div className="control-kpi-grid"><div className="control-kpi"><strong>{snapshot.summary.policy_summary.total}</strong><span>Policies · {snapshot.summary.policy_summary.actionable} actionable</span></div><div className="control-kpi"><strong>{snapshot.summary.policy_summary.recommendation_only}</strong><span>Recommendation-only</span></div><div className="control-kpi"><strong>{snapshot.summary.binding_summary.actionable}</strong><span>Actionable bindings</span></div><div className="control-kpi"><strong>{snapshot.summary.binding_summary.invalid}</strong><span>Invalid bindings</span></div></div></article>
          <article className="control-panel"><div className="control-panel-heading"><div><span className="panel-kicker">Delivery summary</span><h2>Lifecycle</h2></div></div><div className="control-kpi-grid"><div className="control-kpi"><strong>{snapshot.summary.delivery_summary.ACKNOWLEDGED}</strong><span>Acknowledged</span></div><div className="control-kpi"><strong>{snapshot.summary.delivery_summary.PENDING + snapshot.summary.delivery_summary.PUBLISHED}</strong><span>Pending or published</span></div><div className="control-kpi"><strong>{snapshot.summary.delivery_summary.RETRYING}</strong><span>Retrying</span></div><div className="control-kpi"><strong>{snapshot.summary.delivery_summary.FAILED + snapshot.summary.delivery_summary.EXPIRED}</strong><span>Failed or expired</span></div></div></article>
        </section>

        <section className="control-panel control-attention-panel"><div className="control-panel-heading"><div><span className="panel-kicker">Attention first</span><h2>Operational conditions</h2></div><span className={snapshot.attention.length ? "status-badge status-maintenance" : "status-badge status-active"}>{snapshot.attention.length ? `${snapshot.attention.length} conditions` : "All clear"}</span></div>{snapshot.attention.length === 0 ? <p className="control-empty">No operational conditions require attention.</p> : <ul className="control-attention-list">{snapshot.attention.map((item) => <li key={`${item.entity_type}:${item.entity_id}:${item.category}`} className={`control-attention-item control-attention-${item.severity}`}><div><strong>{item.severity.toUpperCase()} · {item.category}</strong><p>{item.message}</p><span>{item.entity_type} · {formatControlTimestamp(item.detected_at)}</span></div><p className="control-attention-hint">{item.action_hint}</p></li>)}</ul>}</section>

        <section className="control-content-grid">
          <article className="control-panel"><div className="control-panel-heading"><div><span className="panel-kicker">Configuration</span><h2>Policies</h2></div></div>{snapshot.policies.items.length === 0 ? <p className="control-empty">No control policies are configured for this project.</p> : <div className="control-policy-grid">{snapshot.policies.items.map((policy) => <article className="control-policy-card" key={policy.policy_id}><div className="control-policy-card-header"><div><h3>{policy.variable}</h3><p className="control-policy-meta">{policy.source_asset_name ?? "No source asset"} → {policy.target_asset_name ?? "No actuation target"}</p></div><div className="control-policy-badges"><span className={getOperationalStatusBadgeClass(policy.effective_status)}>{policy.effective_status}</span><span className="status-badge status-inactive">{policy.configured_status}</span></div></div><div className="control-policy-meta-grid"><div><span>Actionability</span><strong>{policy.actionability}</strong></div><div><span>Operation</span><strong>{policy.operation ?? "No operation"}</strong></div><div><span>Last recommendation</span><strong>{formatControlTimestamp(policy.last_recommendation_at)}</strong></div></div>{policy.recommendation_only ? <p className="control-recommendation-only"><strong>Recommendation-only.</strong> This policy may generate recommendations, but it has no valid actionable target. No DeliveryIntent is created by design.</p> : null}{policy.reason ? <p className="control-policy-reason"><strong>{policy.reason_code}:</strong> {policy.reason}</p> : null}<button className="btn btn-secondary" type="button" onClick={() => updateRecommendations({ policyId: policy.policy_id, correlationId: undefined, offset: 0 })}>View recommendations</button><TechnicalDetails values={{ policy_id: policy.policy_id, source_asset_id: policy.source_asset_id, target_asset_id: policy.target_asset_id }} /></article>)}</div>}</article>

          <article className="control-panel"><div className="control-panel-heading"><div><span className="panel-kicker">Routing</span><h2>Bindings</h2></div></div>{snapshot.bindings.items.length === 0 ? <p className="control-empty">No actuation bindings are configured.</p> : <div className="control-binding-list">{snapshot.bindings.items.map((binding) => <article className="control-binding-card" key={binding.binding_id}><div className="control-binding-flow"><strong>{binding.source_asset_name ?? "Unknown source"}</strong><span aria-hidden="true">→</span><strong>{binding.target_asset_name ?? "Unavailable target"}</strong><span aria-hidden="true">→</span><span>{binding.control_point} / {binding.operation}</span></div><span className={binding.valid ? "status-badge status-active" : "status-badge status-fault"}>{binding.valid ? "VALID ACTIONABLE" : "INVALID"}</span><p>Capabilities: {binding.target_capabilities.map((item) => String(item.key ?? "unknown")).join(", ") || "Not advertised"}</p>{binding.reason ? <p className="control-policy-reason"><strong>{binding.reason_code}:</strong> {binding.reason}</p> : null}<TechnicalDetails values={{ binding_id: binding.binding_id, policy_id: binding.policy_id, source_asset_id: binding.source_asset_id, target_asset_id: binding.target_asset_id }} /></article>)}</div>}</article>
        </section>

        <section className="control-content-grid">
          <article className="control-panel"><div className="control-panel-heading"><div><span className="panel-kicker">Read-only timeline</span><h2>Recommendations</h2></div></div><form className="control-filter-bar" onSubmit={(event) => { event.preventDefault(); updateRecommendations({ offset: 0 }); }}><label>Policy ID<input value={recommendationQuery.policyId ?? ""} onChange={(event) => setRecommendationQuery((current) => ({ ...current, policyId: event.target.value || undefined }))} /></label><label>Correlation ID<input value={recommendationQuery.correlationId ?? ""} onChange={(event) => setRecommendationQuery((current) => ({ ...current, correlationId: event.target.value || undefined }))} /></label><button className="btn btn-secondary" type="submit">Apply filters</button></form>{snapshot.recommendations.items.length === 0 ? <p className="control-empty">No recommendations have been generated yet.</p> : <div className="control-table-wrap"><table className="control-table"><thead><tr><th>Created</th><th>Recommendation</th><th>Policy / source</th><th>Delivery</th></tr></thead><tbody>{snapshot.recommendations.items.map((item) => <tr key={item.audit_id}><td>{formatControlTimestamp(item.created_at)}</td><td><div className="control-cell-stack"><strong>{item.status}</strong><span>{item.summary ?? "No summary"}</span></div></td><td><div className="control-cell-stack"><strong>{item.policy_id ?? "No policy reference"}</strong><span>{item.source_asset_id ?? "No source reference"}</span></div></td><td>{item.delivery_intent_id ? <button className="btn btn-secondary" type="button" onClick={() => updateDeliveries({ recommendationId: item.recommendation_id ?? undefined, correlationId: item.recommendation_id ? undefined : item.correlation_id ?? undefined, offset: 0 })}>View delivery</button> : <span className="status-badge status-inactive">No delivery</span>}<TechnicalDetails values={{ recommendation_id: item.recommendation_id, correlation_id: item.correlation_id, delivery_intent_id: item.delivery_intent_id, command_id: item.command_id }} /></td></tr>)}</tbody></table></div>}<PageControls label="Recommendations" page={snapshot.recommendations} onPrevious={() => updateRecommendations({ offset: Math.max(0, snapshot.recommendations.offset - PAGE_SIZE) })} onNext={() => updateRecommendations({ offset: snapshot.recommendations.offset + PAGE_SIZE })} /></article>

          <article className="control-panel"><div className="control-panel-heading"><div><span className="panel-kicker">Simulated delivery</span><h2>Deliveries</h2></div></div><form className="control-filter-bar" onSubmit={(event) => { event.preventDefault(); updateDeliveries({ offset: 0 }); }}><label>Status<select value={deliveryQuery.status ?? ""} onChange={(event) => setDeliveryQuery((current) => ({ ...current, status: event.target.value || undefined }))}><option value="">All statuses</option><option value="received">Pending</option><option value="retry_pending">Retrying</option><option value="acknowledged">Acknowledged</option><option value="failed_final">Failed</option><option value="expired">Expired</option></select></label><label>Command ID<input value={deliveryQuery.commandId ?? ""} onChange={(event) => setDeliveryQuery((current) => ({ ...current, commandId: event.target.value || undefined }))} /></label><label>Correlation ID<input value={deliveryQuery.correlationId ?? ""} onChange={(event) => setDeliveryQuery((current) => ({ ...current, correlationId: event.target.value || undefined }))} /></label><button className="btn btn-secondary" type="submit">Apply filters</button></form>{snapshot.deliveries.items.length === 0 ? <p className="control-empty">No delivery activity has been recorded.</p> : <div className="control-table-wrap"><table className="control-table"><thead><tr><th>Target / operation</th><th>Intent</th><th>Publication</th><th>Updated</th></tr></thead><tbody>{snapshot.deliveries.items.map((item) => <tr key={item.delivery_intent_id}><td><div className="control-cell-stack"><strong>{item.target_name ?? item.target_asset_id ?? "Unknown target"}</strong><span>{item.operation}</span></div></td><td><span className={getOperationalStatusBadgeClass(item.intent_status)}>{item.intent_status}</span><p>{item.ack_status ? "Acknowledgement received" : item.retry_count ? `Retry count: ${item.retry_count}` : "No acknowledgement recorded"}</p></td><td><span className={item.outbox_status ? getOperationalStatusBadgeClass(item.outbox_status) : "status-badge status-inactive"}>{item.outbox_status ?? "NOT PUBLISHED"}</span><p>{item.last_error ?? "No delivery error recorded"}</p></td><td>{formatControlTimestamp(item.updated_at)}<TechnicalDetails values={{ delivery_intent_id: item.delivery_intent_id, recommendation_id: item.recommendation_id, correlation_id: item.correlation_id, command_id: item.command_id, event_id: item.event_id }} /></td></tr>)}</tbody></table></div>}<PageControls label="Deliveries" page={snapshot.deliveries} onPrevious={() => updateDeliveries({ offset: Math.max(0, snapshot.deliveries.offset - PAGE_SIZE) })} onNext={() => updateDeliveries({ offset: snapshot.deliveries.offset + PAGE_SIZE })} /></article>
        </section>
      </> : null}
    </main>
  );
}
