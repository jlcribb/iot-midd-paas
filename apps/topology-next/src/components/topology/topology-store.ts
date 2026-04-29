"use client";

import { create } from "zustand";
import type { Edge, Node } from "@xyflow/react";
import type { ApiAsset, ApiProject, ApiSector, ApiTopologyLink, ApiTopologyView, GraphIssue, ViewMode, ViewType } from "@/components/topology/types";
import type { NodeShape } from "@/components/topology/topology-style";

export interface TopologyNodeData extends Record<string, unknown> {
  kind: "sector" | "asset";
  mode: ViewMode;
  entityId: string;
  label: string;
  subtitle: string;
  status: string;
  assetType?: ApiAsset["asset_type"];
  sectorId?: string;
  shape: NodeShape;
  fillColor: string;
  strokeColor: string;
  textColor: string;
  issueCount: number;
  issues: GraphIssue[];
}

export interface TopologyEdgeData extends Record<string, unknown> {
  kind: "hierarchy" | "topology";
  entityId: string;
  relationType?: ApiTopologyLink["relation_type"];
  status?: ApiTopologyLink["status"];
  issues: GraphIssue[];
}

interface TopologyUiState {
  mode: ViewMode;
  viewType: ViewType;
  gridEnabled: boolean;
  search: string;
  sectorFilters: string[];
  typeFilters: ApiAsset["asset_type"][];
  statusFilters: ApiAsset["status"][];
  showHierarchyEdges: boolean;
  showTopologyEdges: boolean;
  selectedProjectId: string | null;
  selectedViewId: string | null;
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  isDirty: boolean;
  isLoading: boolean;
  isSavingLayout: boolean;
  errorMessage: string | null;
  projects: ApiProject[];
  sectors: ApiSector[];
  assets: ApiAsset[];
  topologyLinks: ApiTopologyLink[];
  topologyViews: ApiTopologyView[];
  issues: GraphIssue[];
  nodes: Node[];
  edges: Edge[];
  setMode: (mode: ViewMode) => void;
  setViewType: (viewType: ViewType) => void;
  setGridEnabled: (enabled: boolean) => void;
  setSearch: (value: string) => void;
  setSectorFilters: (filters: string[]) => void;
  setTypeFilters: (filters: ApiAsset["asset_type"][]) => void;
  setStatusFilters: (filters: ApiAsset["status"][]) => void;
  setShowHierarchyEdges: (value: boolean) => void;
  setShowTopologyEdges: (value: boolean) => void;
  setSelectedProjectId: (projectId: string | null) => void;
  setSelectedViewId: (viewId: string | null) => void;
  setSelectedNodeId: (nodeId: string | null) => void;
  setSelectedEdgeId: (edgeId: string | null) => void;
  setIsDirty: (value: boolean) => void;
  setIsLoading: (value: boolean) => void;
  setIsSavingLayout: (value: boolean) => void;
  setErrorMessage: (message: string | null) => void;
  setProjects: (data: ApiProject[]) => void;
  setSectors: (data: ApiSector[]) => void;
  setAssets: (data: ApiAsset[]) => void;
  setTopologyLinks: (data: ApiTopologyLink[]) => void;
  setTopologyViews: (data: ApiTopologyView[]) => void;
  setIssues: (issues: GraphIssue[]) => void;
  setGraph: (params: { nodes: Node[]; edges: Edge[] }) => void;
}

export const useTopologyStore = create<TopologyUiState>((set) => ({
  mode: "design",
  viewType: "logical",
  gridEnabled: true,
  search: "",
  sectorFilters: [],
  typeFilters: [],
  statusFilters: [],
  showHierarchyEdges: true,
  showTopologyEdges: true,
  selectedProjectId: null,
  selectedViewId: null,
  selectedNodeId: null,
  selectedEdgeId: null,
  isDirty: false,
  isLoading: false,
  isSavingLayout: false,
  errorMessage: null,
  projects: [],
  sectors: [],
  assets: [],
  topologyLinks: [],
  topologyViews: [],
  issues: [],
  nodes: [],
  edges: [],
  setMode: (mode) => set((state) => (state.mode === mode ? state : { mode })),
  setViewType: (viewType) => set((state) => (state.viewType === viewType ? state : { viewType })),
  setGridEnabled: (gridEnabled) => set((state) => (state.gridEnabled === gridEnabled ? state : { gridEnabled })),
  setSearch: (search) => set((state) => (state.search === search ? state : { search })),
  setSectorFilters: (sectorFilters) => set((state) => (state.sectorFilters === sectorFilters ? state : { sectorFilters })),
  setTypeFilters: (typeFilters) => set((state) => (state.typeFilters === typeFilters ? state : { typeFilters })),
  setStatusFilters: (statusFilters) => set((state) => (state.statusFilters === statusFilters ? state : { statusFilters })),
  setShowHierarchyEdges: (showHierarchyEdges) =>
    set((state) => (state.showHierarchyEdges === showHierarchyEdges ? state : { showHierarchyEdges })),
  setShowTopologyEdges: (showTopologyEdges) =>
    set((state) => (state.showTopologyEdges === showTopologyEdges ? state : { showTopologyEdges })),
  setSelectedProjectId: (selectedProjectId) =>
    set((state) => (state.selectedProjectId === selectedProjectId ? state : { selectedProjectId })),
  setSelectedViewId: (selectedViewId) => set((state) => (state.selectedViewId === selectedViewId ? state : { selectedViewId })),
  setSelectedNodeId: (selectedNodeId) => set((state) => (state.selectedNodeId === selectedNodeId ? state : { selectedNodeId })),
  setSelectedEdgeId: (selectedEdgeId) => set((state) => (state.selectedEdgeId === selectedEdgeId ? state : { selectedEdgeId })),
  setIsDirty: (isDirty) => set((state) => (state.isDirty === isDirty ? state : { isDirty })),
  setIsLoading: (isLoading) => set((state) => (state.isLoading === isLoading ? state : { isLoading })),
  setIsSavingLayout: (isSavingLayout) => set((state) => (state.isSavingLayout === isSavingLayout ? state : { isSavingLayout })),
  setErrorMessage: (errorMessage) => set((state) => (state.errorMessage === errorMessage ? state : { errorMessage })),
  setProjects: (projects) => set((state) => (state.projects === projects ? state : { projects })),
  setSectors: (sectors) => set((state) => (state.sectors === sectors ? state : { sectors })),
  setAssets: (assets) => set((state) => (state.assets === assets ? state : { assets })),
  setTopologyLinks: (topologyLinks) => set((state) => (state.topologyLinks === topologyLinks ? state : { topologyLinks })),
  setTopologyViews: (topologyViews) => set((state) => (state.topologyViews === topologyViews ? state : { topologyViews })),
  setIssues: (issues) => set((state) => (state.issues === issues ? state : { issues })),
  setGraph: ({ nodes, edges }) => set((state) => (state.nodes === nodes && state.edges === edges ? state : { nodes, edges }))
}));
