"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { LogoutButton } from "@/components/auth/logout-button";
import type { ControlAccessSnapshot } from "@/lib/dto/control-access.dto";
import type {
  ControlAuditView,
  ControlRecommendationView,
  ControlStatusView
} from "@/lib/dto/control.dto";
import {
  auditKey,
  formatControlTimestamp,
  getActivityBadgeClass,
  getActivityLabel,
  recommendationKey
} from "@/components/control/control-dashboard.helpers";

interface ApiSuccessResponse<T> {
  success: true;
  data: T;
}

interface ControlDashboardSnapshot {
  access: ControlAccessSnapshot;
  status: ControlStatusView;
  recommendations: ControlRecommendationView[];
  audit: ControlAuditView[];
}

async function fetchApi<T>(url: string): Promise<T> {
  const response = await fetch(url, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const payload = (await response.json()) as ApiSuccessResponse<T>;
  if (!payload.success) {
    throw new Error("Unexpected API payload");
  }

  return payload.data;
}

async function fetchControlDashboardSnapshot(): Promise<ControlDashboardSnapshot> {
  const [access, status, recommendations, audit] = await Promise.all([
    fetchApi<ControlAccessSnapshot>("/api/control/access"),
    fetchApi<ControlStatusView>("/api/control/status"),
    fetchApi<ControlRecommendationView[]>("/api/control/recommendations?limit=8"),
    fetchApi<ControlAuditView[]>("/api/control/audit?limit=8")
  ]);

  return {
    access,
    status,
    recommendations,
    audit
  };
}

export function ControlDashboard() {
  const [data, setData] = useState<ControlDashboardSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadedAt, setLoadedAt] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const snapshot = await fetchControlDashboardSnapshot();
        if (cancelled) {
          return;
        }
        setData(snapshot);
        setError(null);
        setLoadedAt(new Date().toISOString());
      } catch (loadError) {
        if (cancelled) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "No se pudo cargar observabilidad de control");
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="control-dashboard">
      <section className="control-header">
        <div className="control-header-main">
          <span className="control-eyebrow">Midd IOT / Control Engine</span>
          <h1>Dashboard mínimo de control</h1>
          <p>
            Vista read-only de estado, recomendaciones y auditoría del control engine.
          </p>
          {data ? (
            <p>
              Usuario actual: <code>{data.access.actor.user_id}</code> · rol <code>{data.access.actor.role}</code> ·
              scope {data.access.actor.all_projects ? <code>all-projects</code> : <code>{data.access.allowed_projects.length} projects</code>}
            </p>
          ) : null}
        </div>
        <div className="control-header-meta">
          <Link className="control-nav-link" href="/control/policies">
            Gestionar Policies
          </Link>
          <LogoutButton />
          <Link className="control-nav-link" href="/">
            Volver a Topología
          </Link>
          <span className="control-loaded-at">
            Última carga: {formatControlTimestamp(loadedAt)}
          </span>
        </div>
      </section>

      {error ? (
        <section className="control-alert control-alert-error">
          <strong>No se pudo cargar el dashboard.</strong>
          <span>{error}</span>
        </section>
      ) : null}

      {!data ? (
        <section className="control-alert">
          <strong>Cargando observabilidad de control...</strong>
        </section>
      ) : (
        <>
          <section className="control-status-grid">
            <article className="control-panel control-hero-panel">
              <div className="control-panel-heading">
                <div>
                  <span className="panel-kicker">Estado general</span>
                  <h2>Control Engine</h2>
                </div>
                <span className={getActivityBadgeClass(data.status.activity_status)}>
                  {getActivityLabel(data.status.activity_status)}
                </span>
              </div>
              <div className="control-hero-metrics">
                <div className="control-stat-card">
                  <span className="control-stat-label">Último audit</span>
                  <strong>{formatControlTimestamp(data.status.latest_audit_at)}</strong>
                </div>
                <div className="control-stat-card">
                  <span className="control-stat-label">Última recommendation</span>
                  <strong>{formatControlTimestamp(data.status.latest_recommendation_at)}</strong>
                </div>
                <div className="control-stat-card">
                  <span className="control-stat-label">Último skipped</span>
                  <strong>{formatControlTimestamp(data.status.latest_skipped_at)}</strong>
                </div>
              </div>
            </article>

            <article className="control-panel">
              <div className="control-panel-heading">
                <div>
                  <span className="panel-kicker">Capacidad habilitada</span>
                  <h2>Configuración operativa</h2>
                </div>
              </div>
              <div className="control-kpi-grid">
                <div className="control-kpi">
                  <strong>{data.status.enabled_projects}</strong>
                  <span>Proyectos con control habilitado</span>
                </div>
                <div className="control-kpi">
                  <strong>{data.status.enabled_policies}</strong>
                  <span>Policies habilitadas</span>
                </div>
                <div className="control-kpi">
                  <strong>{data.status.projects_with_policies}</strong>
                  <span>Proyectos con policies</span>
                </div>
              </div>
            </article>

            <article className="control-panel">
              <div className="control-panel-heading">
                <div>
                  <span className="panel-kicker">Últimas 24 horas</span>
                  <h2>Actividad</h2>
                </div>
              </div>
              <div className="control-kpi-grid">
                <div className="control-kpi">
                  <strong>{data.status.recommendations_last_24h}</strong>
                  <span>Recommendations</span>
                </div>
                <div className="control-kpi">
                  <strong>{data.status.skipped_last_24h}</strong>
                  <span>Skipped</span>
                </div>
                <div className="control-kpi">
                  <strong>{data.status.errors_last_24h}</strong>
                  <span>Errors</span>
                </div>
                <div className="control-kpi">
                  <strong>{data.status.audits_last_24h}</strong>
                  <span>Audit events</span>
                </div>
              </div>
            </article>
          </section>

          <section className="control-content-grid">
            <article className="control-panel">
              <div className="control-panel-heading">
                <div>
                  <span className="panel-kicker">Read-only</span>
                  <h2>Recommendations recientes</h2>
                </div>
              </div>
              {data.recommendations.length === 0 ? (
                <p className="control-empty">No hay recommendations persistidas todavía.</p>
              ) : (
                <div className="control-table-wrap">
                  <table className="control-table">
                    <thead>
                      <tr>
                        <th>Momento</th>
                        <th>Proyecto</th>
                        <th>Variable</th>
                        <th>Acción</th>
                        <th>Valor</th>
                        <th>Policy</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recommendations.map((item) => (
                        <tr key={recommendationKey(item)}>
                          <td>{formatControlTimestamp(item.observed_at)}</td>
                          <td>{item.project_id ?? "N/A"}</td>
                          <td>{item.variable_id ?? "N/A"}</td>
                          <td>
                            <div className="control-cell-stack">
                              <strong>{item.action_label ?? item.recommendation_kind ?? "N/A"}</strong>
                              <span>{item.summary ?? "Sin resumen"}</span>
                            </div>
                          </td>
                          <td>{item.command_value ?? "N/A"}</td>
                          <td>
                            <div className="control-cell-stack">
                              <strong>{item.policy_type ?? "N/A"}</strong>
                              <span>
                                prioridad {item.policy_priority ?? 0} / v{item.policy_version ?? 1}
                              </span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </article>

            <article className="control-panel">
              <div className="control-panel-heading">
                <div>
                  <span className="panel-kicker">Read-only</span>
                  <h2>Audit events recientes</h2>
                </div>
              </div>
              {data.audit.length === 0 ? (
                <p className="control-empty">No hay eventos de auditoría todavía.</p>
              ) : (
                <div className="control-table-wrap">
                  <table className="control-table">
                    <thead>
                      <tr>
                        <th>Momento</th>
                        <th>Estado</th>
                        <th>Proyecto</th>
                        <th>Variable</th>
                        <th>Acción</th>
                        <th>Resumen</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.audit.map((item) => (
                        <tr key={auditKey(item)}>
                          <td>{formatControlTimestamp(item.ts)}</td>
                          <td>
                            <span className={getActivityBadgeClass(item.status === "processed" ? "active" : item.status === "error" ? "stale" : "idle")}>
                              {item.status}
                            </span>
                          </td>
                          <td>{item.project_id ?? "N/A"}</td>
                          <td>{item.variable_id ?? "N/A"}</td>
                          <td>{item.action}</td>
                          <td>{item.summary ?? "Sin detalle"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </article>
          </section>
        </>
      )}
    </main>
  );
}
