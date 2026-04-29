"use client";

import {
  Background,
  Connection,
  Controls,
  ReactFlow,
  applyEdgeChanges,
  applyNodeChanges,
  type Edge,
  type EdgeChange,
  type Node,
  type NodeChange,
  type OnConnect,
  type ReactFlowInstance
} from "@xyflow/react";
import { useCallback, useMemo } from "react";
import { TopologyAssetNode, TopologySectorNode } from "@/components/topology/topology-node";
import { TopologyEdge } from "@/components/topology/topology-edge";
import { TopologyMiniMap } from "@/components/topology/topology-minimap";

interface TopologyCanvasProps {
  nodes: Node[];
  edges: Edge[];
  mode: "design" | "operation";
  gridEnabled: boolean;
  onNodesChange: (nodes: Node[], changes: NodeChange[]) => void;
  onEdgesChange: (edges: Edge[]) => void;
  onSelectionChange: (selection: { nodeId: string | null; edgeId: string | null }) => void;
  onConnect: OnConnect;
  onNodeDragStop: () => void;
  onReady: (instance: ReactFlowInstance) => void;
}

const nodeTypes = {
  topologyAsset: TopologyAssetNode,
  sectorGroup: TopologySectorNode
};

const edgeTypes = {
  topologyEdge: TopologyEdge
};

export function TopologyCanvas(props: TopologyCanvasProps) {
  const fitViewOptions = useMemo(() => ({ padding: 0.2 }), []);

  const handleNodesChange = useCallback(
    (changes: NodeChange[]) => {
      props.onNodesChange(applyNodeChanges(changes, props.nodes), changes);
    },
    [props.nodes, props.onNodesChange]
  );

  const handleEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      props.onEdgesChange(applyEdgeChanges(changes, props.edges));
    },
    [props.edges, props.onEdgesChange]
  );

  const handleConnect = useCallback(
    (connection: Connection) => {
      props.onConnect(connection);
    },
    [props.onConnect]
  );

  const handleSelectionChange = useCallback(
    (value: { nodes: Node[]; edges: Edge[] }) => {
      props.onSelectionChange({
        nodeId: value.nodes[0]?.id ?? null,
        edgeId: value.edges[0]?.id ?? null
      });
    },
    [props.onSelectionChange]
  );

  return (
    <div className="topology-canvas">
      <ReactFlow
        nodes={props.nodes}
        edges={props.edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={fitViewOptions}
        nodesDraggable={props.mode === "design"}
        nodesConnectable={props.mode === "design"}
        zoomOnScroll
        zoomOnPinch
        panOnScroll={false}
        minZoom={0.25}
        maxZoom={2.5}
        elementsSelectable
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={handleConnect}
        onSelectionChange={handleSelectionChange}
        onNodeDragStop={props.mode === "design" ? props.onNodeDragStop : undefined}
        onInit={props.onReady}
      >
        {props.gridEnabled ? <Background gap={18} size={1} /> : null}
        <Controls position="bottom-right" />
        <TopologyMiniMap />
      </ReactFlow>
    </div>
  );
}
