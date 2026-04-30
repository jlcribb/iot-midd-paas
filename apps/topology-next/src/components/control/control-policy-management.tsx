"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import type {
  ControlPolicy,
  ControlPolicyConflict,
  ControlPolicyPreviewResponse
} from "@/lib/dto/control-policy.dto";
import type { Project } from "@/lib/dto/project.dto";
import {
  buildPreviewPayload,
  buildCreatePolicyPayload,
  buildUpdatePolicyPayload,
  collectListWarnings,
  createEmptyPolicyFormState,
  defaultParamsText,
  policyToDraft,
  previewSummaryText,
  type ControlPolicyCreateFormState,
  type ControlPolicyDraft
} from "@/components/control/control-policies.helpers";
import { formatControlTimestamp } from "@/components/control/control-dashboard.helpers";

interface ApiSuccessResponse<T> {
  success: true;
  data: T;
}

interface ApiFailureResponse {
  success: false;
  error: {
    message: string;
  };
}

type ApiResponse<T> = ApiSuccessResponse<T> | ApiFailureResponse;

function errorMessageFromPayload(payload: ApiResponse<unknown> | null, fallback: string) {
  if (payload && !payload.success) {
    return payload.error.message;
  }
  return fallback;
}

async function fetchApi<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    cache: "no-store",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });

  const payload = (await response.json().catch(() => null)) as ApiResponse<T> | null;
  if (!response.ok || !payload || !payload.success) {
    throw new Error(errorMessageFromPayload(payload, `HTTP ${response.status}`));
  }

  return payload.data;
}

function buildDraftMap(policies: ControlPolicy[]) {
  return Object.fromEntries(policies.map((policy) => [policy.id, policyToDraft(policy)])) as Record<string, ControlPolicyDraft>;
}

export function ControlPolicyManagement() {
  const [policies, setPolicies] = useState<ControlPolicy[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [drafts, setDrafts] = useState<Record<string, ControlPolicyDraft>>({});
  const [createForm, setCreateForm] = useState<ControlPolicyCreateFormState>(createEmptyPolicyFormState());
  const [loading, setLoading] = useState(true);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [createPreview, setCreatePreview] = useState<ControlPolicyPreviewResponse | null>(null);
  const [policyPreviews, setPolicyPreviews] = useState<Record<string, ControlPolicyPreviewResponse | null>>({});

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [policiesData, projectsData] = await Promise.all([
          fetchApi<ControlPolicy[]>("/api/control/policies"),
          fetchApi<Project[]>("/api/projects")
        ]);

        if (cancelled) {
          return;
        }

        setPolicies(policiesData);
        setProjects(projectsData);
        setDrafts(buildDraftMap(policiesData));
        setCreateForm((current) => ({
          ...current,
          project_id: current.project_id || projectsData[0]?.id || ""
        }));
        setError(null);
      } catch (loadError) {
        if (cancelled) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "No se pudo cargar la gestión de policies");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  async function reloadPolicies() {
    const policiesData = await fetchApi<ControlPolicy[]>("/api/control/policies");
    setPolicies(policiesData);
    setDrafts(buildDraftMap(policiesData));
    setPolicyPreviews({});
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusyKey("create");
    setError(null);
    setNotice(null);

    try {
      const payload = buildCreatePolicyPayload(createForm);
      await fetchApi<ControlPolicy>("/api/control/policies", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      await reloadPolicies();
      setCreateForm({
        ...createEmptyPolicyFormState(),
        project_id: createForm.project_id
      });
      setCreatePreview(null);
      setNotice("Policy creada correctamente.");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "No se pudo crear la policy");
    } finally {
      setBusyKey(null);
    }
  }

  async function handleSave(policyId: string) {
    const draft = drafts[policyId];
    if (!draft) {
      return;
    }

    setBusyKey(`save:${policyId}`);
    setError(null);
    setNotice(null);

    try {
      const payload = buildUpdatePolicyPayload(draft);
      await fetchApi<ControlPolicy>(`/api/control/policies/${policyId}`, {
        method: "PATCH",
        body: JSON.stringify(payload)
      });
      await reloadPolicies();
      setPolicyPreviews((current) => ({
        ...current,
        [policyId]: null
      }));
      setNotice("Policy actualizada correctamente.");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "No se pudo actualizar la policy");
    } finally {
      setBusyKey(null);
    }
  }

  async function handleDisable(policyId: string) {
    setBusyKey(`disable:${policyId}`);
    setError(null);
    setNotice(null);

    try {
      await fetchApi<ControlPolicy>(`/api/control/policies/${policyId}`, {
        method: "DELETE"
      });
      await reloadPolicies();
      setNotice("Policy deshabilitada correctamente.");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "No se pudo deshabilitar la policy");
    } finally {
      setBusyKey(null);
    }
  }

  function updateDraft(policyId: string, next: Partial<ControlPolicyDraft>) {
    setDrafts((current) => ({
      ...current,
      [policyId]: {
        ...current[policyId],
        ...next
      }
    }));
  }

  function handlePolicyTypeChange(nextType: ControlPolicyCreateFormState["policy_type"]) {
    setCreateForm((current) => {
      const replaceParams =
        !current.params_text.trim() ||
        current.params_text === defaultParamsText("proportional") ||
        current.params_text === defaultParamsText("threshold");

      return {
        ...current,
        policy_type: nextType,
        params_text: replaceParams ? defaultParamsText(nextType) : current.params_text
      };
    });
  }

  async function handleCreatePreview() {
    setBusyKey("preview:create");
    setError(null);

    try {
      const payload = buildPreviewPayload({
        project_id: createForm.project_id,
        variable: createForm.variable,
        draft: createForm,
        policy_type: createForm.policy_type,
        version: 1
      });
      const preview = await fetchApi<ControlPolicyPreviewResponse>("/api/control/policies/preview", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      setCreatePreview(preview);
    } catch (previewError) {
      setError(previewError instanceof Error ? previewError.message : "No se pudo generar el preview");
    } finally {
      setBusyKey(null);
    }
  }

  async function handlePolicyPreview(policy: ControlPolicy) {
    const draft = drafts[policy.id];
    if (!draft) {
      return;
    }

    setBusyKey(`preview:${policy.id}`);
    setError(null);

    try {
      const payload = buildPreviewPayload({
        project_id: policy.project_id,
        variable: policy.variable,
        draft,
        policy_type: policy.policy_type,
        policy_id: policy.id,
        version: policy.version + 1
      });
      const preview = await fetchApi<ControlPolicyPreviewResponse>("/api/control/policies/preview", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      setPolicyPreviews((current) => ({
        ...current,
        [policy.id]: preview
      }));
    } catch (previewError) {
      setError(previewError instanceof Error ? previewError.message : "No se pudo generar el preview");
    } finally {
      setBusyKey(null);
    }
  }

  function renderConflicts(conflicts: ControlPolicyConflict[]) {
    if (conflicts.length === 0) {
      return null;
    }

    return (
      <div className="control-warning-list">
        {conflicts.map((conflict) => (
          <div
            className={conflict.severity === "error" ? "control-alert control-alert-error" : "control-alert"}
            key={`${conflict.type}:${conflictingIdsKey(conflict.conflicting_policy_ids)}`}
          >
            <strong>{conflict.severity === "error" ? "Conflicto bloqueante" : "Warning de gobernanza"}</strong>
            <span>{conflict.message}</span>
            <span>Policies relacionadas: {conflict.conflicting_policy_ids.join(", ")}</span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <main className="control-dashboard">
      <section className="control-header">
        <div className="control-header-main">
          <span className="control-eyebrow">Midd IOT / Policy Management</span>
          <h1>Gestión mínima de policies</h1>
          <p>
            Alta, edición operativa y deshabilitación de <code>project_control_policies</code> desde
            <code> apps/topology-next </code>
            , manteniendo el runtime desacoplado y usando PostgreSQL como source of truth.
          </p>
        </div>
        <div className="control-header-meta">
          <Link className="control-nav-link" href="/control">
            Volver a Dashboard de Control
          </Link>
          <Link className="control-nav-link" href="/">
            Volver a Topología
          </Link>
          <span className="control-loaded-at">
            Policies cargadas: {loading ? "..." : String(policies.length)}
          </span>
        </div>
      </section>

      <section className="control-alert">
        <strong>Nota operacional</strong>
        <span>
          La UI no ejecuta control. Solo administra rows de PostgreSQL; el runtime sigue leyendo desde
          <code> project_control_policies </code>
          y solo actuará si el proyecto tiene <code>parametric_control_enabled = true</code>.
        </span>
      </section>

      {error ? (
        <section className="control-alert control-alert-error">
          <strong>No se pudo completar la operación.</strong>
          <span>{error}</span>
        </section>
      ) : null}

      {notice ? (
        <section className="control-alert">
          <strong>Operación completada.</strong>
          <span>{notice}</span>
        </section>
      ) : null}

      <section className="control-panel">
        <div className="control-panel-heading">
          <div>
            <span className="panel-kicker">Write path</span>
            <h2>Crear policy</h2>
          </div>
        </div>

        <form className="control-form-grid" onSubmit={handleCreate}>
          <label className="control-field">
            <span>Proyecto</span>
            <select
              className="input-select"
              value={createForm.project_id}
              onChange={(event) => setCreateForm((current) => ({ ...current, project_id: event.target.value }))}
            >
              {projects.length === 0 ? <option value="">Sin proyectos</option> : null}
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name} · {project.id}
                </option>
              ))}
            </select>
          </label>

          <label className="control-field">
            <span>Variable</span>
            <input
              className="input-text"
              value={createForm.variable}
              onChange={(event) => setCreateForm((current) => ({ ...current, variable: event.target.value }))}
              placeholder="tank_level"
            />
          </label>

          <label className="control-field">
            <span>Policy type</span>
            <select
              className="input-select"
              value={createForm.policy_type}
              onChange={(event) => handlePolicyTypeChange(event.target.value as ControlPolicyCreateFormState["policy_type"])}
            >
              <option value="proportional">proportional</option>
              <option value="threshold">threshold</option>
            </select>
          </label>

          <label className="control-field">
            <span>Priority</span>
            <input
              className="input-text"
              value={createForm.priority}
              onChange={(event) => setCreateForm((current) => ({ ...current, priority: event.target.value }))}
              inputMode="numeric"
            />
          </label>

          <label className="control-field control-field-wide">
            <span>Params JSON</span>
            <textarea
              className="control-textarea"
              value={createForm.params_text}
              onChange={(event) => setCreateForm((current) => ({ ...current, params_text: event.target.value }))}
              rows={10}
            />
          </label>

          <label className="control-field control-field-wide">
            <span>Context selector JSON</span>
            <textarea
              className="control-textarea"
              value={createForm.context_selector_text}
              onChange={(event) => setCreateForm((current) => ({ ...current, context_selector_text: event.target.value }))}
              rows={6}
            />
          </label>

          <label className="control-field control-field-wide">
            <span>Preview context JSON</span>
            <textarea
              className="control-textarea"
              value={createForm.preview_context_text}
              onChange={(event) => setCreateForm((current) => ({ ...current, preview_context_text: event.target.value }))}
              rows={4}
            />
          </label>

          <label className="check-row">
            <input
              type="checkbox"
              checked={createForm.enabled}
              onChange={(event) => setCreateForm((current) => ({ ...current, enabled: event.target.checked }))}
            />
            <span>Enabled</span>
          </label>

          <div className="control-actions">
            <button className="btn btn-primary" disabled={busyKey === "create"} type="submit">
              {busyKey === "create" ? "Creando..." : "Crear policy"}
            </button>
            <button
              className="btn btn-secondary"
              disabled={busyKey === "preview:create"}
              onClick={() => void handleCreatePreview()}
              type="button"
            >
              {busyKey === "preview:create" ? "Calculando..." : "Preview selección"}
            </button>
          </div>
        </form>

        {createPreview ? (
          <div className="control-preview-panel">
            <strong>Resultado del preview</strong>
            <span>{previewSummaryText(createPreview)}</span>
            {createPreview.current_selected_policy ? (
              <span>
                Selección actual: <code>{createPreview.current_selected_policy.id}</code>
              </span>
            ) : (
              <span>No hay selección actual para ese contexto.</span>
            )}
            {renderConflicts(createPreview.conflicts)}
            {createPreview.warnings.length > 0 ? (
              <div className="control-warning-list">
                {createPreview.warnings.map((warning) => (
                  <div className="control-alert" key={warning}>
                    <strong>Warning</strong>
                    <span>{warning}</span>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
      </section>

      <section className="control-panel">
        <div className="control-panel-heading">
          <div>
            <span className="panel-kicker">Read / Write</span>
            <h2>Policies actuales</h2>
          </div>
        </div>

        {loading ? (
          <p className="control-empty">Cargando policies...</p>
        ) : policies.length === 0 ? (
          <p className="control-empty">No hay policies persistidas todavía.</p>
        ) : (
          <div className="control-policy-grid">
            {policies.map((policy) => {
              const draft = drafts[policy.id];
              const listWarnings = collectListWarnings(policy, policies);
              const preview = policyPreviews[policy.id] ?? null;

              return (
                <article className="control-policy-card" key={policy.id}>
                  <div className="control-policy-card-header">
                    <div>
                      <span className="panel-kicker">{policy.policy_type}</span>
                      <h3>{policy.variable}</h3>
                      <p className="control-policy-meta">
                        project_id: <code>{policy.project_id}</code>
                      </p>
                    </div>
                    <div className="control-policy-badges">
                      <span className={policy.enabled ? "status-badge status-active" : "status-badge status-inactive"}>
                        {policy.enabled ? "enabled" : "disabled"}
                      </span>
                      <span className="status-badge">priority {policy.priority}</span>
                      <span className="status-badge">v{policy.version}</span>
                    </div>
                  </div>

                  <div className="control-policy-meta-grid">
                    <div>
                      <span className="control-stat-label">Creada</span>
                      <strong>{formatControlTimestamp(policy.created_at)}</strong>
                    </div>
                    <div>
                      <span className="control-stat-label">Actualizada</span>
                      <strong>{formatControlTimestamp(policy.updated_at)}</strong>
                    </div>
                    <div>
                      <span className="control-stat-label">ID</span>
                      <strong className="control-code-text">{policy.id}</strong>
                    </div>
                  </div>

                  {renderConflicts(listWarnings)}

                  {draft ? (
                    <div className="control-form-grid">
                      <label className="control-field control-field-wide">
                        <span>Params JSON</span>
                        <textarea
                          className="control-textarea"
                          value={draft.params_text}
                          onChange={(event) => updateDraft(policy.id, { params_text: event.target.value })}
                          rows={10}
                        />
                      </label>

                      <label className="control-field control-field-wide">
                        <span>Context selector JSON</span>
                        <textarea
                          className="control-textarea"
                          value={draft.context_selector_text}
                          onChange={(event) => updateDraft(policy.id, { context_selector_text: event.target.value })}
                          rows={6}
                        />
                      </label>

                      <label className="control-field control-field-wide">
                        <span>Preview context JSON</span>
                        <textarea
                          className="control-textarea"
                          value={draft.preview_context_text}
                          onChange={(event) => updateDraft(policy.id, { preview_context_text: event.target.value })}
                          rows={4}
                        />
                      </label>

                      <label className="control-field">
                        <span>Priority</span>
                        <input
                          className="input-text"
                          value={draft.priority}
                          onChange={(event) => updateDraft(policy.id, { priority: event.target.value })}
                          inputMode="numeric"
                        />
                      </label>

                      <label className="check-row">
                        <input
                          type="checkbox"
                          checked={draft.enabled}
                          onChange={(event) => updateDraft(policy.id, { enabled: event.target.checked })}
                        />
                        <span>Enabled</span>
                      </label>

                      <div className="control-actions">
                        <button
                          className="btn btn-secondary"
                          disabled={busyKey === `preview:${policy.id}`}
                          onClick={() => void handlePolicyPreview(policy)}
                          type="button"
                        >
                          {busyKey === `preview:${policy.id}` ? "Calculando..." : "Preview selección"}
                        </button>
                        <button
                          className="btn btn-primary"
                          disabled={busyKey === `save:${policy.id}`}
                          onClick={() => void handleSave(policy.id)}
                          type="button"
                        >
                          {busyKey === `save:${policy.id}` ? "Guardando..." : "Guardar cambios"}
                        </button>
                        <button
                          className="btn btn-secondary"
                          disabled={busyKey === `disable:${policy.id}` || !policy.enabled}
                          onClick={() => void handleDisable(policy.id)}
                          type="button"
                        >
                          {busyKey === `disable:${policy.id}` ? "Deshabilitando..." : "Deshabilitar"}
                        </button>
                      </div>

                      {preview ? (
                        <div className="control-preview-panel control-field-wide">
                          <strong>Resultado del preview</strong>
                          <span>{previewSummaryText(preview)}</span>
                          {preview.current_selected_policy ? (
                            <span>
                              Selección actual: <code>{preview.current_selected_policy.id}</code>
                            </span>
                          ) : (
                            <span>No hay selección actual para ese contexto.</span>
                          )}
                          {renderConflicts(preview.conflicts)}
                          {preview.warnings.length > 0 ? (
                            <div className="control-warning-list">
                              {preview.warnings.map((warning) => (
                                <div className="control-alert" key={warning}>
                                  <strong>Warning</strong>
                                  <span>{warning}</span>
                                </div>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}

function conflictingIdsKey(ids: string[]) {
  return ids.slice().sort().join(":");
}
