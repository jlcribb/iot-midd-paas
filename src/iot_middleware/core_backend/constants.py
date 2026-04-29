"""Constants derived from public core schema enums."""

PROJECT_STATUSES = {"draft", "active", "inactive", "archived"}
ASSET_TYPES = {
    "programmable_node",
    "sensor",
    "actuator",
    "gateway",
    "relay_module",
    "camera",
    "power_unit",
}
ASSET_STATUSES = {
    "provisioning",
    "online",
    "offline",
    "active",
    "inactive",
    "fault",
    "maintenance",
    "retired",
}
TOPOLOGY_RELATIONS = {
    "contains",
    "hosts",
    "reads",
    "controls",
    "connects_to",
    "routes_to",
    "depends_on",
    "powered_by",
    "mounted_on",
}
LINK_STATUSES = {"planned", "active", "inactive", "fault", "retired"}

PARENT_ALLOWED_TYPES = {"programmable_node", "gateway", "relay_module", "power_unit"}
CHILD_FORBIDDEN_WITH_PARENT = {"programmable_node", "gateway", "power_unit"}
