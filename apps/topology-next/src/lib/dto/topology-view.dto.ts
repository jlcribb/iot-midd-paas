export type TopologyViewType = "logical" | "physical" | "geographic";

export interface TopologyView {
  id: string;
  project_id: string;
  name: string;
  view_type: TopologyViewType;
  is_default: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface TopologyNodeLayout {
  id: string;
  topology_view_id: string;
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
  created_at: string;
  updated_at: string;
}

export interface TopologyLinkLayout {
  id: string;
  topology_view_id: string;
  topology_link_id: string;
  hidden: boolean;
  label_offset_x: number;
  label_offset_y: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface TopologyViewLayout {
  node_layouts: TopologyNodeLayout[];
  link_layouts: TopologyLinkLayout[];
}
