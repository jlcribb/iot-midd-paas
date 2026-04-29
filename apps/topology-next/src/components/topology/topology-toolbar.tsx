"use client";

import Link from "next/link";
import type { ApiProject, GraphIssue, ViewMode, ViewType } from "@/components/topology/types";

interface TopologyToolbarProps {
  project: ApiProject | null;
  mode: ViewMode;
  viewType: ViewType;
  issues: GraphIssue[];
  isDirty: boolean;
  isSavingLayout: boolean;
  onModeChange: (mode: ViewMode) => void;
  onViewTypeChange: (viewType: ViewType) => void;
  onSaveLayout: () => void;
  onAutoLayout: () => void;
  onValidate: () => void;
  onCenter: () => void;
  onRefresh: () => void;
}

export function TopologyToolbar(props: TopologyToolbarProps) {
  const errorCount = props.issues.filter((item) => item.severity === "error").length;
  const warningCount = props.issues.filter((item) => item.severity === "warning").length;

  return (
    <header className="topology-toolbar">
      <div className="toolbar-title">
        <h1>Project Topology Workspace</h1>
        <p>{props.project ? `${props.project.name} (${props.project.status})` : "Selecciona un proyecto"}</p>
      </div>

      <div className="toolbar-controls">
        <select
          value={props.viewType}
          onChange={(event) => props.onViewTypeChange(event.target.value as ViewType)}
          className="input-select"
        >
          <option value="logical">Vista lógica</option>
          <option value="physical">Vista física</option>
          <option value="geographic">Vista geográfica (base)</option>
        </select>

        <div className="btn-group">
          <button
            type="button"
            className={props.mode === "design" ? "btn btn-primary" : "btn btn-secondary"}
            onClick={() => props.onModeChange("design")}
          >
            Diseño
          </button>
          <button
            type="button"
            className={props.mode === "operation" ? "btn btn-primary" : "btn btn-secondary"}
            onClick={() => props.onModeChange("operation")}
          >
            Operación
          </button>
        </div>

        <button
          type="button"
          className="btn btn-primary"
          onClick={props.onSaveLayout}
          disabled={!props.isDirty || props.isSavingLayout}
        >
          {props.isSavingLayout ? "Guardando..." : "Guardar workspace"}
        </button>
        <button type="button" className="btn btn-secondary" onClick={props.onAutoLayout}>
          Auto organizar
        </button>
        <button type="button" className="btn btn-secondary" onClick={props.onValidate}>
          Validar topología
        </button>
        <button type="button" className="btn btn-secondary" onClick={props.onCenter}>
          Vista panorámica
        </button>
        <button type="button" className="btn btn-secondary" onClick={props.onRefresh}>
          Refrescar
        </button>
        <Link href="/control" className="btn btn-secondary">
          Control Engine
        </Link>
      </div>

      <div className="toolbar-health">
        <span className="health-chip">{warningCount} warnings</span>
        <span className={errorCount > 0 ? "health-chip health-chip-error" : "health-chip"}>{errorCount} errors</span>
      </div>
    </header>
  );
}
