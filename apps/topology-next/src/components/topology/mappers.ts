import type { CSSProperties } from "react";
import type { Edge, Node } from "@xyflow/react";
import type {
  ApiAsset,
  ApiSector,
  ApiTopologyLink,
  ApiTopologyLinkLayout,
  ApiTopologyNodeLayout,
  GraphIssue,
  ViewMode
} from "@/components/topology/types";
import type { TopologyEdgeData, TopologyNodeData } from "@/components/topology/topology-store";
import type { ProjectTopologyStyles, TopologyNodeVisualStyle } from "@/components/topology/topology-style";

interface BuildGraphArgs {
  sectors: ApiSector[];
  assets: ApiAsset[];
  topologyLinks: ApiTopologyLink[];
  nodeLayouts: ApiTopologyNodeLayout[];
  linkLayouts: ApiTopologyLinkLayout[];
  mode: ViewMode;
  projectStyles: ProjectTopologyStyles;
  search: string;
  sectorFilters: string[];
  typeFilters: ApiAsset["asset_type"][];
  statusFilters: ApiAsset["status"][];
  showHierarchyEdges: boolean;
  showTopologyEdges: boolean;
}

export interface GraphBuildResult {
  nodes: Node[];
  edges: Edge[];
  issues: GraphIssue[];
}

export const DEFAULT_ASSET_NODE_WIDTH = 196;
export const DEFAULT_ASSET_NODE_HEIGHT = 116;
export const DEFAULT_SECTOR_NODE_WIDTH = 520;
export const DEFAULT_SECTOR_NODE_HEIGHT = 440;

const SECTOR_GAP = 80;
const ASSET_GAP_X = 24;
const ASSET_GAP_Y = 28;
const SECTOR_INNER_PADDING_LEFT = 34;
const SECTOR_INNER_PADDING_TOP = 94;
const SECTOR_INNER_PADDING_RIGHT = 34;
const SECTOR_INNER_PADDING_BOTTOM = 36;
const PREFERRED_CHILD_OFFSET_X = 220;
const PREFERRED_CHILD_OFFSET_Y = 146;
const COLLISION_PADDING = 18;

interface Bounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

interface Box {
  x: number;
  y: number;
  width: number;
  height: number;
}

function sectorNodeId(sectorId: string): string {
  return `sector:${sectorId}`;
}

function assetNodeId(assetId: string): string {
  return `asset:${assetId}`;
}

function cloneLayout(layout: ApiTopologyNodeLayout): ApiTopologyNodeLayout {
  return {
    ...layout,
    metadata: { ...(layout.metadata ?? {}) }
  };
}

function createCssVariables(style: TopologyNodeVisualStyle, width: number, height: number): CSSProperties {
  return {
    width,
    height,
    ["--node-fill" as string]: style.fillColor,
    ["--node-stroke" as string]: style.strokeColor,
    ["--node-text" as string]: style.textColor
  };
}

function getAssetSortRank(asset: ApiAsset): number {
  if (!asset.parent_asset_id) return 0;
  if (asset.asset_type === "sensor") return 1;
  if (asset.asset_type === "actuator") return 2;
  return 3;
}

function getBoundsForSector(layout: ApiTopologyNodeLayout): Bounds {
  const sectorWidth = layout.width ?? DEFAULT_SECTOR_NODE_WIDTH;
  const sectorHeight = layout.height ?? DEFAULT_SECTOR_NODE_HEIGHT;
  return {
    minX: SECTOR_INNER_PADDING_LEFT,
    minY: SECTOR_INNER_PADDING_TOP,
    maxX: sectorWidth - SECTOR_INNER_PADDING_RIGHT,
    maxY: sectorHeight - SECTOR_INNER_PADDING_BOTTOM
  };
}

function clampToBounds(x: number, y: number, bounds: Bounds, width: number, height: number) {
  return {
    x: Math.min(Math.max(x, bounds.minX), Math.max(bounds.minX, bounds.maxX - width)),
    y: Math.min(Math.max(y, bounds.minY), Math.max(bounds.minY, bounds.maxY - height))
  };
}

function boxesOverlap(a: Box, b: Box, padding = COLLISION_PADDING): boolean {
  return !(
    a.x + a.width + padding <= b.x ||
    b.x + b.width + padding <= a.x ||
    a.y + a.height + padding <= b.y ||
    b.y + b.height + padding <= a.y
  );
}

function isPositionAvailable(x: number, y: number, width: number, height: number, occupied: Box[]) {
  const candidate = { x, y, width, height };
  return occupied.every((box) => !boxesOverlap(candidate, box));
}

function createAssetBox(layout: ApiTopologyNodeLayout): Box {
  return {
    x: layout.x,
    y: layout.y,
    width: layout.width ?? DEFAULT_ASSET_NODE_WIDTH,
    height: layout.height ?? DEFAULT_ASSET_NODE_HEIGHT
  };
}

function normalizeSectorLayouts(layouts: ApiTopologyNodeLayout[], sectors: ApiSector[]): ApiTopologyNodeLayout[] {
  const layoutBySector = new Map(layouts.filter((item) => item.sector_id).map((item) => [item.sector_id as string, cloneLayout(item)]));
  let cursorX = 0;

  return sectors.map((sector) => {
    const current = layoutBySector.get(sector.id);
    const width = current?.width ?? DEFAULT_SECTOR_NODE_WIDTH;
    const normalized = {
      ...(current ?? {
        asset_id: null,
        sector_id: sector.id,
        x: cursorX,
        y: 0,
        width,
        height: DEFAULT_SECTOR_NODE_HEIGHT,
        collapsed: false,
        hidden: false,
        z_index: 0,
        metadata: {}
      }),
      x: Math.max(current?.x ?? cursorX, cursorX),
      y: current?.y ?? 0,
      width,
      height: current?.height ?? DEFAULT_SECTOR_NODE_HEIGHT
    };
    cursorX = normalized.x + width + SECTOR_GAP;
    return normalized;
  });
}

function buildGridCandidates(bounds: Bounds, width: number, height: number): Array<{ x: number; y: number }> {
  const candidates: Array<{ x: number; y: number }> = [];
  for (let y = bounds.minY; y <= Math.max(bounds.minY, bounds.maxY - height); y += height + ASSET_GAP_Y) {
    for (let x = bounds.minX; x <= Math.max(bounds.minX, bounds.maxX - width); x += width + ASSET_GAP_X) {
      candidates.push({ x, y });
    }
  }
  return candidates;
}

function buildPreferredCandidates(
  parentLayout: ApiTopologyNodeLayout,
  bounds: Bounds,
  width: number,
  height: number
): Array<{ x: number; y: number }> {
  const positions = [
    { x: parentLayout.x + PREFERRED_CHILD_OFFSET_X, y: parentLayout.y },
    { x: parentLayout.x, y: parentLayout.y + PREFERRED_CHILD_OFFSET_Y },
    { x: parentLayout.x + PREFERRED_CHILD_OFFSET_X, y: parentLayout.y + PREFERRED_CHILD_OFFSET_Y },
    { x: parentLayout.x - PREFERRED_CHILD_OFFSET_X, y: parentLayout.y },
    { x: parentLayout.x, y: parentLayout.y - PREFERRED_CHILD_OFFSET_Y }
  ];
  return positions.map((position) => clampToBounds(position.x, position.y, bounds, width, height));
}

function findAvailableAssetPosition(
  occupied: Box[],
  bounds: Bounds,
  width: number,
  height: number,
  preferred: Array<{ x: number; y: number }>
): { x: number; y: number } {
  for (const candidate of preferred) {
    if (isPositionAvailable(candidate.x, candidate.y, width, height, occupied)) {
      return candidate;
    }
  }

  const gridCandidates = buildGridCandidates(bounds, width, height);
  for (const candidate of gridCandidates) {
    if (isPositionAvailable(candidate.x, candidate.y, width, height, occupied)) {
      return candidate;
    }
  }

  const fallbackY = occupied.length * (height + ASSET_GAP_Y);
  return clampToBounds(bounds.minX, bounds.minY + fallbackY, bounds, width, height);
}

function normalizeAssetLayouts(
  sectors: ApiSector[],
  assets: ApiAsset[],
  sectorLayouts: ApiTopologyNodeLayout[],
  inputLayouts: ApiTopologyNodeLayout[]
): ApiTopologyNodeLayout[] {
  const normalizedLayouts: ApiTopologyNodeLayout[] = [];
  const inputByAssetId = new Map(inputLayouts.filter((item) => item.asset_id).map((item) => [item.asset_id as string, cloneLayout(item)]));
  const sectorLayoutById = new Map(sectorLayouts.map((item) => [item.sector_id as string, item]));
  const normalizedByAssetId = new Map<string, ApiTopologyNodeLayout>();

  for (const sector of sectors) {
    const sectorLayout = sectorLayoutById.get(sector.id);
    if (!sectorLayout) continue;

    const bounds = getBoundsForSector(sectorLayout);
    const occupied: Box[] = [];
    const sectorAssets = assets
      .filter((asset) => asset.sector_id === sector.id)
      .sort((left, right) => getAssetSortRank(left) - getAssetSortRank(right) || left.name.localeCompare(right.name));

    for (const asset of sectorAssets) {
      const current = inputByAssetId.get(asset.id);
      const width = current?.width ?? DEFAULT_ASSET_NODE_WIDTH;
      const height = current?.height ?? DEFAULT_ASSET_NODE_HEIGHT;
      const parentLayout = asset.parent_asset_id ? normalizedByAssetId.get(asset.parent_asset_id) ?? null : null;
      const preferredCandidates = parentLayout
        ? buildPreferredCandidates(parentLayout, bounds, width, height)
        : [];

      let position = current
        ? clampToBounds(current.x, current.y, bounds, width, height)
        : findAvailableAssetPosition(occupied, bounds, width, height, preferredCandidates);

      if (!isPositionAvailable(position.x, position.y, width, height, occupied)) {
        position = findAvailableAssetPosition(occupied, bounds, width, height, preferredCandidates);
      }

      const normalizedLayout: ApiTopologyNodeLayout = {
        asset_id: asset.id,
        sector_id: null,
        x: position.x,
        y: position.y,
        width,
        height,
        collapsed: current?.collapsed ?? false,
        hidden: current?.hidden ?? false,
        z_index: current?.z_index ?? 3,
        metadata: { ...(current?.metadata ?? {}) }
      };

      occupied.push(createAssetBox(normalizedLayout));
      normalizedLayouts.push(normalizedLayout);
      normalizedByAssetId.set(asset.id, normalizedLayout);
    }
  }

  return normalizedLayouts;
}

function getLinkLayoutById(layouts: ApiTopologyLinkLayout[]): Map<string, ApiTopologyLinkLayout> {
  return new Map(layouts.map((item) => [item.topology_link_id, item]));
}

function getLayoutByAssetId(layouts: ApiTopologyNodeLayout[]): Map<string, ApiTopologyNodeLayout> {
  return new Map(layouts.filter((item) => item.asset_id).map((item) => [item.asset_id as string, item]));
}

function getLayoutBySectorId(layouts: ApiTopologyNodeLayout[]): Map<string, ApiTopologyNodeLayout> {
  return new Map(layouts.filter((item) => item.sector_id).map((item) => [item.sector_id as string, item]));
}

function resolveAssetNodeHidden(
  asset: ApiAsset,
  search: string,
  sectorFilters: string[],
  typeFilters: ApiAsset["asset_type"][],
  statusFilters: ApiAsset["status"][]
): boolean {
  const searchValue = search.trim().toLowerCase();
  const matchesSearch =
    searchValue.length === 0 ||
    asset.name.toLowerCase().includes(searchValue) ||
    asset.subtype.toLowerCase().includes(searchValue);

  const sectorAllowed = sectorFilters.length === 0 || sectorFilters.includes(asset.sector_id);
  const typeAllowed = typeFilters.length === 0 || typeFilters.includes(asset.asset_type);
  const statusAllowed = statusFilters.length === 0 || statusFilters.includes(asset.status);

  return !(matchesSearch && sectorAllowed && typeAllowed && statusAllowed);
}

function evaluateIssues(sectors: ApiSector[], assets: ApiAsset[], topologyLinks: ApiTopologyLink[]): GraphIssue[] {
  const issues: GraphIssue[] = [];
  const assetById = new Map(assets.map((asset) => [asset.id, asset]));
  const sectorById = new Map(sectors.map((sector) => [sector.id, sector]));

  for (const sector of sectors) {
    const hasAssets = assets.some((asset) => asset.sector_id === sector.id);
    if (!hasAssets) {
      issues.push({
        id: sector.id,
        kind: "sector",
        severity: "warning",
        message: "Sector vacío: no tiene activos asociados"
      });
    }
  }

  for (const asset of assets) {
    if (!sectorById.has(asset.sector_id)) {
      issues.push({
        id: asset.id,
        kind: "asset",
        severity: "error",
        message: "Asset con sector inconsistente"
      });
    }

    if ((asset.asset_type === "sensor" || asset.asset_type === "actuator") && !asset.parent_asset_id) {
      issues.push({
        id: asset.id,
        kind: "asset",
        severity: "warning",
        message: `${asset.asset_type} sin parent_asset_id`
      });
    }

    if (asset.asset_type === "programmable_node") {
      const hasDevices = assets.some((item) => item.parent_asset_id === asset.id);
      if (!hasDevices) {
        issues.push({
          id: asset.id,
          kind: "asset",
          severity: "warning",
          message: "Nodo programable sin dispositivos hijos"
        });
      }
    }

    if (asset.status === "offline" || asset.status === "fault" || asset.status === "maintenance") {
      issues.push({
        id: asset.id,
        kind: "asset",
        severity: "warning",
        message: `Estado operativo: ${asset.status}`
      });
    }
  }

  for (const link of topologyLinks) {
    const sourceAssetExists = !link.source_asset_id || assetById.has(link.source_asset_id);
    const targetAssetExists = !link.target_asset_id || assetById.has(link.target_asset_id);
    const sourceSectorExists = !link.source_sector_id || sectorById.has(link.source_sector_id);
    const targetSectorExists = !link.target_sector_id || sectorById.has(link.target_sector_id);

    if (!sourceAssetExists || !targetAssetExists || !sourceSectorExists || !targetSectorExists) {
      issues.push({
        id: link.id,
        kind: "link",
        severity: "error",
        message: "Link topológico con referencia inválida o huérfana"
      });
    }
  }

  return issues;
}

function buildIssueMap(issues: GraphIssue[]): Map<string, GraphIssue[]> {
  const issueByEntity = new Map<string, GraphIssue[]>();
  for (const issue of issues) {
    const list = issueByEntity.get(issue.id) ?? [];
    list.push(issue);
    issueByEntity.set(issue.id, list);
  }
  return issueByEntity;
}

export function parseNodeRef(nodeId: string): { kind: "sector" | "asset"; id: string } {
  const [kind, id] = nodeId.split(":");
  if ((kind !== "sector" && kind !== "asset") || !id) {
    throw new Error(`Invalid node reference ${nodeId}`);
  }

  return {
    kind,
    id
  };
}

export function normalizeNodeLayouts(
  sectors: ApiSector[],
  assets: ApiAsset[],
  nodeLayouts: ApiTopologyNodeLayout[]
): ApiTopologyNodeLayout[] {
  const sectorLayouts = normalizeSectorLayouts(nodeLayouts, sectors);
  const assetLayouts = normalizeAssetLayouts(sectors, assets, sectorLayouts, nodeLayouts);
  return [...sectorLayouts, ...assetLayouts];
}

export function buildDefaultNodeLayouts(sectors: ApiSector[], assets: ApiAsset[]): ApiTopologyNodeLayout[] {
  return normalizeNodeLayouts(sectors, assets, []);
}

export function buildGraph(args: BuildGraphArgs): GraphBuildResult {
  const issues = evaluateIssues(args.sectors, args.assets, args.topologyLinks);
  const issueByEntity = buildIssueMap(issues);
  const resolvedNodeLayouts = normalizeNodeLayouts(args.sectors, args.assets, args.nodeLayouts);
  const layoutByAsset = getLayoutByAssetId(resolvedNodeLayouts);
  const layoutBySector = getLayoutBySectorId(resolvedNodeLayouts);
  const linkLayoutByLinkId = getLinkLayoutById(args.linkLayouts);
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  const assetHiddenById = new Map<string, boolean>();
  const visibleAssetCountBySector = new Map<string, number>();
  const hasAssetVisibilityFilters =
    args.search.trim().length > 0 || args.typeFilters.length > 0 || args.statusFilters.length > 0;

  for (const asset of args.assets) {
    const layout = layoutByAsset.get(asset.id);
    const hiddenByFilters = resolveAssetNodeHidden(
      asset,
      args.search,
      args.sectorFilters,
      args.typeFilters,
      args.statusFilters
    );
    const hidden = (layout?.hidden ?? false) || hiddenByFilters;
    assetHiddenById.set(asset.id, hidden);

    if (!hidden) {
      visibleAssetCountBySector.set(asset.sector_id, (visibleAssetCountBySector.get(asset.sector_id) ?? 0) + 1);
    }
  }

  const sectorHiddenById = new Map<string, boolean>();

  for (const sector of args.sectors) {
    const layout = layoutBySector.get(sector.id);
    const hiddenBySectorFilter = args.sectorFilters.length > 0 && !args.sectorFilters.includes(sector.id);
    const hiddenByEmptyResult = !hiddenBySectorFilter && hasAssetVisibilityFilters && !visibleAssetCountBySector.has(sector.id);
    sectorHiddenById.set(sector.id, (layout?.hidden ?? false) || hiddenBySectorFilter || hiddenByEmptyResult);
  }

  for (const sector of args.sectors) {
    const layout = layoutBySector.get(sector.id);
    const sectorStyle = args.projectStyles.sector;
    const sectorWidth = layout?.width ?? DEFAULT_SECTOR_NODE_WIDTH;
    const sectorHeight = layout?.height ?? DEFAULT_SECTOR_NODE_HEIGHT;
    const sectorIssues = issueByEntity.get(sector.id) ?? [];

    nodes.push({
      id: sectorNodeId(sector.id),
      type: "sectorGroup",
      position: {
        x: layout?.x ?? 0,
        y: layout?.y ?? 0
      },
      data: {
        kind: "sector",
        mode: args.mode,
        entityId: sector.id,
        label: sector.name,
        subtitle: sector.code ?? "sector",
        status: "active",
        shape: sectorStyle.shape,
        fillColor: sectorStyle.fillColor,
        strokeColor: sectorStyle.strokeColor,
        textColor: sectorStyle.textColor,
        issueCount: sectorIssues.length,
        issues: sectorIssues
      } satisfies TopologyNodeData,
      draggable: true,
      selected: false,
      zIndex: layout?.z_index ?? 0,
      width: sectorWidth,
      height: sectorHeight,
      style: createCssVariables(sectorStyle, sectorWidth, sectorHeight),
      hidden: sectorHiddenById.get(sector.id) ?? false
    });
  }

  for (const asset of args.assets) {
    const layout = layoutByAsset.get(asset.id);
    const assetStyle = args.projectStyles.assetTypes[asset.asset_type];
    const width = layout?.width ?? DEFAULT_ASSET_NODE_WIDTH;
    const height = layout?.height ?? DEFAULT_ASSET_NODE_HEIGHT;
    const assetIssues = issueByEntity.get(asset.id) ?? [];
    const assetHidden = assetHiddenById.get(asset.id) ?? false;
    const parentSectorNodeId = sectorNodeId(asset.sector_id);
    const hasVisibleParentSector = !(sectorHiddenById.get(asset.sector_id) ?? true);

    nodes.push({
      id: assetNodeId(asset.id),
      type: "topologyAsset",
      parentId: hasVisibleParentSector ? parentSectorNodeId : undefined,
      extent: hasVisibleParentSector ? "parent" : undefined,
      position: {
        x: layout?.x ?? SECTOR_INNER_PADDING_LEFT,
        y: layout?.y ?? SECTOR_INNER_PADDING_TOP
      },
      data: {
        kind: "asset",
        mode: args.mode,
        entityId: asset.id,
        label: asset.name,
        subtitle: `${asset.asset_type} / ${asset.subtype}`,
        status: asset.status,
        assetType: asset.asset_type,
        sectorId: asset.sector_id,
        shape: assetStyle.shape,
        fillColor: assetStyle.fillColor,
        strokeColor: assetStyle.strokeColor,
        textColor: assetStyle.textColor,
        issueCount: assetIssues.length,
        issues: assetIssues
      } satisfies TopologyNodeData,
      zIndex: layout?.z_index ?? 2,
      width,
      height,
      style: createCssVariables(assetStyle, width, height),
      hidden: assetHidden || !hasVisibleParentSector
    });
  }

  if (args.showHierarchyEdges) {
    for (const asset of args.assets) {
      if (!asset.parent_asset_id) continue;
      const hidden = (assetHiddenById.get(asset.id) ?? true) || (assetHiddenById.get(asset.parent_asset_id) ?? true);
      edges.push({
        id: `hierarchy:${asset.id}`,
        source: assetNodeId(asset.parent_asset_id),
        target: assetNodeId(asset.id),
        type: "smoothstep",
        animated: false,
        selectable: true,
        hidden,
        style: {
          stroke: "#9ca3af",
          strokeDasharray: "5 4"
        },
        label: "parent",
        data: {
          kind: "hierarchy",
          entityId: asset.id,
          issues: []
        } satisfies TopologyEdgeData
      });
    }
  }

  if (args.showTopologyEdges) {
    for (const link of args.topologyLinks) {
      const source = link.source_asset_id
        ? assetNodeId(link.source_asset_id)
        : link.source_sector_id
          ? sectorNodeId(link.source_sector_id)
          : null;
      const target = link.target_asset_id
        ? assetNodeId(link.target_asset_id)
        : link.target_sector_id
          ? sectorNodeId(link.target_sector_id)
          : null;

      if (!source || !target) continue;
      const sourceHidden = link.source_asset_id
        ? (assetHiddenById.get(link.source_asset_id) ?? true)
        : link.source_sector_id
          ? (sectorHiddenById.get(link.source_sector_id) ?? true)
          : true;
      const targetHidden = link.target_asset_id
        ? (assetHiddenById.get(link.target_asset_id) ?? true)
        : link.target_sector_id
          ? (sectorHiddenById.get(link.target_sector_id) ?? true)
          : true;

      const issueList = issueByEntity.get(link.id) ?? [];
      const layout = linkLayoutByLinkId.get(link.id);
      edges.push({
        id: `topology:${link.id}`,
        source,
        target,
        type: "topologyEdge",
        label: link.relation_type,
        animated: link.status === "active",
        hidden: (layout?.hidden ?? false) || sourceHidden || targetHidden,
        data: {
          kind: "topology",
          entityId: link.id,
          relationType: link.relation_type,
          status: link.status,
          issues: issueList
        } satisfies TopologyEdgeData
      });
    }
  }

  return {
    nodes,
    edges,
    issues
  };
}
