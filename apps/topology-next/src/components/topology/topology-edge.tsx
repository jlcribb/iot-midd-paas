"use client";

import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from "@xyflow/react";
import type { TopologyEdgeData } from "@/components/topology/topology-store";

export function TopologyEdge(props: EdgeProps) {
  const edgeData = (props.data ?? {}) as TopologyEdgeData;
  const [path, labelX, labelY] = getBezierPath({
    sourceX: props.sourceX,
    sourceY: props.sourceY,
    sourcePosition: props.sourcePosition,
    targetX: props.targetX,
    targetY: props.targetY,
    targetPosition: props.targetPosition
  });

  const strokeColor = edgeData.status === "fault" ? "#dc2626" : "#2563eb";
  return (
    <>
      <BaseEdge path={path} style={{ stroke: strokeColor, strokeWidth: 2 }} />
      <EdgeLabelRenderer>
        <div
          style={{
            position: "absolute",
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            background: "#ffffff",
            border: "1px solid #cbd5e1",
            borderRadius: 6,
            fontSize: 11,
            padding: "2px 6px",
            pointerEvents: "all"
          }}
        >
          {props.label}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
