export type ViewMode = "design" | "operation";
export type ViewType = "logical" | "physical" | "geographic";

export interface ApiProject {
  id: string;
  name: string;
  status: "draft" | "active" | "inactive" | "archived";
  description: string | null;
  metadata: Record<string, unknown>;
}

export interface ApiSector {
  id: string;
  project_id: string;
  location_id: string | null;
  name: string;
  code: string | null;
  description: string | null;
  metadata: Record<string, unknown>;
}

export interface ApiAsset {
  id: string;
  project_id: string;
  sector_id: string;
  parent_asset_id: string | null;
  asset_type:
    | "programmable_node"
    | "sensor"
    | "actuator"
    | "gateway"
    | "relay_module"
    | "camera"
    | "power_unit";
  subtype: string;
  name: string;
  code?: string | null;
  description?: string | null;
  status: "provisioning" | "online" | "offline" | "active" | "inactive" | "fault" | "maintenance" | "retired";
  metadata: Record<string, unknown>;
}

export interface ApiTopologyLink {
  id: string;
  project_id: string;
  source_asset_id: string | null;
  source_sector_id: string | null;
  target_asset_id: string | null;
  target_sector_id: string | null;
  relation_type:
    | "contains"
    | "hosts"
    | "reads"
    | "controls"
    | "connects_to"
    | "routes_to"
    | "depends_on"
    | "powered_by"
    | "mounted_on";
  status: "planned" | "active" | "inactive" | "fault" | "retired";
  metadata: Record<string, unknown>;
}

export interface ApiTopologyView {
  id: string;
  project_id: string;
  name: string;
  view_type: ViewType;
  is_default: boolean;
  metadata: Record<string, unknown>;
}

export interface ApiTopologyNodeLayout {
  asset_id: string | null;
  sector_id: string | null;
  x: number;
  y: number;
  width: number | null;
  height: number | null;
  collapsed: boolean;
  hidden: boolean;
  z_index: number;
  metadata: Record<string, unknown>;
}

export interface ApiTopologyLinkLayout {
  topology_link_id: string;
  hidden: boolean;
  label_offset_x: number;
  label_offset_y: number;
  metadata: Record<string, unknown>;
}

export interface ApiTopologyViewLayoutPayload {
  node_layouts: ApiTopologyNodeLayout[];
  link_layouts: ApiTopologyLinkLayout[];
}

export interface GraphIssue {
  id: string;
  kind: "asset" | "sector" | "link";
  severity: "warning" | "error";
  message: string;
}
