export type AssetType =
  | "programmable_node"
  | "sensor"
  | "actuator"
  | "gateway"
  | "relay_module"
  | "camera"
  | "power_unit";

export type AssetStatus =
  | "provisioning"
  | "online"
  | "offline"
  | "active"
  | "inactive"
  | "fault"
  | "maintenance"
  | "retired";

export interface Asset {
  id: string;
  project_id: string;
  sector_id: string;
  location_id: string | null;
  parent_asset_id: string | null;
  asset_type: AssetType;
  subtype: string;
  name: string;
  code: string | null;
  description: string | null;
  status: AssetStatus;
  role: string | null;
  serial_number: string | null;
  manufacturer: string | null;
  model: string | null;
  firmware_version: string | null;
  hardware_version: string | null;
  mac_address: string | null;
  ip_address: string | null;
  last_seen_at: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AssetTreeNode extends Asset {
  depth: number;
}
