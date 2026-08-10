"use client";

import "@xyflow/react/dist/style.css";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ReactFlowProvider,
  type Connection,
  type Edge,
  type Node,
  type NodeChange,
  type ReactFlowInstance
} from "@xyflow/react";
import {
  createAsset,
  createSector,
  createTopologyLink,
  createTopologyView,
  deleteAsset,
  deleteSector,
  deleteTopologyLink,
  getControlAccess,
  getTopologyViewLayout,
  listAssets,
  listProjects,
  listSectors,
  listTopology,
  listTopologyViews,
  saveTopologyViewLayout,
  updateProject,
  updateAsset,
  updateSector,
  updateTopologyLink
} from "@/components/topology/api";
import { buildDefaultNodeLayouts, buildGraph, normalizeNodeLayouts, parseNodeRef } from "@/components/topology/mappers";
import { resolveProjectControlUiState } from "@/components/topology/project-control-access";
import {
  getDefaultProjectTopologyStyles,
  resolveProjectTopologyStyles,
  type ProjectTopologyStyles
} from "@/components/topology/topology-style";
import { useTopologyStore, type TopologyEdgeData, type TopologyNodeData } from "@/components/topology/topology-store";
import { TopologyCanvas } from "@/components/topology/topology-canvas";
import { TopologyInspector } from "@/components/topology/topology-inspector";
import { TopologySidebar } from "@/components/topology/topology-sidebar";
import { TopologyToolbar } from "@/components/topology/topology-toolbar";
import type {
  ApiAsset,
  ApiSector,
  ApiTopologyLink,
  ApiTopologyLinkLayout,
  ApiTopologyNodeLayout,
  ViewType
} from "@/components/topology/types";
import type { ControlAccessSnapshot } from "@/lib/dto/control-access.dto";

function inferRelationType(source: ApiAsset | null, target: ApiAsset | null): ApiTopologyLink["relation_type"] {
  if (source?.asset_type === "programmable_node" && target?.asset_type === "sensor") return "reads";
  if (source?.asset_type === "programmable_node" && target?.asset_type === "actuator") return "controls";
  return "connects_to";
}

function toNodeLayouts(nodes: Node[]): ApiTopologyNodeLayout[] {
  return nodes
    .filter((node) => {
      const data = node.data as TopologyNodeData;
      return data.kind === "asset" || data.kind === "sector";
    })
    .map((node) => {
      const ref = parseNodeRef(node.id);
      return {
        asset_id: ref.kind === "asset" ? ref.id : null,
        sector_id: ref.kind === "sector" ? ref.id : null,
        x: node.position.x,
        y: node.position.y,
        width: node.width ?? null,
        height: node.height ?? null,
        collapsed: false,
        hidden: Boolean(node.hidden),
        z_index: node.zIndex ?? 0,
        metadata: {}
      };
    });
}

function toLinkLayouts(edges: Edge[]): ApiTopologyLinkLayout[] {
  return edges
    .filter((edge) => {
      const data = edge.data as TopologyEdgeData | undefined;
      return data?.kind === "topology";
    })
    .map((edge) => ({
      topology_link_id: ((edge.data as TopologyEdgeData | undefined)?.entityId ?? edge.id),
      hidden: Boolean(edge.hidden),
      label_offset_x: 0,
      label_offset_y: 0,
      metadata: {}
    }));
}

export function TopologyWorkspace() {
  const flowRef = useRef<ReactFlowInstance | null>(null);
  const initialProjectFromQueryRef = useRef<string | null>(null);
  const initialViewTypeFromQueryRef = useRef<ViewType | null>(null);
  const workspaceLoadSequenceRef = useRef(0);
  const [projectStylesDraft, setProjectStylesDraft] = useState<ProjectTopologyStyles>(getDefaultProjectTopologyStyles);
  const [isProjectControlTogglePending, setIsProjectControlTogglePending] = useState(false);
  const [projectControlToggleConfirmationTarget, setProjectControlToggleConfirmationTarget] = useState<boolean | null>(null);
  const [projectControlFeedback, setProjectControlFeedback] = useState<string | null>(null);
  const [controlAccess, setControlAccess] = useState<ControlAccessSnapshot | null>(null);
  const [isControlAccessLoading, setIsControlAccessLoading] = useState(true);

  if (typeof window !== "undefined" && initialProjectFromQueryRef.current === null) {
    const params = new URLSearchParams(window.location.search);
    initialProjectFromQueryRef.current = params.get("projectId");
    const viewType = params.get("viewType");
    if (viewType === "logical" || viewType === "physical" || viewType === "geographic") {
      initialViewTypeFromQueryRef.current = viewType;
    }
  }

  const {
    mode,
    viewType,
    gridEnabled,
    search,
    sectorFilters,
    typeFilters,
    statusFilters,
    showHierarchyEdges,
    showTopologyEdges,
    selectedProjectId,
    selectedViewId,
    selectedNodeId,
    selectedEdgeId,
    isDirty,
    isLoading,
    isSavingLayout,
    errorMessage,
    projects,
    sectors,
    assets,
    topologyLinks,
    issues,
    nodes,
    edges,
    setMode,
    setViewType,
    setGridEnabled,
    setSearch,
    setSectorFilters,
    setTypeFilters,
    setStatusFilters,
    setShowHierarchyEdges,
    setShowTopologyEdges,
    setSelectedProjectId,
    setSelectedViewId,
    setSelectedNodeId,
    setSelectedEdgeId,
    setIsDirty,
    setIsLoading,
    setIsSavingLayout,
    setErrorMessage,
    setProjects,
    setSectors,
    setAssets,
    setTopologyLinks,
    setTopologyViews,
    setIssues,
    setGraph
  } = useTopologyStore();

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId) ?? null,
    [projects, selectedProjectId]
  );
  const persistedProjectStyles = useMemo(() => resolveProjectTopologyStyles(selectedProject?.metadata), [selectedProject?.metadata]);
  const hasProjectStyleChanges = useMemo(
    () => JSON.stringify(projectStylesDraft) !== JSON.stringify(persistedProjectStyles),
    [persistedProjectStyles, projectStylesDraft]
  );
  const projectControlUiState = useMemo(
    () => resolveProjectControlUiState({
      projectId: selectedProject?.id ?? null,
      isAccessLoading: isControlAccessLoading,
      hasAccessSnapshot: controlAccess !== null,
      allowedProjectIds: controlAccess?.allowed_projects.map((project) => project.id) ?? [],
      manageableProjectIds: controlAccess?.manageable_parametric_control_project_ids ?? []
    }),
    [controlAccess, isControlAccessLoading, selectedProject?.id]
  );

  const selectedNode = useMemo(() => nodes.find((node) => node.id === selectedNodeId) ?? null, [nodes, selectedNodeId]);
  const selectedEdge = useMemo(() => edges.find((edge) => edge.id === selectedEdgeId) ?? null, [edges, selectedEdgeId]);
  const selectedNodeData = selectedNode?.data as TopologyNodeData | undefined;

  useEffect(() => {
    setProjectStylesDraft(persistedProjectStyles);
  }, [persistedProjectStyles]);

  useEffect(() => {
    let mounted = true;
    void getControlAccess()
      .then((snapshot) => {
        if (mounted) setControlAccess(snapshot);
      })
      .catch(() => {
        if (mounted) setControlAccess(null);
      })
      .finally(() => {
        if (mounted) setIsControlAccessLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const rebuildGraph = useCallback(
    (nodeLayouts: ApiTopologyNodeLayout[], linkLayouts: ApiTopologyLinkLayout[]) => {
      const result = buildGraph({
        sectors,
        assets,
        topologyLinks,
        nodeLayouts,
        linkLayouts,
        mode,
        projectStyles: projectStylesDraft,
        search,
        sectorFilters,
        typeFilters,
        statusFilters,
        showHierarchyEdges,
        showTopologyEdges
      });
      setGraph({
        nodes: result.nodes,
        edges: result.edges
      });
      setIssues(result.issues);
    },
    [
      sectors,
      assets,
      topologyLinks,
      mode,
      projectStylesDraft,
      search,
      sectorFilters,
      typeFilters,
      statusFilters,
      showHierarchyEdges,
      showTopologyEdges,
      setGraph,
      setIssues
    ]
  );

  const loadProjectWorkspace = useCallback(
    async (
      projectId: string,
      desiredViewType: ViewType,
      graphOptions: {
        mode: typeof mode;
        projectStyles: ProjectTopologyStyles;
        search: string;
        sectorFilters: string[];
        typeFilters: ApiAsset["asset_type"][];
        statusFilters: ApiAsset["status"][];
        showHierarchyEdges: boolean;
        showTopologyEdges: boolean;
      }
    ) => {
      const requestId = workspaceLoadSequenceRef.current + 1;
      workspaceLoadSequenceRef.current = requestId;
      setIsLoading(true);
      setErrorMessage(null);
      try {
        const [loadedSectors, loadedAssets, loadedTopologyLinks, loadedViews] = await Promise.all([
          listSectors(projectId),
          listAssets(projectId),
          listTopology(projectId),
          listTopologyViews(projectId, desiredViewType)
        ]);

        let view = loadedViews.find((item) => item.is_default) ?? loadedViews[0] ?? null;
        if (!view) {
          view = await createTopologyView(projectId, {
            name: desiredViewType === "logical" ? "Vista lógica principal" : `Vista ${desiredViewType}`,
            view_type: desiredViewType,
            is_default: true
          });
        }

        if (workspaceLoadSequenceRef.current !== requestId) {
          return;
        }

        setSectors(loadedSectors);
        setAssets(loadedAssets);
        setTopologyLinks(loadedTopologyLinks);
        setTopologyViews(view ? [...loadedViews.filter((item) => item.id !== view?.id), view] : loadedViews);
        setSelectedViewId(view.id);

        const layoutResponse = await getTopologyViewLayout(view.id);
        const nodeLayouts =
          layoutResponse.layout.node_layouts.length > 0
            ? layoutResponse.layout.node_layouts
            : buildDefaultNodeLayouts(loadedSectors, loadedAssets);

        const result = buildGraph({
          sectors: loadedSectors,
          assets: loadedAssets,
          topologyLinks: loadedTopologyLinks,
          nodeLayouts,
          linkLayouts: layoutResponse.layout.link_layouts,
          mode: graphOptions.mode,
          projectStyles: graphOptions.projectStyles,
          search: graphOptions.search,
          sectorFilters: graphOptions.sectorFilters,
          typeFilters: graphOptions.typeFilters,
          statusFilters: graphOptions.statusFilters,
          showHierarchyEdges: graphOptions.showHierarchyEdges,
          showTopologyEdges: graphOptions.showTopologyEdges
        });

        if (workspaceLoadSequenceRef.current !== requestId) {
          return;
        }

        setGraph({
          nodes: result.nodes,
          edges: result.edges
        });
        setIssues(result.issues);
        setIsDirty(false);
        fitCanvasPanorama();
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "No se pudo cargar el workspace");
      } finally {
        if (workspaceLoadSequenceRef.current === requestId) {
          setIsLoading(false);
        }
      }
    },
    [
      setAssets,
      setErrorMessage,
      setGraph,
      setIsDirty,
      setIsLoading,
      setIssues,
      setSectors,
      setSelectedViewId,
      setTopologyLinks,
      setTopologyViews
    ]
  );

  useEffect(() => {
    if (initialViewTypeFromQueryRef.current) {
      setViewType(initialViewTypeFromQueryRef.current);
    }
  }, [setViewType]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      setIsLoading(true);
      try {
        const loadedProjects = await listProjects();
        if (!mounted) return;
        setProjects(loadedProjects);
        if (loadedProjects.length > 0 && !selectedProjectId) {
          const requested = initialProjectFromQueryRef.current;
          const matched = requested
            ? loadedProjects.find((project) => String(project.id) === String(requested))
            : null;
          setSelectedProjectId(matched?.id ?? loadedProjects[0].id);
        }
      } catch (error) {
        if (mounted) {
          setErrorMessage(error instanceof Error ? error.message : "No se pudo cargar proyectos");
        }
      } finally {
        if (mounted) setIsLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [selectedProjectId, setErrorMessage, setIsLoading, setProjects, setSelectedProjectId]);

  useEffect(() => {
    if (!selectedProjectId) return;
    void loadProjectWorkspace(selectedProjectId, viewType, {
      mode,
      projectStyles: projectStylesDraft,
      search,
      sectorFilters,
      typeFilters,
      statusFilters,
      showHierarchyEdges,
      showTopologyEdges
    });
  }, [selectedProjectId, viewType, loadProjectWorkspace]);

  useEffect(() => {
    if (sectors.length === 0 && assets.length === 0) return;
    const currentNodeLayouts = toNodeLayouts(nodes);
    const currentLinkLayouts = toLinkLayouts(edges);
    rebuildGraph(currentNodeLayouts, currentLinkLayouts);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, search, sectorFilters, typeFilters, statusFilters, showHierarchyEdges, showTopologyEdges, projectStylesDraft]);

  async function refreshWorkspace() {
    if (!selectedProjectId) return;
    await loadProjectWorkspace(selectedProjectId, viewType, {
      mode,
      projectStyles: projectStylesDraft,
      search,
      sectorFilters,
      typeFilters,
      statusFilters,
      showHierarchyEdges,
      showTopologyEdges
    });
  }

  async function handleProjectControlToggle(enabled: boolean) {
    if (!selectedProject || !projectControlUiState.canManage || isProjectControlTogglePending) return;
    setProjectControlFeedback(null);
    setProjectControlToggleConfirmationTarget(enabled);
  }

  async function confirmProjectControlToggle() {
    if (
      !selectedProject
      || !projectControlUiState.canManage
      || isProjectControlTogglePending
      || projectControlToggleConfirmationTarget === null
    ) return;
    const enabled = projectControlToggleConfirmationTarget;
    setProjectControlToggleConfirmationTarget(null);
    setIsProjectControlTogglePending(true);
    setErrorMessage(null);
    try {
      const updated = await updateProject(selectedProject.id, {
        parametric_control_enabled: enabled
      });
      const currentProjects = useTopologyStore.getState().projects;
      setProjects(currentProjects.map((project) => (project.id === updated.id ? updated : project)));
      setProjectControlFeedback(`Control paramétrico ${enabled ? "habilitado" : "deshabilitado"} para este proyecto.`);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No se pudo actualizar el feature flag de control");
      setProjectControlFeedback("No se pudo actualizar el control paramétrico. Intentá nuevamente.");
    } finally {
      setIsProjectControlTogglePending(false);
    }
  }

  function getNormalizedNodeLayoutsFromCanvas(sourceNodes: Node[] = flowRef.current?.getNodes() ?? nodes) {
    return normalizeNodeLayouts(sectors, assets, toNodeLayouts(sourceNodes));
  }

  async function saveLayout() {
    if (!selectedViewId || !selectedProject) return;
    setIsSavingLayout(true);
    setErrorMessage(null);
    try {
      const currentNodes = flowRef.current?.getNodes() ?? nodes;
      const normalizedNodeLayouts = getNormalizedNodeLayoutsFromCanvas(currentNodes);
      const currentEdges = flowRef.current?.getEdges() ?? edges;
      const payload = {
        node_layouts: normalizedNodeLayouts,
        link_layouts: toLinkLayouts(currentEdges)
      };
      await saveTopologyViewLayout(selectedViewId, payload);
      await updateProject(selectedProject.id, {
        metadata: {
          ...(selectedProject.metadata ?? {}),
          topology_node_styles: projectStylesDraft
        }
      });
      setProjects(projects.map((project) => (
        project.id === selectedProject.id
          ? {
              ...project,
              metadata: {
                ...(project.metadata ?? {}),
                topology_node_styles: projectStylesDraft
              }
            }
          : project
      )));
      rebuildGraph(normalizedNodeLayouts, payload.link_layouts);
      setIsDirty(false);
      fitCanvasPanorama();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No se pudo guardar el workspace");
    } finally {
      setIsSavingLayout(false);
    }
  }

  function applyAutoLayout() {
    const nodeLayouts = buildDefaultNodeLayouts(sectors, assets);
    rebuildGraph(nodeLayouts, toLinkLayouts(edges));
    setIsDirty(true);
    fitCanvasPanorama();
  }

  function validateGraph() {
    if (issues.length === 0) {
      window.alert("Topología validada: no se detectaron inconsistencias.");
      return;
    }
    const lines = issues.slice(0, 8).map((item) => `• ${item.message}`);
    const suffix = issues.length > 8 ? `\n... y ${issues.length - 8} más` : "";
    window.alert(`Se detectaron ${issues.length} inconsistencias:\n${lines.join("\n")}${suffix}`);
  }

  function centerCanvas() {
    flowRef.current?.fitView({ padding: 0.2, duration: 350 });
  }

  function fitCanvasPanorama() {
    window.requestAnimationFrame(() => {
      flowRef.current?.fitView({
        padding: 0.22,
        duration: 350,
        minZoom: 0.35,
        maxZoom: 1.35
      });
    });
  }

  async function handleCreateSector() {
    if (!selectedProjectId || mode !== "design") return;
    const name = window.prompt("Nombre del sector");
    if (!name || !name.trim()) return;
    try {
      await createSector({
        project_id: selectedProjectId,
        name: name.trim()
      });
      await refreshWorkspace();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No se pudo crear el sector");
    }
  }

  function resolveTargetSectorId(): string | null {
    if (selectedNodeData?.kind === "sector") return selectedNodeData.entityId;
    if (selectedNodeData?.kind === "asset") return selectedNodeData.sectorId ?? null;
    return sectors[0]?.id ?? null;
  }

  async function handleCreateNode() {
    if (!selectedProjectId || mode !== "design") return;
    const sectorId = resolveTargetSectorId();
    if (!sectorId) {
      setErrorMessage("Primero crea un sector para ubicar el nodo");
      return;
    }
    const name = window.prompt("Nombre del nodo programable");
    if (!name || !name.trim()) return;
    try {
      await createAsset({
        project_id: selectedProjectId,
        sector_id: sectorId,
        asset_type: "programmable_node",
        subtype: "esp32",
        name: name.trim()
      });
      await refreshWorkspace();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No se pudo crear el nodo");
    }
  }

  async function handleCreateChildAsset(assetType: "sensor" | "actuator") {
    if (!selectedProjectId || mode !== "design") return;

    const selectedAssetId =
      selectedNodeData?.kind === "asset" && selectedNodeData.assetType === "programmable_node"
        ? selectedNodeData.entityId
        : null;

    if (!selectedAssetId) {
      setErrorMessage("Selecciona un nodo programable para crear un dispositivo hijo");
      return;
    }

    const parentAsset = assets.find((item) => item.id === selectedAssetId);
    if (!parentAsset) {
      setErrorMessage("Nodo padre no encontrado");
      return;
    }

    const name = window.prompt(`Nombre del ${assetType}`);
    if (!name || !name.trim()) return;

    try {
      await createAsset({
        project_id: selectedProjectId,
        sector_id: parentAsset.sector_id,
        parent_asset_id: parentAsset.id,
        asset_type: assetType,
        subtype: assetType === "sensor" ? "generic-sensor" : "generic-actuator",
        name: name.trim()
      });
      await refreshWorkspace();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : `No se pudo crear el ${assetType}`);
    }
  }

  async function handleConnect(connection: Connection) {
    if (!selectedProjectId || mode !== "design") return;
    if (!connection.source || !connection.target) return;

    try {
      const source = parseNodeRef(connection.source);
      const target = parseNodeRef(connection.target);

      const sourceAsset = source.kind === "asset" ? assets.find((item) => item.id === source.id) ?? null : null;
      const targetAsset = target.kind === "asset" ? assets.find((item) => item.id === target.id) ?? null : null;

      const suggestedRelation = inferRelationType(sourceAsset, targetAsset);
      const relation = window.prompt(
        "relation_type (contains, hosts, reads, controls, connects_to, routes_to, depends_on, powered_by, mounted_on)",
        suggestedRelation
      ) as ApiTopologyLink["relation_type"] | null;
      if (!relation) return;

      await createTopologyLink({
        project_id: selectedProjectId,
        source_asset_id: source.kind === "asset" ? source.id : null,
        source_sector_id: source.kind === "sector" ? source.id : null,
        target_asset_id: target.kind === "asset" ? target.id : null,
        target_sector_id: target.kind === "sector" ? target.id : null,
        relation_type: relation
      });
      await refreshWorkspace();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No se pudo crear la conexión");
    }
  }

  async function handleUpdateAsset(id: string, payload: Partial<ApiAsset> & { code?: string | null; description?: string | null }) {
    await updateAsset(id, {
      name: payload.name,
      subtype: payload.subtype,
      status: payload.status,
      code: payload.code ?? null,
      description: payload.description ?? null,
      parent_asset_id: payload.parent_asset_id ?? undefined,
      metadata: payload.metadata
    });
    await refreshWorkspace();
  }

  async function handleUpdateSector(id: string, payload: Partial<ApiSector>) {
    await updateSector(id, {
      name: payload.name,
      code: payload.code ?? null
    });
    await refreshWorkspace();
  }

  async function handleUpdateTopologyLink(id: string, payload: Partial<ApiTopologyLink>) {
    await updateTopologyLink(id, {
      relation_type: payload.relation_type,
      status: payload.status
    });
    await refreshWorkspace();
  }

  async function handleDeleteAsset(id: string) {
    await deleteAsset(id);
    await refreshWorkspace();
  }

  async function handleDeleteSector(id: string) {
    await deleteSector(id);
    await refreshWorkspace();
  }

  async function handleDeleteTopologyLink(id: string) {
    await deleteTopologyLink(id);
    await refreshWorkspace();
  }

  const handleCanvasNodesChange = useCallback(
    (updatedNodes: Node[], changes: NodeChange[]) => {
      const finishedResize = changes.some((change) => change.type === "dimensions" && change.resizing === false);

      if (finishedResize) {
        const currentEdges = flowRef.current?.getEdges() ?? edges;
        const normalizedNodeLayouts = normalizeNodeLayouts(sectors, assets, toNodeLayouts(updatedNodes));
        rebuildGraph(normalizedNodeLayouts, toLinkLayouts(currentEdges));
      } else {
        setGraph({ nodes: updatedNodes, edges });
      }

      setIsDirty(true);
    },
    [assets, edges, rebuildGraph, sectors, setGraph, setIsDirty]
  );

  const handleCanvasEdgesChange = useCallback(
    (updatedEdges: Edge[]) => {
      setGraph({ nodes, edges: updatedEdges });
      setIsDirty(true);
    },
    [nodes, setGraph, setIsDirty]
  );

  const handleCanvasSelectionChange = useCallback(
    ({ nodeId, edgeId }: { nodeId: string | null; edgeId: string | null }) => {
      setSelectedNodeId(nodeId);
      setSelectedEdgeId(edgeId);
    },
    [setSelectedEdgeId, setSelectedNodeId]
  );

  const handleCanvasNodeDragStop = useCallback(() => {
    if (mode !== "design") return;
    const currentNodes = flowRef.current?.getNodes() ?? nodes;
    const currentEdges = flowRef.current?.getEdges() ?? edges;
    const normalizedNodeLayouts = normalizeNodeLayouts(sectors, assets, toNodeLayouts(currentNodes));
    rebuildGraph(normalizedNodeLayouts, toLinkLayouts(currentEdges));
    setIsDirty(true);
  }, [assets, edges, mode, nodes, rebuildGraph, sectors, setIsDirty]);

  const handleCanvasReady = useCallback((instance: ReactFlowInstance) => {
    flowRef.current = instance;
  }, []);

  const handleSidebarNodeSelect = useCallback(
    (nodeId: string) => {
      setSelectedNodeId(nodeId);
      setSelectedEdgeId(null);
      window.requestAnimationFrame(() => {
        const targetNode = flowRef.current?.getNode(nodeId);
        if (!targetNode) {
          return;
        }
        flowRef.current?.fitView({
          nodes: [targetNode],
          padding: 0.45,
          duration: 350,
          minZoom: 0.4,
          maxZoom: 1.25
        });
      });
    },
    [setSelectedEdgeId, setSelectedNodeId]
  );

  return (
    <ReactFlowProvider>
      <div className="topology-workspace">
        <TopologyToolbar
          project={selectedProject}
          mode={mode}
          viewType={viewType}
          issues={issues}
          isDirty={isDirty}
          isSavingLayout={isSavingLayout}
          onModeChange={setMode}
          onViewTypeChange={setViewType}
          onSaveLayout={saveLayout}
          onAutoLayout={applyAutoLayout}
          onValidate={validateGraph}
          onCenter={centerCanvas}
          onRefresh={refreshWorkspace}
        />

        {errorMessage ? <div className="workspace-error">{errorMessage}</div> : null}
        {isLoading ? <div className="workspace-loading">Cargando workspace...</div> : null}

        <div className="workspace-grid">
          <TopologySidebar
            projects={projects}
            project={selectedProject}
            selectedProjectId={selectedProjectId}
            sectors={sectors}
            assets={assets}
            search={search}
            sectorFilters={sectorFilters}
            typeFilters={typeFilters}
            statusFilters={statusFilters}
            showHierarchyEdges={showHierarchyEdges}
            showTopologyEdges={showTopologyEdges}
            selectedNodeId={selectedNodeId}
            issues={issues}
            mode={mode}
            viewType={viewType}
            projectStyles={projectStylesDraft}
            isProjectStylesDirty={hasProjectStyleChanges}
            isProjectControlTogglePending={isProjectControlTogglePending}
            projectControlToggleConfirmationTarget={projectControlToggleConfirmationTarget}
            canManageProjectControl={projectControlUiState.canManage}
            isProjectControlAccessLoading={projectControlUiState.isAccessLoading}
            projectControlAccessMessage={projectControlUiState.message}
            projectControlFeedback={projectControlFeedback}
            onProjectSelect={(projectId) => {
              setSelectedProjectId(projectId);
              setProjectControlToggleConfirmationTarget(null);
              setProjectControlFeedback(null);
            }}
            onProjectControlToggle={(enabled) => void handleProjectControlToggle(enabled)}
            onConfirmProjectControlToggle={() => void confirmProjectControlToggle()}
            onCancelProjectControlToggle={() => setProjectControlToggleConfirmationTarget(null)}
            onSearchChange={setSearch}
            onSectorFiltersChange={setSectorFilters}
            onTypeFiltersChange={setTypeFilters}
            onStatusFiltersChange={setStatusFilters}
            onShowHierarchyEdges={setShowHierarchyEdges}
            onShowTopologyEdges={setShowTopologyEdges}
            onProjectStylesChange={(styles) => {
              setProjectStylesDraft(styles);
              setIsDirty(true);
            }}
            onCreateSector={handleCreateSector}
            onCreateNode={handleCreateNode}
            onCreateSensor={() => void handleCreateChildAsset("sensor")}
            onCreateActuator={() => void handleCreateChildAsset("actuator")}
            onSelectNode={handleSidebarNodeSelect}
          />

          <section className="workspace-canvas">
            <div className="workspace-canvas-head">
              <div>
                <span className="panel-kicker">Canvas</span>
                <h2>{selectedProject ? `${selectedProject.name} topology` : "Project topology"}</h2>
                <p>
                  {mode === "design"
                    ? "Arrastra nodos, conecta relaciones y guarda el layout cuando termines."
                    : "Explora la infraestructura sin modificar la topologia."}
                </p>
              </div>
              <div className="workspace-canvas-meta">
                <span>{viewType}</span>
                <span>{isDirty ? "Cambios sin guardar" : "Layout sincronizado"}</span>
              </div>
            </div>
            <TopologyCanvas
              nodes={nodes}
              edges={edges}
              mode={mode}
              gridEnabled={gridEnabled}
              onNodesChange={handleCanvasNodesChange}
              onEdgesChange={handleCanvasEdgesChange}
              onSelectionChange={handleCanvasSelectionChange}
              onConnect={handleConnect}
              onNodeDragStop={handleCanvasNodeDragStop}
              onReady={handleCanvasReady}
            />
          </section>

          <TopologyInspector
            selectedNode={selectedNode}
            selectedEdge={selectedEdge}
            assets={assets}
            sectors={sectors}
            topologyLinks={topologyLinks}
            mode={mode}
            onUpdateAsset={handleUpdateAsset}
            onUpdateSector={handleUpdateSector}
            onUpdateTopologyLink={handleUpdateTopologyLink}
            onDeleteAsset={handleDeleteAsset}
            onDeleteSector={handleDeleteSector}
            onDeleteTopologyLink={handleDeleteTopologyLink}
          />
        </div>

        <footer className="workspace-footer">
          <label className="check-row">
            <input type="checkbox" checked={gridEnabled} onChange={(event) => setGridEnabled(event.target.checked)} />
            Mostrar grilla
          </label>
          <span>
            Vista activa: <strong>{viewType}</strong> | Modo: <strong>{mode}</strong>
          </span>
        </footer>
      </div>
    </ReactFlowProvider>
  );
}
