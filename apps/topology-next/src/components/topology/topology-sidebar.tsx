"use client";

import { TopologyFilters } from "@/components/topology/topology-filters";
import { TopologyPalette } from "@/components/topology/topology-palette";
import { TopologyStatusBadge } from "@/components/topology/topology-status-badge";
import { TopologyStyleEditor } from "@/components/topology/topology-style-editor";
import type { ProjectTopologyStyles } from "@/components/topology/topology-style";
import type { ApiAsset, ApiProject, ApiSector } from "@/components/topology/types";

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
  mode: "design" | "operation";
  projectStyles: ProjectTopologyStyles;
  isProjectStylesDirty: boolean;
  onProjectSelect: (projectId: string) => void;
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
}

export function TopologySidebar(props: TopologySidebarProps) {
  const assetsBySector = new Map<string, ApiAsset[]>();
  for (const asset of props.assets) {
    const list = assetsBySector.get(asset.sector_id) ?? [];
    list.push(asset);
    assetsBySector.set(asset.sector_id, list);
  }

  return (
    <aside className="topology-sidebar">
      <section className="panel-block">
        <h2>Proyecto</h2>
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
      </section>

      <section className="panel-block">
        <h2>Búsqueda</h2>
        <input
          className="input-text full"
          value={props.search}
          onChange={(event) => props.onSearchChange(event.target.value)}
          placeholder="nombre, subtype..."
        />
      </section>

      <section className="panel-block">
        <h2>Paleta</h2>
        <TopologyPalette
          onCreateSector={props.onCreateSector}
          onCreateNode={props.onCreateNode}
          onCreateSensor={props.onCreateSensor}
          onCreateActuator={props.onCreateActuator}
        />
      </section>

      <TopologyStyleEditor
        project={props.project}
        mode={props.mode}
        styles={props.projectStyles}
        isDirty={props.isProjectStylesDirty}
        onChange={props.onProjectStylesChange}
      />

      <section className="panel-block">
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

      <section className="panel-block">
        <h2>Árbol</h2>
        <div className="tree-list">
          {props.sectors.map((sector) => {
            const sectorAssets = assetsBySector.get(sector.id) ?? [];
            return (
              <details key={sector.id} open>
                <summary>{sector.name}</summary>
                <ul>
                  {sectorAssets.map((asset) => (
                    <li key={asset.id}>
                      <span>{asset.name}</span>
                      <TopologyStatusBadge status={asset.status} />
                    </li>
                  ))}
                  {sectorAssets.length === 0 ? <li className="tree-empty">Sin activos</li> : null}
                </ul>
              </details>
            );
          })}
        </div>
      </section>
    </aside>
  );
}
