"use client";

import { TopologyFilters } from "@/components/topology/topology-filters";
import { TopologyPalette } from "@/components/topology/topology-palette";
import { TopologyStatusBadge } from "@/components/topology/topology-status-badge";
import { TopologyStyleEditor } from "@/components/topology/topology-style-editor";
import type { ProjectTopologyStyles } from "@/components/topology/topology-style";
import type { ApiAsset, ApiProject, ApiSector, GraphIssue, ViewType } from "@/components/topology/types";

const ASSET_SHORT_LABEL: Record<ApiAsset["asset_type"], string> = {
  programmable_node: "PN",
  sensor: "SN",
  actuator: "AC",
  gateway: "GW",
  relay_module: "RM",
  camera: "CM",
  power_unit: "PW"
};

const ASSET_TYPE_LABEL: Record<ApiAsset["asset_type"], string> = {
  programmable_node: "Programmable Node",
  sensor: "Sensor",
  actuator: "Actuator",
  gateway: "Gateway",
  relay_module: "Relay Module",
  camera: "Camera",
  power_unit: "Power Unit"
};

const VIEW_LABEL: Record<ViewType, string> = {
  logical: "Vista logica",
  physical: "Vista fisica",
  geographic: "Vista geografica"
};

interface TopologySidebarProps {
  projects: ApiProject[];
  project: ApiProject | null;
  selectedProjectId: string | null;
  sectors: ApiSector[];
  assets: ApiAsset[];
  search: string;
  sectorFilters: string[];
  typeFilters: ApiAsset["asset_type"][];
  statusFilters: ApiAsset["status"][];
  showHierarchyEdges: boolean;
  showTopologyEdges: boolean;
  selectedNodeId: string | null;
  issues: GraphIssue[];
  mode: "design" | "operation";
  viewType: ViewType;
  projectStyles: ProjectTopologyStyles;
  isProjectStylesDirty: boolean;
  isProjectControlTogglePending: boolean;
  projectControlToggleConfirmationTarget: boolean | null;
  canManageProjectControl: boolean;
  isProjectControlAccessLoading: boolean;
  projectControlAccessMessage: string;
  projectControlFeedback: string | null;
  onProjectSelect: (projectId: string) => void;
  onProjectControlToggle: (enabled: boolean) => void;
  onConfirmProjectControlToggle: () => void;
  onCancelProjectControlToggle: () => void;
  onSearchChange: (value: string) => void;
  onSectorFiltersChange: (value: string[]) => void;
  onTypeFiltersChange: (value: ApiAsset["asset_type"][]) => void;
  onStatusFiltersChange: (value: ApiAsset["status"][]) => void;
  onShowHierarchyEdges: (value: boolean) => void;
  onShowTopologyEdges: (value: boolean) => void;
  onProjectStylesChange: (styles: ProjectTopologyStyles) => void;
  onCreateSector: () => void;
  onCreateNode: () => void;
  onCreateSensor: () => void;
  onCreateActuator: () => void;
  onSelectNode: (nodeId: string) => void;
}

export function TopologySidebar(props: TopologySidebarProps) {
  const assetsBySector = new Map<string, ApiAsset[]>();
  for (const asset of props.assets) {
    const list = assetsBySector.get(asset.sector_id) ?? [];
    list.push(asset);
    assetsBySector.set(asset.sector_id, list);
  }

  const searchValue = props.search.trim().toLowerCase();
  const visibleAssets = props.assets
    .filter((asset) => {
      const matchesSearch =
        searchValue.length === 0 ||
        asset.name.toLowerCase().includes(searchValue) ||
        asset.subtype.toLowerCase().includes(searchValue) ||
        (asset.code ?? "").toLowerCase().includes(searchValue);
      const matchesSector = props.sectorFilters.length === 0 || props.sectorFilters.includes(asset.sector_id);
      const matchesType = props.typeFilters.length === 0 || props.typeFilters.includes(asset.asset_type);
      const matchesStatus = props.statusFilters.length === 0 || props.statusFilters.includes(asset.status);
      return matchesSearch && matchesSector && matchesType && matchesStatus;
    })
    .sort((left, right) => left.name.localeCompare(right.name));

  const warningCount = props.issues.filter((item) => item.severity === "warning").length;
  const errorCount = props.issues.filter((item) => item.severity === "error").length;
  const onlineCount = props.assets.filter((asset) => asset.status === "online" || asset.status === "active").length;
  const sectorsWithAssetsCount = props.sectors.filter((sector) => (assetsBySector.get(sector.id) ?? []).length > 0).length;

  return (
    <aside className="topology-sidebar">
      <section className="panel-block workspace-card">
        <div className="panel-heading-inline">
          <h2>Proyecto</h2>
          {props.project ? <span className="sidebar-project-status">{props.project.status}</span> : null}
        </div>
        <select
          className="input-select full"
          value={props.selectedProjectId ?? ""}
          onChange={(event) => props.onProjectSelect(event.target.value)}
        >
          {props.projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
        {props.project ? (
          <>
            <label className="check-row" aria-busy={props.isProjectControlTogglePending}>
              <input
                type="checkbox"
                checked={props.project.parametric_control_enabled}
                disabled={props.isProjectControlTogglePending || props.isProjectControlAccessLoading || !props.canManageProjectControl}
                onChange={(event) => props.onProjectControlToggle(event.target.checked)}
              />
              Control Paramétrico: {props.project.parametric_control_enabled ? "Enabled" : "Disabled"}
            </label>
            {props.isProjectControlTogglePending ? <p className="panel-note">Actualizando feature flag del proyecto...</p> : null}
            <p className="panel-note">{props.projectControlAccessMessage}</p>
            {props.projectControlFeedback ? <p className="panel-note" role="status">{props.projectControlFeedback}</p> : null}
            {props.projectControlToggleConfirmationTarget !== null ? (
              <div className="panel-note" role="status">
                <p>
                  Confirmá {props.projectControlToggleConfirmationTarget ? "habilitar" : "deshabilitar"} el control paramétrico para este proyecto.
                </p>
                <button type="button" className="btn btn-primary" onClick={props.onConfirmProjectControlToggle}>
                  Confirmar cambio
                </button>
                <button type="button" className="btn btn-secondary" onClick={props.onCancelProjectControlToggle}>
                  Cancelar
                </button>
              </div>
            ) : null}
          </>
        ) : null}
        <p className="panel-note">
          {props.project?.parametric_control_enabled
            ? "El proyecto ya puede participar del flujo runtime -> recommendation -> audit."
            : "Activa el feature flag para habilitar la capacidad C4 por proyecto."}
        </p>
      </section>

      <section className="sidebar-stat-grid">
        <article className="sidebar-stat-card">
          <span className="sidebar-stat-icon">WRN</span>
          <div>
            <p>Warnings</p>
            <strong>{warningCount}</strong>
          </div>
        </article>
        <article className="sidebar-stat-card sidebar-stat-card-danger">
          <span className="sidebar-stat-icon">ERR</span>
          <div>
            <p>Errors</p>
            <strong>{errorCount}</strong>
          </div>
        </article>
        <article className="sidebar-stat-card">
          <span className="sidebar-stat-icon">ON</span>
          <div>
            <p>Online</p>
            <strong>{onlineCount}</strong>
          </div>
        </article>
        <article className="sidebar-stat-card">
          <span className="sidebar-stat-icon">SC</span>
          <div>
            <p>Sectors</p>
            <strong>{sectorsWithAssetsCount}</strong>
          </div>
        </article>
      </section>

      <section className="panel-block workspace-card">
        <h2>Busqueda</h2>
        <label className="search-shell">
          <span className="search-icon">/</span>
          <input
            className="input-text full"
            value={props.search}
            onChange={(event) => props.onSearchChange(event.target.value)}
            placeholder="nombre, subtype, code..."
          />
        </label>
        <p className="panel-note">
          {visibleAssets.length} activos visibles en {VIEW_LABEL[props.viewType]}.
        </p>
      </section>

      <section className="panel-block workspace-card">
        <div className="panel-heading-inline">
          <h2>Paleta</h2>
          <span className="panel-muted">{props.mode === "design" ? "Modo edicion" : "Solo lectura"}</span>
        </div>
        <TopologyPalette
          disabled={props.mode !== "design"}
          onCreateSector={props.onCreateSector}
          onCreateNode={props.onCreateNode}
          onCreateSensor={props.onCreateSensor}
          onCreateActuator={props.onCreateActuator}
        />
        <p className="panel-note">
          La creacion sigue usando los handlers existentes. Si quieres modales en lugar de `prompt`, hoy ese flujo no existe.
        </p>
      </section>

      <section className="panel-block workspace-card">
        <h2>Filtros</h2>
        <TopologyFilters
          sectors={props.sectors}
          sectorFilters={props.sectorFilters}
          typeFilters={props.typeFilters}
          statusFilters={props.statusFilters}
          onSectorFiltersChange={props.onSectorFiltersChange}
          onTypeFiltersChange={props.onTypeFiltersChange}
          onStatusFiltersChange={props.onStatusFiltersChange}
        />
        <label className="check-row">
          <input
            type="checkbox"
            checked={props.showHierarchyEdges}
            onChange={(event) => props.onShowHierarchyEdges(event.target.checked)}
          />
          Mostrar jerarquía (parent_asset_id)
        </label>
        <label className="check-row">
          <input
            type="checkbox"
            checked={props.showTopologyEdges}
            onChange={(event) => props.onShowTopologyEdges(event.target.checked)}
          />
            Mostrar topología explícita
          </label>
      </section>

      <section className="panel-block workspace-card">
        <div className="panel-heading-inline">
          <h2>Active Components</h2>
          <span className="panel-muted">{visibleAssets.length} items</span>
        </div>
        <div className="component-feed">
          {props.sectors.map((sector) => {
            const sectorAssets = visibleAssets.filter((asset) => asset.sector_id === sector.id);
            const isSectorVisible =
              sectorAssets.length > 0 ||
              props.sectorFilters.includes(sector.id) ||
              (searchValue.length > 0 && sector.name.toLowerCase().includes(searchValue));
            if (!isSectorVisible) {
              return null;
            }

            return (
              <div key={sector.id} className="component-group">
                <button
                  type="button"
                  className={props.selectedNodeId === `sector:${sector.id}` ? "component-item component-item-active" : "component-item"}
                  onClick={() => props.onSelectNode(`sector:${sector.id}`)}
                >
                  <span className="component-icon">SC</span>
                  <span className="component-copy">
                    <strong>{sector.name}</strong>
                    <span>Sector · {(assetsBySector.get(sector.id) ?? []).length} assets</span>
                  </span>
                  <span className="component-trailing">{sectorAssets.length}</span>
                </button>
                {sectorAssets.map((asset) => (
                  <button
                    key={asset.id}
                    type="button"
                    className={props.selectedNodeId === `asset:${asset.id}` ? "component-item component-item-active" : "component-item"}
                    onClick={() => props.onSelectNode(`asset:${asset.id}`)}
                  >
                    <span className="component-icon">{ASSET_SHORT_LABEL[asset.asset_type]}</span>
                    <span className="component-copy">
                      <strong>{asset.name}</strong>
                      <span>
                        {ASSET_TYPE_LABEL[asset.asset_type]} · {asset.subtype}
                      </span>
                    </span>
                    <span className="component-trailing">
                      <TopologyStatusBadge status={asset.status} />
                    </span>
                  </button>
                ))}
              </div>
            );
          })}
          {visibleAssets.length === 0 ? <p className="tree-empty">No hay componentes activos para los filtros actuales.</p> : null}
        </div>
      </section>

      <section className="workspace-hero-card">
        <div className="workspace-hero-copy">
          <span className="panel-kicker">Active Topology</span>
          <h3>{props.project?.name ?? "Sin proyecto seleccionado"}</h3>
          <p>
            {props.mode === "design" ? "Edita layout, relaciones y estilos." : "Monitorea la red desde la vista operacional."}
          </p>
        </div>
        <div className="workspace-hero-meta">
          <span>{VIEW_LABEL[props.viewType]}</span>
          <span>{props.project?.parametric_control_enabled ? "Control enabled" : "Control disabled"}</span>
        </div>
      </section>

      <TopologyStyleEditor
        project={props.project}
        mode={props.mode}
        styles={props.projectStyles}
        isDirty={props.isProjectStylesDirty}
        onChange={props.onProjectStylesChange}
      />
    </aside>
  );
}
