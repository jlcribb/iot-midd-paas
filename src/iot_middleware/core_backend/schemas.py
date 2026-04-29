"""Input schemas for core backend endpoints."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


ProjectStatus = Literal["draft", "active", "inactive", "archived"]
AssetType = Literal[
    "programmable_node",
    "sensor",
    "actuator",
    "gateway",
    "relay_module",
    "camera",
    "power_unit",
]
AssetStatus = Literal[
    "provisioning",
    "online",
    "offline",
    "active",
    "inactive",
    "fault",
    "maintenance",
    "retired",
]
TopologyRelation = Literal[
    "contains",
    "hosts",
    "reads",
    "controls",
    "connects_to",
    "routes_to",
    "depends_on",
    "powered_by",
    "mounted_on",
]
LinkStatus = Literal["planned", "active", "inactive", "fault", "retired"]


class _BasePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateProjectPayload(_BasePayload):
    name: str = Field(min_length=1)
    description: Optional[str] = None
    status: ProjectStatus = "draft"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpdateProjectPayload(_BasePayload):
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class CreateSectorPayload(_BasePayload):
    project_id: str
    location_id: Optional[str] = None
    name: str = Field(min_length=1)
    code: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpdateSectorPayload(_BasePayload):
    location_id: Optional[str] = None
    name: Optional[str] = Field(default=None, min_length=1)
    code: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class CreateLocationPayload(_BasePayload):
    name: str = Field(min_length=1)
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    accuracy_meters: Optional[float] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address_text: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    zone: Optional[str] = None
    rack: Optional[str] = None
    position: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("longitude")
    @classmethod
    def _validate_lat_lon_pair(cls, longitude: Optional[float], info):
        latitude = info.data.get("latitude")
        if (latitude is None) != (longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return longitude


class UpdateLocationPayload(_BasePayload):
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    accuracy_meters: Optional[float] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address_text: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    zone: Optional[str] = None
    rack: Optional[str] = None
    position: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CreateAssetPayload(_BasePayload):
    project_id: str
    sector_id: str
    location_id: Optional[str] = None
    parent_asset_id: Optional[str] = None
    asset_type: AssetType
    subtype: str = Field(min_length=1)
    name: str = Field(min_length=1)
    code: Optional[str] = None
    description: Optional[str] = None
    status: AssetStatus = "inactive"
    role: Optional[str] = None
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    last_seen_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpdateAssetPayload(_BasePayload):
    sector_id: Optional[str] = None
    location_id: Optional[str] = None
    parent_asset_id: Optional[str] = None
    asset_type: Optional[AssetType] = None
    subtype: Optional[str] = Field(default=None, min_length=1)
    name: Optional[str] = Field(default=None, min_length=1)
    code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AssetStatus] = None
    role: Optional[str] = None
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    last_seen_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CreateTopologyLinkPayload(_BasePayload):
    project_id: str
    source_asset_id: Optional[str] = None
    target_asset_id: Optional[str] = None
    source_sector_id: Optional[str] = None
    target_sector_id: Optional[str] = None
    relation_type: TopologyRelation
    connection_medium: Optional[str] = None
    protocol: Optional[str] = None
    ports: List[Any] = Field(default_factory=list)
    link_quality: Optional[float] = None
    status: LinkStatus = "active"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpdateTopologyLinkPayload(_BasePayload):
    source_asset_id: Optional[str] = None
    target_asset_id: Optional[str] = None
    source_sector_id: Optional[str] = None
    target_sector_id: Optional[str] = None
    relation_type: Optional[TopologyRelation] = None
    connection_medium: Optional[str] = None
    protocol: Optional[str] = None
    ports: Optional[List[Any]] = None
    link_quality: Optional[float] = None
    status: Optional[LinkStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class NodeSpecPayload(_BasePayload):
    subtype: str = Field(min_length=1)
    name: str = Field(min_length=1)
    code: Optional[str] = None
    description: Optional[str] = None
    status: AssetStatus = "active"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChildDeviceSpecPayload(_BasePayload):
    asset_type: Literal["sensor", "actuator"]
    subtype: str = Field(min_length=1)
    name: str = Field(min_length=1)
    code: Optional[str] = None
    description: Optional[str] = None
    status: AssetStatus = "active"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProvisionNodeBundlePayload(_BasePayload):
    sector_id: str
    node: NodeSpecPayload
    children: List[ChildDeviceSpecPayload] = Field(default_factory=list)
    create_topology_links: bool = True
