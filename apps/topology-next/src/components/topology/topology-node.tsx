"use client";

import { Handle, NodeResizer, Position, type NodeProps } from "@xyflow/react";
import type { CSSProperties } from "react";
import type { TopologyNodeData } from "@/components/topology/topology-store";
import { TopologyStatusBadge } from "@/components/topology/topology-status-badge";

const ASSET_ICON: Record<string, string> = {
  programmable_node: "🧠",
  sensor: "📟",
  actuator: "⚙️",
  gateway: "🛰️",
  relay_module: "🔌",
  camera: "📷",
  power_unit: "🔋"
};

export function TopologyAssetNode({ data, selected }: NodeProps) {
  const nodeData = data as TopologyNodeData;
  const icon = ASSET_ICON[nodeData.assetType ?? "programmable_node"] ?? "📦";
  const nodeStyle = {
    "--node-fill": nodeData.fillColor,
    "--node-stroke": nodeData.strokeColor,
    "--node-text": nodeData.textColor
  } as CSSProperties;
  return (
    <div
      className={selected ? "asset-node asset-node-selected" : "asset-node"}
      style={nodeStyle}
      title={nodeData.issues.map((i) => i.message).join("\n")}
    >
      <NodeResizer
        isVisible={selected && nodeData.mode === "design"}
        minWidth={160}
        minHeight={96}
        keepAspectRatio={nodeData.shape === "circle"}
        lineClassName="node-resize-line"
        handleClassName="node-resize-handle"
      />
      <Handle type="target" position={Position.Top} />
      <div className="asset-node-shell">
        <div className={`asset-node-frame node-shape-${nodeData.shape}`} />
        <div className="asset-node-content">
          <div className="asset-node-header">
            <span className="asset-icon">{icon}</span>
            <div className="asset-node-copy">
              <p className="asset-title">{nodeData.label}</p>
              <p className="asset-subtitle">{nodeData.subtitle}</p>
            </div>
          </div>
          <div className="asset-node-footer">
            <TopologyStatusBadge status={nodeData.status} />
            {nodeData.issueCount > 0 ? <span className="issue-pill">{nodeData.issueCount}</span> : null}
          </div>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

export function TopologySectorNode({ data, selected }: NodeProps) {
  const nodeData = data as TopologyNodeData;
  const nodeStyle = {
    "--node-fill": nodeData.fillColor,
    "--node-stroke": nodeData.strokeColor,
    "--node-text": nodeData.textColor
  } as CSSProperties;
  return (
    <div className={selected ? "sector-node sector-node-selected" : "sector-node"} style={nodeStyle}>
      <NodeResizer
        isVisible={selected && nodeData.mode === "design"}
        minWidth={360}
        minHeight={300}
        keepAspectRatio={nodeData.shape === "circle"}
        lineClassName="node-resize-line"
        handleClassName="node-resize-handle"
      />
      <Handle type="target" position={Position.Left} />
      <div className="sector-node-shell">
        <div className={`sector-node-frame node-shape-${nodeData.shape}`} />
        <div className="sector-node-header">
          <strong className="sector-title">{nodeData.label}</strong>
          <span className="sector-subtitle">{nodeData.subtitle}</span>
          {nodeData.issueCount > 0 ? <span className="issue-pill">{nodeData.issueCount}</span> : null}
        </div>
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
