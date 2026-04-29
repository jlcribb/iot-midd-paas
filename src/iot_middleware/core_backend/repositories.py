"""Repository layer for core public schema."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def _row_to_dict(row: Any) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    return dict(row)


def _rows_to_dicts(rows: Iterable[Any]) -> List[Dict[str, Any]]:
    return [_row_to_dict(row) for row in rows]


def _json_value(value: Optional[Any]) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=True)


class ProjectRepository:
    def create(self, session: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        row = session.execute(
            text(
                """
                INSERT INTO public.projects (name, description, status, metadata)
                VALUES (
                    :name,
                    :description,
                    CAST(:status AS project_status_enum),
                    CAST(:metadata AS jsonb)
                )
                RETURNING id::text AS id, name, description, status::text AS status, metadata, created_at, updated_at
                """
            ),
            {
                "name": payload.get("name"),
                "description": payload.get("description"),
                "status": payload.get("status", "draft"),
                "metadata": _json_value(payload.get("metadata")),
            },
        ).mappings().first()
        return _row_to_dict(row)

    def get_by_id(self, session: Session, project_id: str) -> Optional[Dict[str, Any]]:
        row = session.execute(
            text(
                """
                SELECT id::text AS id, name, description, status::text AS status, metadata, created_at, updated_at
                FROM public.projects
                WHERE id = CAST(:project_id AS uuid)
                """
            ),
            {"project_id": project_id},
        ).mappings().first()
        return _row_to_dict(row)

    def list(self, session: Session, status: Optional[str] = None, include_archived: bool = True) -> List[Dict[str, Any]]:
        rows = session.execute(
            text(
                """
                SELECT id::text AS id, name, description, status::text AS status, metadata, created_at, updated_at
                FROM public.projects
                WHERE (:status IS NULL OR status = CAST(:status AS project_status_enum))
                  AND (:include_archived OR status <> CAST('archived' AS project_status_enum))
                ORDER BY created_at DESC
                """
            ),
            {
                "status": status,
                "include_archived": include_archived,
            },
        ).mappings().all()
        return _rows_to_dicts(rows)

    def update(self, session: Session, project_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not payload:
            return self.get_by_id(session, project_id)

        setters = []
        params: Dict[str, Any] = {"project_id": project_id}
        if "name" in payload:
            setters.append("name = :name")
            params["name"] = payload.get("name")
        if "description" in payload:
            setters.append("description = :description")
            params["description"] = payload.get("description")
        if "status" in payload:
            setters.append("status = CAST(:status AS project_status_enum)")
            params["status"] = payload.get("status")
        if "metadata" in payload:
            setters.append("metadata = CAST(:metadata AS jsonb)")
            params["metadata"] = _json_value(payload.get("metadata"))

        row = session.execute(
            text(
                f"""
                UPDATE public.projects
                SET {", ".join(setters)}
                WHERE id = CAST(:project_id AS uuid)
                RETURNING id::text AS id, name, description, status::text AS status, metadata, created_at, updated_at
                """
            ),
            params,
        ).mappings().first()
        return _row_to_dict(row)

    def archive(self, session: Session, project_id: str) -> Optional[Dict[str, Any]]:
        return self.update(session, project_id, {"status": "archived"})


class LocationRepository:
    def create(self, session: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        row = session.execute(
            text(
                """
                INSERT INTO public.locations (
                    name, description, latitude, longitude, altitude, accuracy_meters,
                    country, province, city, address_text, building, floor, zone, rack, position, metadata
                )
                VALUES (
                    :name, :description, :latitude, :longitude, :altitude, :accuracy_meters,
                    :country, :province, :city, :address_text, :building, :floor, :zone, :rack, :position,
                    CAST(:metadata AS jsonb)
                )
                RETURNING *
                """
            ),
            {
                **payload,
                "metadata": _json_value(payload.get("metadata")),
            },
        ).mappings().first()
        return _row_to_dict(row)

    def get_by_id(self, session: Session, location_id: str) -> Optional[Dict[str, Any]]:
        row = session.execute(
            text("SELECT * FROM public.locations WHERE id = CAST(:location_id AS uuid)"),
            {"location_id": location_id},
        ).mappings().first()
        return _row_to_dict(row)

    def update(self, session: Session, location_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not payload:
            return self.get_by_id(session, location_id)
        setters = []
        params: Dict[str, Any] = {"location_id": location_id}
        for key in (
            "name",
            "description",
            "latitude",
            "longitude",
            "altitude",
            "accuracy_meters",
            "country",
            "province",
            "city",
            "address_text",
            "building",
            "floor",
            "zone",
            "rack",
            "position",
        ):
            if key in payload:
                setters.append(f"{key} = :{key}")
                params[key] = payload.get(key)
        if "metadata" in payload:
            setters.append("metadata = CAST(:metadata AS jsonb)")
            params["metadata"] = _json_value(payload.get("metadata"))
        row = session.execute(
            text(
                f"""
                UPDATE public.locations
                SET {", ".join(setters)}
                WHERE id = CAST(:location_id AS uuid)
                RETURNING *
                """
            ),
            params,
        ).mappings().first()
        return _row_to_dict(row)

    def list(self, session: Session, query: Optional[str] = None, city: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = session.execute(
            text(
                """
                SELECT *
                FROM public.locations
                WHERE
                    (:city IS NULL OR city = :city)
                    AND (
                        :query IS NULL
                        OR name ILIKE '%' || :query || '%'
                        OR COALESCE(address_text, '') ILIKE '%' || :query || '%'
                        OR COALESCE(province, '') ILIKE '%' || :query || '%'
                        OR COALESCE(country, '') ILIKE '%' || :query || '%'
                    )
                ORDER BY created_at DESC
                """
            ),
            {
                "query": query,
                "city": city,
            },
        ).mappings().all()
        return _rows_to_dicts(rows)


class SectorRepository:
    def create(self, session: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        row = session.execute(
            text(
                """
                INSERT INTO public.sectors (project_id, location_id, name, code, description, metadata)
                VALUES (
                    CAST(:project_id AS uuid),
                    CAST(:location_id AS uuid),
                    :name,
                    :code,
                    :description,
                    CAST(:metadata AS jsonb)
                )
                RETURNING *
                """
            ),
            {
                **payload,
                "metadata": _json_value(payload.get("metadata")),
            },
        ).mappings().first()
        return _row_to_dict(row)

    def get_by_id(self, session: Session, sector_id: str) -> Optional[Dict[str, Any]]:
        row = session.execute(
            text("SELECT * FROM public.sectors WHERE id = CAST(:sector_id AS uuid)"),
            {"sector_id": sector_id},
        ).mappings().first()
        return _row_to_dict(row)

    def list_by_project(self, session: Session, project_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        rows = session.execute(
            text(
                """
                SELECT *
                FROM public.sectors
                WHERE project_id = CAST(:project_id AS uuid)
                  AND (NOT :active_only OR is_active = true)
                ORDER BY name
                """
            ),
            {"project_id": project_id, "active_only": active_only},
        ).mappings().all()
        return _rows_to_dicts(rows)

    def update(self, session: Session, sector_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not payload:
            return self.get_by_id(session, sector_id)
        setters = []
        params: Dict[str, Any] = {"sector_id": sector_id}
        for key in ("location_id", "name", "code", "description"):
            if key in payload:
                if key == "location_id":
                    setters.append("location_id = CAST(:location_id AS uuid)")
                else:
                    setters.append(f"{key} = :{key}")
                params[key] = payload.get(key)
        if "metadata" in payload:
            setters.append("metadata = CAST(:metadata AS jsonb)")
            params["metadata"] = _json_value(payload.get("metadata"))
        row = session.execute(
            text(
                f"""
                UPDATE public.sectors
                SET {", ".join(setters)}
                WHERE id = CAST(:sector_id AS uuid)
                RETURNING *
                """
            ),
            params,
        ).mappings().first()
        return _row_to_dict(row)

    def set_active(self, session: Session, sector_id: str, is_active: bool) -> Optional[Dict[str, Any]]:
        row = session.execute(
            text(
                """
                UPDATE public.sectors
                SET
                    is_active = :is_active,
                    metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:patch AS jsonb)
                WHERE id = CAST(:sector_id AS uuid)
                RETURNING *
                """
            ),
            {
                "sector_id": sector_id,
                "is_active": bool(is_active),
                "patch": _json_value({"is_active": bool(is_active)}),
            },
        ).mappings().first()
        return _row_to_dict(row)

    def exists_name(self, session: Session, project_id: str, name: str, exclude_id: Optional[str] = None) -> bool:
        row = session.execute(
            text(
                """
                SELECT 1
                FROM public.sectors
                WHERE project_id = CAST(:project_id AS uuid)
                  AND lower(name) = lower(:name)
                  AND (:exclude_id IS NULL OR id <> CAST(:exclude_id AS uuid))
                LIMIT 1
                """
            ),
            {
                "project_id": project_id,
                "name": name,
                "exclude_id": exclude_id,
            },
        ).first()
        return row is not None

    def exists_code(self, session: Session, project_id: str, code: str, exclude_id: Optional[str] = None) -> bool:
        row = session.execute(
            text(
                """
                SELECT 1
                FROM public.sectors
                WHERE project_id = CAST(:project_id AS uuid)
                  AND code = :code
                  AND (:exclude_id IS NULL OR id <> CAST(:exclude_id AS uuid))
                LIMIT 1
                """
            ),
            {
                "project_id": project_id,
                "code": code,
                "exclude_id": exclude_id,
            },
        ).first()
        return row is not None


class AssetRepository:
    def create(self, session: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        params = {
            "project_id": payload.get("project_id"),
            "sector_id": payload.get("sector_id"),
            "location_id": payload.get("location_id"),
            "parent_asset_id": payload.get("parent_asset_id"),
            "asset_type": payload.get("asset_type"),
            "subtype": payload.get("subtype"),
            "name": payload.get("name"),
            "code": payload.get("code"),
            "description": payload.get("description"),
            "status": payload.get("status", "inactive"),
            "role": payload.get("role"),
            "serial_number": payload.get("serial_number"),
            "manufacturer": payload.get("manufacturer"),
            "model": payload.get("model"),
            "firmware_version": payload.get("firmware_version"),
            "hardware_version": payload.get("hardware_version"),
            "mac_address": payload.get("mac_address"),
            "ip_address": payload.get("ip_address"),
            "last_seen_at": payload.get("last_seen_at"),
            "metadata": _json_value(payload.get("metadata")),
        }
        row = session.execute(
            text(
                """
                INSERT INTO public.assets (
                    project_id, sector_id, location_id, parent_asset_id, asset_type, subtype, name, code, description,
                    status, role, serial_number, manufacturer, model, firmware_version, hardware_version,
                    mac_address, ip_address, last_seen_at, metadata
                )
                VALUES (
                    CAST(:project_id AS uuid),
                    CAST(:sector_id AS uuid),
                    CAST(:location_id AS uuid),
                    CAST(:parent_asset_id AS uuid),
                    CAST(:asset_type AS asset_type_enum),
                    :subtype,
                    :name,
                    :code,
                    :description,
                    CAST(:status AS asset_status_enum),
                    :role,
                    :serial_number,
                    :manufacturer,
                    :model,
                    :firmware_version,
                    :hardware_version,
                    :mac_address,
                    CAST(:ip_address AS inet),
                    CAST(:last_seen_at AS timestamptz),
                    CAST(:metadata AS jsonb)
                )
                RETURNING *
                """
            ),
            params,
        ).mappings().first()
        return _row_to_dict(row)

    def get_by_id(self, session: Session, asset_id: str) -> Optional[Dict[str, Any]]:
        row = session.execute(
            text("SELECT * FROM public.assets WHERE id = CAST(:asset_id AS uuid)"),
            {"asset_id": asset_id},
        ).mappings().first()
        return _row_to_dict(row)

    def list_by_project(self, session: Session, project_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        rows = session.execute(
            text(
                """
                SELECT *
                FROM public.assets
                WHERE project_id = CAST(:project_id AS uuid)
                  AND (NOT :active_only OR status <> CAST('retired' AS asset_status_enum))
                ORDER BY created_at DESC
                """
            ),
            {"project_id": project_id, "active_only": active_only},
        ).mappings().all()
        return _rows_to_dicts(rows)

    def list_by_sector(self, session: Session, sector_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        rows = session.execute(
            text(
                """
                SELECT *
                FROM public.assets
                WHERE sector_id = CAST(:sector_id AS uuid)
                  AND (NOT :active_only OR status <> CAST('retired' AS asset_status_enum))
                ORDER BY created_at DESC
                """
            ),
            {"sector_id": sector_id, "active_only": active_only},
        ).mappings().all()
        return _rows_to_dicts(rows)

    def list_children(self, session: Session, parent_asset_id: str) -> List[Dict[str, Any]]:
        rows = session.execute(
            text(
                """
                SELECT *
                FROM public.assets
                WHERE parent_asset_id = CAST(:parent_asset_id AS uuid)
                ORDER BY created_at ASC
                """
            ),
            {"parent_asset_id": parent_asset_id},
        ).mappings().all()
        return _rows_to_dicts(rows)

    def update(self, session: Session, asset_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not payload:
            return self.get_by_id(session, asset_id)

        setters = []
        params: Dict[str, Any] = {"asset_id": asset_id}
        cast_uuid = {"sector_id", "location_id", "parent_asset_id"}
        for key in (
            "sector_id",
            "location_id",
            "parent_asset_id",
            "subtype",
            "name",
            "code",
            "description",
            "role",
            "serial_number",
            "manufacturer",
            "model",
            "firmware_version",
            "hardware_version",
            "mac_address",
            "ip_address",
            "last_seen_at",
        ):
            if key in payload:
                if key in cast_uuid:
                    setters.append(f"{key} = CAST(:{key} AS uuid)")
                elif key == "ip_address":
                    setters.append("ip_address = CAST(:ip_address AS inet)")
                elif key == "last_seen_at":
                    setters.append("last_seen_at = CAST(:last_seen_at AS timestamptz)")
                else:
                    setters.append(f"{key} = :{key}")
                params[key] = payload.get(key)
        if "asset_type" in payload:
            setters.append("asset_type = CAST(:asset_type AS asset_type_enum)")
            params["asset_type"] = payload.get("asset_type")
        if "status" in payload:
            setters.append("status = CAST(:status AS asset_status_enum)")
            params["status"] = payload.get("status")
        if "metadata" in payload:
            setters.append("metadata = CAST(:metadata AS jsonb)")
            params["metadata"] = _json_value(payload.get("metadata"))

        row = session.execute(
            text(
                f"""
                UPDATE public.assets
                SET {", ".join(setters)}
                WHERE id = CAST(:asset_id AS uuid)
                RETURNING *
                """
            ),
            params,
        ).mappings().first()
        return _row_to_dict(row)

    def set_status(self, session: Session, asset_id: str, status: str, patch_metadata: Optional[Dict[str, Any]] = None) -> None:
        if patch_metadata is None:
            session.execute(
                text(
                    """
                    UPDATE public.assets
                    SET status = CAST(:status AS asset_status_enum)
                    WHERE id = CAST(:asset_id AS uuid)
                    """
                ),
                {"asset_id": asset_id, "status": status},
            )
            return
        session.execute(
            text(
                """
                UPDATE public.assets
                SET
                    status = CAST(:status AS asset_status_enum),
                    metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:patch AS jsonb)
                WHERE id = CAST(:asset_id AS uuid)
                """
            ),
            {
                "asset_id": asset_id,
                "status": status,
                "patch": _json_value(patch_metadata),
            },
        )

    def get_node_devices(self, session: Session, node_id: str) -> List[Dict[str, Any]]:
        rows = session.execute(
            text(
                """
                SELECT *
                FROM public.assets
                WHERE parent_asset_id = CAST(:node_id AS uuid)
                  AND asset_type IN (CAST('sensor' AS asset_type_enum), CAST('actuator' AS asset_type_enum))
                ORDER BY name
                """
            ),
            {"node_id": node_id},
        ).mappings().all()
        return _rows_to_dicts(rows)

    def get_offline_assets(self, session: Session, project_id: str, offline_minutes: int = 15) -> List[Dict[str, Any]]:
        rows = session.execute(
            text(
                """
                SELECT *
                FROM public.assets
                WHERE project_id = CAST(:project_id AS uuid)
                  AND (
                    status = CAST('offline' AS asset_status_enum)
                    OR (
                        last_seen_at IS NOT NULL
                        AND last_seen_at < now() - make_interval(mins => :offline_minutes)
                    )
                  )
                ORDER BY last_seen_at ASC NULLS FIRST, created_at DESC
                """
            ),
            {"project_id": project_id, "offline_minutes": offline_minutes},
        ).mappings().all()
        return _rows_to_dicts(rows)

    def get_asset_tree(self, session: Session, root_asset_id: str) -> List[Dict[str, Any]]:
        rows = session.execute(
            text(
                """
                WITH RECURSIVE tree AS (
                    SELECT
                        a.*,
                        0::int AS depth
                    FROM public.assets a
                    WHERE a.id = CAST(:root_asset_id AS uuid)
                    UNION ALL
                    SELECT
                        c.*,
                        t.depth + 1
                    FROM public.assets c
                    JOIN tree t ON c.parent_asset_id = t.id
                )
                SELECT *
                FROM tree
                ORDER BY depth, name
                """
            ),
            {"root_asset_id": root_asset_id},
        ).mappings().all()
        return _rows_to_dicts(rows)

    def get_project_assets_map(self, session: Session, project_id: str) -> Dict[str, Dict[str, Any]]:
        rows = session.execute(
            text("SELECT * FROM public.assets WHERE project_id = CAST(:project_id AS uuid)"),
            {"project_id": project_id},
        ).mappings().all()
        return {str(row["id"]): _row_to_dict(row) for row in rows}

    def retire_subtree(self, session: Session, root_asset_id: str) -> None:
        session.execute(
            text(
                """
                WITH RECURSIVE descendants AS (
                    SELECT id, 0::int AS depth
                    FROM public.assets
                    WHERE id = CAST(:root_asset_id AS uuid)
                    UNION ALL
                    SELECT a.id, d.depth + 1
                    FROM public.assets a
                    JOIN descendants d ON a.parent_asset_id = d.id
                )
                UPDATE public.assets a
                SET
                    status = CASE
                        WHEN a.id = CAST(:root_asset_id AS uuid) THEN CAST('retired' AS asset_status_enum)
                        ELSE CAST('inactive' AS asset_status_enum)
                    END,
                    metadata = COALESCE(a.metadata, '{}'::jsonb) || '{"is_active": false}'::jsonb
                FROM descendants d
                WHERE a.id = d.id
                """
            ),
            {"root_asset_id": root_asset_id},
        )


class TopologyLinkRepository:
    def create(self, session: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        params = {
            "project_id": payload.get("project_id"),
            "source_asset_id": payload.get("source_asset_id"),
            "target_asset_id": payload.get("target_asset_id"),
            "source_sector_id": payload.get("source_sector_id"),
            "target_sector_id": payload.get("target_sector_id"),
            "relation_type": payload.get("relation_type"),
            "connection_medium": payload.get("connection_medium"),
            "protocol": payload.get("protocol"),
            "ports": _json_value(payload.get("ports", [])),
            "link_quality": payload.get("link_quality"),
            "status": payload.get("status", "active"),
            "metadata": _json_value(payload.get("metadata")),
        }
        row = session.execute(
            text(
                """
                INSERT INTO public.topology_links (
                    project_id, source_asset_id, target_asset_id, source_sector_id, target_sector_id,
                    relation_type, connection_medium, protocol, ports, link_quality, status, metadata
                )
                VALUES (
                    CAST(:project_id AS uuid),
                    CAST(:source_asset_id AS uuid),
                    CAST(:target_asset_id AS uuid),
                    CAST(:source_sector_id AS uuid),
                    CAST(:target_sector_id AS uuid),
                    CAST(:relation_type AS topology_relation_enum),
                    :connection_medium,
                    :protocol,
                    CAST(:ports AS jsonb),
                    :link_quality,
                    CAST(:status AS link_status_enum),
                    CAST(:metadata AS jsonb)
                )
                RETURNING *
                """
            ),
            params,
        ).mappings().first()
        return _row_to_dict(row)

    def get_by_id(self, session: Session, link_id: str) -> Optional[Dict[str, Any]]:
        row = session.execute(
            text("SELECT * FROM public.topology_links WHERE id = CAST(:link_id AS uuid)"),
            {"link_id": link_id},
        ).mappings().first()
        return _row_to_dict(row)

    def update(self, session: Session, link_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not payload:
            return self.get_by_id(session, link_id)

        setters = []
        params: Dict[str, Any] = {"link_id": link_id}
        for key in (
            "source_asset_id",
            "target_asset_id",
            "source_sector_id",
            "target_sector_id",
            "connection_medium",
            "protocol",
            "link_quality",
        ):
            if key in payload:
                if key.endswith("_id"):
                    setters.append(f"{key} = CAST(:{key} AS uuid)")
                else:
                    setters.append(f"{key} = :{key}")
                params[key] = payload.get(key)
        if "relation_type" in payload:
            setters.append("relation_type = CAST(:relation_type AS topology_relation_enum)")
            params["relation_type"] = payload.get("relation_type")
        if "status" in payload:
            setters.append("status = CAST(:status AS link_status_enum)")
            params["status"] = payload.get("status")
        if "ports" in payload:
            setters.append("ports = CAST(:ports AS jsonb)")
            params["ports"] = _json_value(payload.get("ports", []))
        if "metadata" in payload:
            setters.append("metadata = CAST(:metadata AS jsonb)")
            params["metadata"] = _json_value(payload.get("metadata"))

        row = session.execute(
            text(
                f"""
                UPDATE public.topology_links
                SET {", ".join(setters)}
                WHERE id = CAST(:link_id AS uuid)
                RETURNING *
                """
            ),
            params,
        ).mappings().first()
        return _row_to_dict(row)

    def delete(self, session: Session, link_id: str) -> bool:
        row = session.execute(
            text("DELETE FROM public.topology_links WHERE id = CAST(:link_id AS uuid) RETURNING id"),
            {"link_id": link_id},
        ).first()
        return row is not None

    def list_by_project(self, session: Session, project_id: str) -> List[Dict[str, Any]]:
        rows = session.execute(
            text(
                """
                SELECT *
                FROM public.topology_links
                WHERE project_id = CAST(:project_id AS uuid)
                ORDER BY created_at DESC
                """
            ),
            {"project_id": project_id},
        ).mappings().all()
        return _rows_to_dicts(rows)

    def list_by_asset(self, session: Session, asset_id: str) -> List[Dict[str, Any]]:
        rows = session.execute(
            text(
                """
                SELECT *
                FROM public.topology_links
                WHERE
                    source_asset_id = CAST(:asset_id AS uuid)
                    OR target_asset_id = CAST(:asset_id AS uuid)
                ORDER BY created_at DESC
                """
            ),
            {"asset_id": asset_id},
        ).mappings().all()
        return _rows_to_dicts(rows)

    def get_project_topology(self, session: Session, project_id: str) -> List[Dict[str, Any]]:
        rows = session.execute(
            text(
                """
                SELECT
                    tl.*,
                    sa.name AS source_asset_name,
                    ta.name AS target_asset_name,
                    ss.name AS source_sector_name,
                    ts.name AS target_sector_name
                FROM public.topology_links tl
                LEFT JOIN public.assets sa ON sa.id = tl.source_asset_id
                LEFT JOIN public.assets ta ON ta.id = tl.target_asset_id
                LEFT JOIN public.sectors ss ON ss.id = tl.source_sector_id
                LEFT JOIN public.sectors ts ON ts.id = tl.target_sector_id
                WHERE tl.project_id = CAST(:project_id AS uuid)
                ORDER BY tl.created_at DESC
                """
            ),
            {"project_id": project_id},
        ).mappings().all()
        return _rows_to_dicts(rows)

    def exists_same_relation(
        self,
        session: Session,
        payload: Dict[str, Any],
        exclude_id: Optional[str] = None,
    ) -> bool:
        row = session.execute(
            text(
                """
                SELECT 1
                FROM public.topology_links
                WHERE project_id = CAST(:project_id AS uuid)
                  AND relation_type = CAST(:relation_type AS topology_relation_enum)
                  AND COALESCE(source_asset_id, '00000000-0000-0000-0000-000000000000'::uuid)
                      = COALESCE(CAST(:source_asset_id AS uuid), '00000000-0000-0000-0000-000000000000'::uuid)
                  AND COALESCE(target_asset_id, '00000000-0000-0000-0000-000000000000'::uuid)
                      = COALESCE(CAST(:target_asset_id AS uuid), '00000000-0000-0000-0000-000000000000'::uuid)
                  AND COALESCE(source_sector_id, '00000000-0000-0000-0000-000000000000'::uuid)
                      = COALESCE(CAST(:source_sector_id AS uuid), '00000000-0000-0000-0000-000000000000'::uuid)
                  AND COALESCE(target_sector_id, '00000000-0000-0000-0000-000000000000'::uuid)
                      = COALESCE(CAST(:target_sector_id AS uuid), '00000000-0000-0000-0000-000000000000'::uuid)
                  AND (:exclude_id IS NULL OR id <> CAST(:exclude_id AS uuid))
                LIMIT 1
                """
            ),
            {
                "project_id": payload.get("project_id"),
                "relation_type": payload.get("relation_type"),
                "source_asset_id": payload.get("source_asset_id"),
                "target_asset_id": payload.get("target_asset_id"),
                "source_sector_id": payload.get("source_sector_id"),
                "target_sector_id": payload.get("target_sector_id"),
                "exclude_id": exclude_id,
            },
        ).first()
        return row is not None
