"use client";

import { useEffect, useMemo, useState } from "react";
import type { Edge, Node } from "@xyflow/react";
import type { TopologyEdgeData, TopologyNodeData } from "@/components/topology/topology-store";
import type { ApiAsset, ApiSector, ApiTopologyLink } from "@/components/topology/types";
import { TopologyStatusBadge } from "@/components/topology/topology-status-badge";

interface TopologyInspectorProps {
  selectedNode: Node | null;
  selectedEdge: Edge | null;
  assets: ApiAsset[];
  sectors: ApiSector[];
  topologyLinks: ApiTopologyLink[];
  mode: "design" | "operation";
  onUpdateAsset: (id: string, payload: Partial<ApiAsset>) => Promise<void>;
  onUpdateSector: (id: string, payload: Partial<ApiSector>) => Promise<void>;
  onUpdateTopologyLink: (id: string, payload: Partial<ApiTopologyLink>) => Promise<void>;
  onDeleteAsset: (id: string) => Promise<void>;
  onDeleteSector: (id: string) => Promise<void>;
  onDeleteTopologyLink: (id: string) => Promise<void>;
}

export function TopologyInspector(props: TopologyInspectorProps) {
  const selectedNodeData = props.selectedNode?.data as TopologyNodeData | undefined;
  const selectedEdgeData = props.selectedEdge?.data as TopologyEdgeData | undefined;

  const selectedAsset = useMemo(() => {
    if (!selectedNodeData || selectedNodeData.kind !== "asset") return null;
    return props.assets.find((item) => item.id === selectedNodeData.entityId) ?? null;
  }, [props.assets, selectedNodeData]);

  const selectedSector = useMemo(() => {
    if (!selectedNodeData || selectedNodeData.kind !== "sector") return null;
    return props.sectors.find((item) => item.id === selectedNodeData.entityId) ?? null;
  }, [props.sectors, selectedNodeData]);

  const selectedTopologyLink = useMemo(() => {
    if (!selectedEdgeData || selectedEdgeData.kind !== "topology") return null;
    return props.topologyLinks.find((item) => item.id === selectedEdgeData.entityId) ?? null;
  }, [props.topologyLinks, selectedEdgeData]);

  const [assetName, setAssetName] = useState("");
  const [assetSubtype, setAssetSubtype] = useState("");
  const [assetStatus, setAssetStatus] = useState<ApiAsset["status"]>("active");
  const [sectorName, setSectorName] = useState("");
  const [sectorCode, setSectorCode] = useState("");
  const [relationType, setRelationType] = useState<ApiTopologyLink["relation_type"]>("connects_to");
  const [relationStatus, setRelationStatus] = useState<ApiTopologyLink["status"]>("active");

  useEffect(() => {
    if (!selectedAsset) return;
    setAssetName(selectedAsset.name);
    setAssetSubtype(selectedAsset.subtype);
    setAssetStatus(selectedAsset.status);
  }, [selectedAsset]);

  useEffect(() => {
    if (!selectedSector) return;
    setSectorName(selectedSector.name);
    setSectorCode(selectedSector.code ?? "");
  }, [selectedSector]);

  useEffect(() => {
    if (!selectedTopologyLink) return;
    setRelationType(selectedTopologyLink.relation_type);
    setRelationStatus(selectedTopologyLink.status);
  }, [selectedTopologyLink]);

  if (!props.selectedNode && !props.selectedEdge) {
    return (
      <aside className="topology-inspector">
        <h2>Inspector</h2>
        <p>Selecciona un nodo o enlace para editar propiedades.</p>
      </aside>
    );
  }

  if (selectedAsset) {
    return (
      <aside className="topology-inspector">
        <h2>Inspector: Asset</h2>
        <p className="inspector-subtitle">{selectedAsset.asset_type}</p>
        <TopologyStatusBadge status={selectedAsset.status} />

        <label className="input-label">
          Nombre
          <input
            className="input-text full"
            value={assetName}
            onChange={(event) => setAssetName(event.target.value)}
            disabled={props.mode !== "design"}
          />
        </label>
        <label className="input-label">
          Subtype
          <input
            className="input-text full"
            value={assetSubtype}
            onChange={(event) => setAssetSubtype(event.target.value)}
            disabled={props.mode !== "design"}
          />
        </label>
        <label className="input-label">
          Estado
          <select
            className="input-select full"
            value={assetStatus}
            onChange={(event) => setAssetStatus(event.target.value as ApiAsset["status"])}
            disabled={props.mode !== "design"}
          >
            <option value="online">online</option>
            <option value="active">active</option>
            <option value="offline">offline</option>
            <option value="inactive">inactive</option>
            <option value="fault">fault</option>
            <option value="maintenance">maintenance</option>
            <option value="provisioning">provisioning</option>
            <option value="retired">retired</option>
          </select>
        </label>

        {props.mode === "design" ? (
          <div className="btn-row">
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => props.onUpdateAsset(selectedAsset.id, { name: assetName, subtype: assetSubtype, status: assetStatus })}
            >
              Guardar cambios
            </button>
            <button
              type="button"
              className="btn btn-danger"
              onClick={async () => {
                const confirmed = window.confirm("¿Eliminar lógicamente este asset y su subárbol?");
                if (!confirmed) return;
                await props.onDeleteAsset(selectedAsset.id);
              }}
            >
              Eliminar
            </button>
          </div>
        ) : null}

        <div className="inspector-issues">
          {(selectedNodeData?.issues ?? []).map((issue) => (
            <p key={issue.message} className={issue.severity === "error" ? "issue-error" : "issue-warning"}>
              {issue.message}
            </p>
          ))}
        </div>
      </aside>
    );
  }

  if (selectedSector) {
    return (
      <aside className="topology-inspector">
        <h2>Inspector: Sector</h2>
        <label className="input-label">
          Nombre
          <input
            className="input-text full"
            value={sectorName}
            onChange={(event) => setSectorName(event.target.value)}
            disabled={props.mode !== "design"}
          />
        </label>
        <label className="input-label">
          Código
          <input
            className="input-text full"
            value={sectorCode}
            onChange={(event) => setSectorCode(event.target.value)}
            disabled={props.mode !== "design"}
          />
        </label>
        {props.mode === "design" ? (
          <div className="btn-row">
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => props.onUpdateSector(selectedSector.id, { name: sectorName, code: sectorCode || null })}
            >
              Guardar cambios
            </button>
            <button
              type="button"
              className="btn btn-danger"
              onClick={async () => {
                const confirmed = window.confirm("¿Eliminar lógicamente este sector y sus activos?");
                if (!confirmed) return;
                await props.onDeleteSector(selectedSector.id);
              }}
            >
              Eliminar
            </button>
          </div>
        ) : null}
      </aside>
    );
  }

  if (selectedTopologyLink) {
    return (
      <aside className="topology-inspector">
        <h2>Inspector: Link topológico</h2>
        <label className="input-label">
          Relación
          <select
            className="input-select full"
            value={relationType}
            onChange={(event) => setRelationType(event.target.value as ApiTopologyLink["relation_type"])}
            disabled={props.mode !== "design"}
          >
            <option value="contains">contains</option>
            <option value="hosts">hosts</option>
            <option value="reads">reads</option>
            <option value="controls">controls</option>
            <option value="connects_to">connects_to</option>
            <option value="routes_to">routes_to</option>
            <option value="depends_on">depends_on</option>
            <option value="powered_by">powered_by</option>
            <option value="mounted_on">mounted_on</option>
          </select>
        </label>
        <label className="input-label">
          Estado
          <select
            className="input-select full"
            value={relationStatus}
            onChange={(event) => setRelationStatus(event.target.value as ApiTopologyLink["status"])}
            disabled={props.mode !== "design"}
          >
            <option value="planned">planned</option>
            <option value="active">active</option>
            <option value="inactive">inactive</option>
            <option value="fault">fault</option>
            <option value="retired">retired</option>
          </select>
        </label>
        {props.mode === "design" ? (
          <div className="btn-row">
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => props.onUpdateTopologyLink(selectedTopologyLink.id, { relation_type: relationType, status: relationStatus })}
            >
              Guardar cambios
            </button>
            <button
              type="button"
              className="btn btn-danger"
              onClick={async () => {
                const confirmed = window.confirm("¿Eliminar el link topológico?");
                if (!confirmed) return;
                await props.onDeleteTopologyLink(selectedTopologyLink.id);
              }}
            >
              Eliminar
            </button>
          </div>
        ) : null}
      </aside>
    );
  }

  return (
    <aside className="topology-inspector">
      <h2>Inspector</h2>
      <p>El enlace de jerarquía se deriva de parent_asset_id y se edita desde el asset hijo.</p>
    </aside>
  );
}
