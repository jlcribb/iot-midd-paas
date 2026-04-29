export type TopologyRelationType =
  | "contains"
  | "hosts"
  | "reads"
  | "controls"
  | "connects_to"
  | "routes_to"
  | "depends_on"
  | "powered_by"
  | "mounted_on";

export type TopologyLinkStatus = "planned" | "active" | "inactive" | "fault" | "retired";

export interface TopologyLink {
  id: string;
  project_id: string;
  source_asset_id: string | null;
  target_asset_id: string | null;
  source_sector_id: string | null;
  target_sector_id: string | null;
  relation_type: TopologyRelationType;
  connection_medium: string | null;
  protocol: string | null;
  ports: unknown[];
  link_quality: number | null;
  status: TopologyLinkStatus;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
