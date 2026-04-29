"""Business services for core backend."""

from __future__ import annotations

import copy
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional

from .constants import (
    CHILD_FORBIDDEN_WITH_PARENT,
    PARENT_ALLOWED_TYPES,
)
from .errors import ConflictError, NotFoundError, ValidationDomainError
from .repositories import (
    AssetRepository,
    LocationRepository,
    ProjectRepository,
    SectorRepository,
    TopologyLinkRepository,
)


def _ensure_metadata_object(payload: Dict[str, Any], key: str = "metadata") -> None:
    if key not in payload or payload[key] is None:
        return
    if not isinstance(payload[key], dict):
        raise ValidationDomainError(f"{key} must be a JSON object")


def _normalize_mac(mac: Optional[str]) -> Optional[str]:
    if mac is None:
        return None
    normalized = str(mac).strip().lower()
    return normalized or None


@contextmanager
def _session_scope(db_handler):
    with db_handler.get_session() as session:
        yield session


class ProjectService:
    def __init__(self, db_handler, project_repo: Optional[ProjectRepository] = None):
        self.db_handler = db_handler
        self.project_repo = project_repo or ProjectRepository()

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not str(payload.get("name", "")).strip():
            raise ValidationDomainError("project name is required")
        _ensure_metadata_object(payload)
        with _session_scope(self.db_handler) as session:
            return self.project_repo.create(session, payload)

    def get_by_id(self, project_id: str) -> Dict[str, Any]:
        with _session_scope(self.db_handler) as session:
            project = self.project_repo.get_by_id(session, project_id)
            if not project:
                raise NotFoundError("project not found")
            return project

    def list(self, status: Optional[str] = None, include_archived: bool = True) -> List[Dict[str, Any]]:
        with _session_scope(self.db_handler) as session:
            return self.project_repo.list(session, status=status, include_archived=include_archived)

    def update(self, project_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if "name" in payload and not str(payload.get("name") or "").strip():
            raise ValidationDomainError("project name cannot be blank")
        _ensure_metadata_object(payload)
        with _session_scope(self.db_handler) as session:
            current = self.project_repo.get_by_id(session, project_id)
            if not current:
                raise NotFoundError("project not found")
            updated = self.project_repo.update(session, project_id, payload)
            if not updated:
                raise NotFoundError("project not found")
            if payload.get("status") == "archived":
                sector_repo = SectorRepository()
                asset_repo = AssetRepository()
                topology_repo = TopologyLinkRepository()
                sectors = sector_repo.list_by_project(session, project_id, active_only=False)
                for sector in sectors:
                    sector_repo.set_active(session, str(sector["id"]), False)
                assets = asset_repo.list_by_project(session, project_id, active_only=False)
                for asset in assets:
                    asset_repo.set_status(
                        session,
                        str(asset["id"]),
                        "inactive",
                        patch_metadata={"is_active": False},
                    )
                links = topology_repo.list_by_project(session, project_id)
                for link in links:
                    topology_repo.update(session, str(link["id"]), {"status": "inactive"})
            return updated

    def archive(self, project_id: str) -> Dict[str, Any]:
        with _session_scope(self.db_handler) as session:
            current = self.project_repo.get_by_id(session, project_id)
            if not current:
                raise NotFoundError("project not found")
            archived = self.project_repo.archive(session, project_id)
            return archived


class LocationService:
    def __init__(self, db_handler, location_repo: Optional[LocationRepository] = None):
        self.db_handler = db_handler
        self.location_repo = location_repo or LocationRepository()

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not str(payload.get("name", "")).strip():
            raise ValidationDomainError("location name is required")
        _ensure_metadata_object(payload)
        with _session_scope(self.db_handler) as session:
            return self.location_repo.create(session, payload)

    def get_by_id(self, location_id: str) -> Dict[str, Any]:
        with _session_scope(self.db_handler) as session:
            location = self.location_repo.get_by_id(session, location_id)
            if not location:
                raise NotFoundError("location not found")
            return location

    def update(self, location_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        _ensure_metadata_object(payload)
        with _session_scope(self.db_handler) as session:
            current = self.location_repo.get_by_id(session, location_id)
            if not current:
                raise NotFoundError("location not found")
            updated = self.location_repo.update(session, location_id, payload)
            if not updated:
                raise NotFoundError("location not found")
            return updated

    def list(self, query: Optional[str] = None, city: Optional[str] = None) -> List[Dict[str, Any]]:
        with _session_scope(self.db_handler) as session:
            return self.location_repo.list(session, query=query, city=city)


class SectorService:
    def __init__(
        self,
        db_handler,
        project_repo: Optional[ProjectRepository] = None,
        location_repo: Optional[LocationRepository] = None,
        sector_repo: Optional[SectorRepository] = None,
        asset_repo: Optional[AssetRepository] = None,
        topology_repo: Optional[TopologyLinkRepository] = None,
    ):
        self.db_handler = db_handler
        self.project_repo = project_repo or ProjectRepository()
        self.location_repo = location_repo or LocationRepository()
        self.sector_repo = sector_repo or SectorRepository()
        self.asset_repo = asset_repo or AssetRepository()
        self.topology_repo = topology_repo or TopologyLinkRepository()

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not str(payload.get("name", "")).strip():
            raise ValidationDomainError("sector name is required")
        _ensure_metadata_object(payload)
        with _session_scope(self.db_handler) as session:
            project = self.project_repo.get_by_id(session, payload.get("project_id"))
            if not project:
                raise NotFoundError("project not found")
            location_id = payload.get("location_id")
            if location_id:
                location = self.location_repo.get_by_id(session, location_id)
                if not location:
                    raise NotFoundError("location not found")
            if self.sector_repo.exists_name(session, payload["project_id"], payload["name"]):
                raise ConflictError("sector name already exists in project")
            if payload.get("code") and self.sector_repo.exists_code(session, payload["project_id"], payload["code"]):
                raise ConflictError("sector code already exists in project")
            return self.sector_repo.create(session, payload)

    def get_by_id(self, sector_id: str) -> Dict[str, Any]:
        with _session_scope(self.db_handler) as session:
            sector = self.sector_repo.get_by_id(session, sector_id)
            if not sector:
                raise NotFoundError("sector not found")
            return sector

    def list_by_project(self, project_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        with _session_scope(self.db_handler) as session:
            project = self.project_repo.get_by_id(session, project_id)
            if not project:
                raise NotFoundError("project not found")
            return self.sector_repo.list_by_project(session, project_id, active_only=active_only)

    def update(self, sector_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        _ensure_metadata_object(payload)
        with _session_scope(self.db_handler) as session:
            current = self.sector_repo.get_by_id(session, sector_id)
            if not current:
                raise NotFoundError("sector not found")
            project_id = str(current["project_id"])
            if payload.get("location_id"):
                location = self.location_repo.get_by_id(session, payload["location_id"])
                if not location:
                    raise NotFoundError("location not found")
            if payload.get("name") and self.sector_repo.exists_name(
                session,
                project_id,
                payload["name"],
                exclude_id=sector_id,
            ):
                raise ConflictError("sector name already exists in project")
            if payload.get("code") and self.sector_repo.exists_code(
                session,
                project_id,
                payload["code"],
                exclude_id=sector_id,
            ):
                raise ConflictError("sector code already exists in project")
            metadata_patch = payload.pop("is_active", None)
            base_payload = copy.deepcopy(payload)
            updated = self.sector_repo.update(session, sector_id, base_payload)
            if not updated:
                raise NotFoundError("sector not found")
            if metadata_patch is not None:
                updated = self.sector_repo.set_active(session, sector_id, bool(metadata_patch))
            return updated

    def soft_delete(self, sector_id: str) -> Dict[str, Any]:
        with _session_scope(self.db_handler) as session:
            sector = self.sector_repo.get_by_id(session, sector_id)
            if not sector:
                raise NotFoundError("sector not found")
            self.sector_repo.set_active(session, sector_id, False)
            assets = self.asset_repo.list_by_sector(session, sector_id, active_only=False)
            sector_asset_ids = {str(asset["id"]) for asset in assets}
            for asset in assets:
                self.asset_repo.set_status(
                    session,
                    str(asset["id"]),
                    "inactive",
                    patch_metadata={"is_active": False},
                )
            links = self.topology_repo.list_by_project(session, str(sector["project_id"]))
            for link in links:
                source_sector_id = str(link.get("source_sector_id") or "")
                target_sector_id = str(link.get("target_sector_id") or "")
                source_asset_id = str(link.get("source_asset_id") or "")
                target_asset_id = str(link.get("target_asset_id") or "")
                if (
                    source_sector_id == sector_id
                    or target_sector_id == sector_id
                    or source_asset_id in sector_asset_ids
                    or target_asset_id in sector_asset_ids
                ):
                    self.topology_repo.update(session, str(link["id"]), {"status": "inactive"})
            refreshed = self.sector_repo.get_by_id(session, sector_id)
            return refreshed


class AssetService:
    def __init__(
        self,
        db_handler,
        project_repo: Optional[ProjectRepository] = None,
        sector_repo: Optional[SectorRepository] = None,
        location_repo: Optional[LocationRepository] = None,
        asset_repo: Optional[AssetRepository] = None,
        topology_repo: Optional[TopologyLinkRepository] = None,
    ):
        self.db_handler = db_handler
        self.project_repo = project_repo or ProjectRepository()
        self.sector_repo = sector_repo or SectorRepository()
        self.location_repo = location_repo or LocationRepository()
        self.asset_repo = asset_repo or AssetRepository()
        self.topology_repo = topology_repo or TopologyLinkRepository()

    def _validate_project_sector(self, session, project_id: str, sector_id: str) -> None:
        project = self.project_repo.get_by_id(session, project_id)
        if not project:
            raise NotFoundError("project not found")
        sector = self.sector_repo.get_by_id(session, sector_id)
        if not sector:
            raise NotFoundError("sector not found")
        if str(sector["project_id"]) != str(project_id):
            raise ConflictError("sector does not belong to project")

    def _validate_parent(
        self,
        session,
        payload: Dict[str, Any],
        current_asset_id: Optional[str] = None,
    ) -> None:
        parent_id = payload.get("parent_asset_id")
        if not parent_id:
            return
        if current_asset_id and str(current_asset_id) == str(parent_id):
            raise ConflictError("asset cannot reference itself as parent")
        parent = self.asset_repo.get_by_id(session, parent_id)
        if not parent:
            raise NotFoundError("parent asset not found")
        if str(parent["project_id"]) != str(payload["project_id"]):
            raise ConflictError("parent asset belongs to a different project")
        if str(parent["sector_id"]) != str(payload["sector_id"]):
            raise ConflictError("parent asset belongs to a different sector")
        parent_type = str(parent["asset_type"])
        child_type = str(payload["asset_type"])
        if parent_type not in PARENT_ALLOWED_TYPES:
            raise ConflictError(f"parent asset type {parent_type} cannot have children")
        if child_type in CHILD_FORBIDDEN_WITH_PARENT:
            raise ConflictError(f"asset type {child_type} cannot be child via parent_asset_id")

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        _ensure_metadata_object(payload)
        if not str(payload.get("name", "")).strip():
            raise ValidationDomainError("asset name is required")
        if not str(payload.get("subtype", "")).strip():
            raise ValidationDomainError("asset subtype is required")
        with _session_scope(self.db_handler) as session:
            self._validate_project_sector(session, payload["project_id"], payload["sector_id"])
            if payload.get("location_id"):
                location = self.location_repo.get_by_id(session, payload["location_id"])
                if not location:
                    raise NotFoundError("location not found")
            payload["mac_address"] = _normalize_mac(payload.get("mac_address"))
            self._validate_parent(session, payload)
            return self.asset_repo.create(session, payload)

    def get_by_id(self, asset_id: str) -> Dict[str, Any]:
        with _session_scope(self.db_handler) as session:
            asset = self.asset_repo.get_by_id(session, asset_id)
            if not asset:
                raise NotFoundError("asset not found")
            return asset

    def list_by_project(self, project_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        with _session_scope(self.db_handler) as session:
            project = self.project_repo.get_by_id(session, project_id)
            if not project:
                raise NotFoundError("project not found")
            return self.asset_repo.list_by_project(session, project_id, active_only=active_only)

    def list_by_sector(self, sector_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        with _session_scope(self.db_handler) as session:
            sector = self.sector_repo.get_by_id(session, sector_id)
            if not sector:
                raise NotFoundError("sector not found")
            return self.asset_repo.list_by_sector(session, sector_id, active_only=active_only)

    def list_children(self, asset_id: str) -> List[Dict[str, Any]]:
        with _session_scope(self.db_handler) as session:
            parent = self.asset_repo.get_by_id(session, asset_id)
            if not parent:
                raise NotFoundError("asset not found")
            return self.asset_repo.list_children(session, asset_id)

    def get_node_devices(self, node_id: str) -> List[Dict[str, Any]]:
        with _session_scope(self.db_handler) as session:
            node = self.asset_repo.get_by_id(session, node_id)
            if not node:
                raise NotFoundError("asset not found")
            return self.asset_repo.get_node_devices(session, node_id)

    def get_asset_tree(self, root_asset_id: str) -> List[Dict[str, Any]]:
        with _session_scope(self.db_handler) as session:
            root = self.asset_repo.get_by_id(session, root_asset_id)
            if not root:
                raise NotFoundError("asset not found")
            return self.asset_repo.get_asset_tree(session, root_asset_id)

    def get_offline_assets(self, project_id: str, offline_minutes: int = 15) -> List[Dict[str, Any]]:
        with _session_scope(self.db_handler) as session:
            project = self.project_repo.get_by_id(session, project_id)
            if not project:
                raise NotFoundError("project not found")
            return self.asset_repo.get_offline_assets(session, project_id, offline_minutes=offline_minutes)

    def update(self, asset_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        _ensure_metadata_object(payload)
        with _session_scope(self.db_handler) as session:
            current = self.asset_repo.get_by_id(session, asset_id)
            if not current:
                raise NotFoundError("asset not found")

            merged = copy.deepcopy(current)
            merged.update(payload)
            merged["project_id"] = str(current["project_id"])
            merged["asset_type"] = payload.get("asset_type", str(current["asset_type"]))
            merged["sector_id"] = payload.get("sector_id", str(current["sector_id"]))
            merged["parent_asset_id"] = payload.get("parent_asset_id", current.get("parent_asset_id"))

            if "sector_id" in payload:
                self._validate_project_sector(session, str(current["project_id"]), payload["sector_id"])
            if payload.get("location_id"):
                location = self.location_repo.get_by_id(session, payload["location_id"])
                if not location:
                    raise NotFoundError("location not found")

            if "mac_address" in payload:
                payload["mac_address"] = _normalize_mac(payload.get("mac_address"))
            self._validate_parent(session, merged, current_asset_id=asset_id)

            updated = self.asset_repo.update(session, asset_id, payload)
            if not updated:
                raise NotFoundError("asset not found")
            return updated

    def soft_delete(self, asset_id: str) -> Dict[str, Any]:
        with _session_scope(self.db_handler) as session:
            current = self.asset_repo.get_by_id(session, asset_id)
            if not current:
                raise NotFoundError("asset not found")
            self.asset_repo.retire_subtree(session, asset_id)
            subtree = self.asset_repo.get_asset_tree(session, asset_id)
            subtree_ids = {str(item["id"]) for item in subtree}
            project_links = self.topology_repo.list_by_project(session, str(current["project_id"]))
            links = [
                link
                for link in project_links
                if str(link.get("source_asset_id") or "") in subtree_ids
                or str(link.get("target_asset_id") or "") in subtree_ids
            ]
            for link in links:
                self.topology_repo.update(session, str(link["id"]), {"status": "inactive"})
            return self.asset_repo.get_by_id(session, asset_id)

    def provision_node_bundle(self, project_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transactional creation of node + children + topology links."""
        _ensure_metadata_object(payload.get("node", {}))
        for child in payload.get("children", []):
            _ensure_metadata_object(child)

        with _session_scope(self.db_handler) as session:
            sector_id = payload["sector_id"]
            self._validate_project_sector(session, project_id, sector_id)

            node_payload = {
                "project_id": project_id,
                "sector_id": sector_id,
                "asset_type": "programmable_node",
                "subtype": payload["node"]["subtype"],
                "name": payload["node"]["name"],
                "code": payload["node"].get("code"),
                "description": payload["node"].get("description"),
                "status": payload["node"].get("status", "active"),
                "metadata": payload["node"].get("metadata", {}),
            }
            node = self.asset_repo.create(session, node_payload)
            node_id = str(node["id"])

            created_children: List[Dict[str, Any]] = []
            for child in payload.get("children", []):
                child_payload = {
                    "project_id": project_id,
                    "sector_id": sector_id,
                    "parent_asset_id": node_id,
                    "asset_type": child["asset_type"],
                    "subtype": child["subtype"],
                    "name": child["name"],
                    "code": child.get("code"),
                    "description": child.get("description"),
                    "status": child.get("status", "active"),
                    "metadata": child.get("metadata", {}),
                }
                created_children.append(self.asset_repo.create(session, child_payload))

            created_links: List[Dict[str, Any]] = []
            if payload.get("create_topology_links", True):
                sector_contains = {
                    "project_id": project_id,
                    "source_sector_id": sector_id,
                    "target_asset_id": node_id,
                    "relation_type": "contains",
                    "ports": [],
                    "status": "active",
                    "metadata": {"auto_provisioned": True},
                }
                if not self.topology_repo.exists_same_relation(session, sector_contains):
                    created_links.append(self.topology_repo.create(session, sector_contains))

                for child in created_children:
                    relation_type = "reads" if str(child["asset_type"]) == "sensor" else "controls"
                    link_payload = {
                        "project_id": project_id,
                        "source_asset_id": node_id,
                        "target_asset_id": str(child["id"]),
                        "relation_type": relation_type,
                        "ports": [],
                        "status": "active",
                        "metadata": {"auto_provisioned": True},
                    }
                    if not self.topology_repo.exists_same_relation(session, link_payload):
                        created_links.append(self.topology_repo.create(session, link_payload))

            return {
                "project_id": project_id,
                "sector_id": sector_id,
                "node": node,
                "children": created_children,
                "topology_links": created_links,
            }


class TopologyService:
    def __init__(
        self,
        db_handler,
        project_repo: Optional[ProjectRepository] = None,
        sector_repo: Optional[SectorRepository] = None,
        asset_repo: Optional[AssetRepository] = None,
        topology_repo: Optional[TopologyLinkRepository] = None,
    ):
        self.db_handler = db_handler
        self.project_repo = project_repo or ProjectRepository()
        self.sector_repo = sector_repo or SectorRepository()
        self.asset_repo = asset_repo or AssetRepository()
        self.topology_repo = topology_repo or TopologyLinkRepository()

    @staticmethod
    def _validate_source_target_payload(payload: Dict[str, Any]) -> None:
        source_count = int(payload.get("source_asset_id") is not None) + int(payload.get("source_sector_id") is not None)
        target_count = int(payload.get("target_asset_id") is not None) + int(payload.get("target_sector_id") is not None)
        if source_count != 1:
            raise ValidationDomainError("exactly one source must be provided (asset or sector)")
        if target_count != 1:
            raise ValidationDomainError("exactly one target must be provided (asset or sector)")
        if payload.get("source_asset_id") and payload.get("target_asset_id"):
            if str(payload["source_asset_id"]) == str(payload["target_asset_id"]):
                raise ConflictError("source_asset_id and target_asset_id cannot be the same")
        if payload.get("source_sector_id") and payload.get("target_sector_id"):
            if str(payload["source_sector_id"]) == str(payload["target_sector_id"]):
                raise ConflictError("source_sector_id and target_sector_id cannot be the same")

    def _assert_entity_project(self, session, project_id: str, payload: Dict[str, Any]) -> None:
        project = self.project_repo.get_by_id(session, project_id)
        if not project:
            raise NotFoundError("project not found")

        for field_name, getter in (
            ("source_asset_id", self.asset_repo.get_by_id),
            ("target_asset_id", self.asset_repo.get_by_id),
            ("source_sector_id", self.sector_repo.get_by_id),
            ("target_sector_id", self.sector_repo.get_by_id),
        ):
            entity_id = payload.get(field_name)
            if not entity_id:
                continue
            entity = getter(session, entity_id)
            if not entity:
                raise NotFoundError(f"{field_name} not found")
            if str(entity["project_id"]) != str(project_id):
                raise ConflictError(f"{field_name} belongs to a different project")

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        _ensure_metadata_object(payload)
        self._validate_source_target_payload(payload)
        with _session_scope(self.db_handler) as session:
            self._assert_entity_project(session, payload["project_id"], payload)
            if self.topology_repo.exists_same_relation(session, payload):
                raise ConflictError("duplicate topology relation")
            return self.topology_repo.create(session, payload)

    def get_by_id(self, link_id: str) -> Dict[str, Any]:
        with _session_scope(self.db_handler) as session:
            link = self.topology_repo.get_by_id(session, link_id)
            if not link:
                raise NotFoundError("topology link not found")
            return link

    def update(self, link_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        _ensure_metadata_object(payload)
        with _session_scope(self.db_handler) as session:
            current = self.topology_repo.get_by_id(session, link_id)
            if not current:
                raise NotFoundError("topology link not found")
            merged = copy.deepcopy(current)
            merged.update(payload)
            merged["project_id"] = str(current["project_id"])
            self._validate_source_target_payload(merged)
            self._assert_entity_project(session, str(current["project_id"]), merged)
            if self.topology_repo.exists_same_relation(session, merged, exclude_id=link_id):
                raise ConflictError("duplicate topology relation")
            updated = self.topology_repo.update(session, link_id, payload)
            if not updated:
                raise NotFoundError("topology link not found")
            return updated

    def delete(self, link_id: str) -> None:
        with _session_scope(self.db_handler) as session:
            deleted = self.topology_repo.delete(session, link_id)
            if not deleted:
                raise NotFoundError("topology link not found")

    def list_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        with _session_scope(self.db_handler) as session:
            project = self.project_repo.get_by_id(session, project_id)
            if not project:
                raise NotFoundError("project not found")
            return self.topology_repo.list_by_project(session, project_id)

    def list_by_asset(self, asset_id: str) -> List[Dict[str, Any]]:
        with _session_scope(self.db_handler) as session:
            asset = self.asset_repo.get_by_id(session, asset_id)
            if not asset:
                raise NotFoundError("asset not found")
            return self.topology_repo.list_by_asset(session, asset_id)

    def get_project_topology(self, project_id: str) -> List[Dict[str, Any]]:
        with _session_scope(self.db_handler) as session:
            project = self.project_repo.get_by_id(session, project_id)
            if not project:
                raise NotFoundError("project not found")
            return self.topology_repo.get_project_topology(session, project_id)
