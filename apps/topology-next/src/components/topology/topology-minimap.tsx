"use client";

import { MiniMap } from "@xyflow/react";
import type { TopologyNodeData } from "@/components/topology/topology-store";

export function TopologyMiniMap() {
  return (
    <MiniMap
      pannable
      zoomable
      nodeColor={(node) => {
        const nodeData = node.data as TopologyNodeData | undefined;
        return nodeData?.fillColor ?? (node.type === "sectorGroup" ? "#bfdbfe" : "#dbeafe");
      }}
      maskColor="rgba(15, 23, 42, 0.1)"
    />
  );
}
