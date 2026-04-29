"""Best-effort sync from DTE plant payload to core schema (public)."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator
from uuid import NAMESPACE_DNS, uuid5

import psycopg2
from psycopg2.extras import Json


SYNC_NAMESPACE = uuid5(NAMESPACE_DNS, "iot-middleware-dte-core-sync-v1")


def _stable_uuid(kind: str, value: str) -> str:
    return str(uuid5(SYNC_NAMESPACE, f"{kind}:{value}"))


@dataclass
class CoreSchemaSyncConfig:
    host: str
    port: int
    database: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "CoreSchemaSyncConfig":
        return cls(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "iot_middleware"),
            user=os.getenv("POSTGRES_USER", "iot_user"),
            password=os.getenv("POSTGRES_PASSWORD", "iot_password_2024"),
        )


@contextmanager
def _connection(cfg: CoreSchemaSyncConfig):
    conn = psycopg2.connect(
        host=cfg.host,
        port=cfg.port,
        dbname=cfg.database,
        user=cfg.user,
        password=cfg.password,
    )
    try:
        yield conn
    finally:
        conn.close()


def sync_plant_to_core_schema(payload: dict[str, Any], cfg: CoreSchemaSyncConfig | None = None) -> dict[str, Any]:
    """Create/update a DTE plant as core project + sectors + assets + links."""
    cfg = cfg or CoreSchemaSyncConfig.from_env()

    plant_id = str(payload.get("plant_id") or "").strip()
    if not plant_id:
        raise ValueError("Plant payload requires 'plant_id'")

    core_project_id = _stable_uuid("project", plant_id)
    units = payload.get("units") or []
    connections = payload.get("connections") or []

    with _connection(cfg) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.projects (id, name, description, status, metadata, created_at, updated_at)
                VALUES (%s::uuid, %s, %s, CAST('active' AS project_status_enum), %s::jsonb, now(), now())
                ON CONFLICT (id) DO UPDATE
                SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status,
                    metadata = EXCLUDED.metadata,
                    updated_at = now()
                """,
                (
                    core_project_id,
                    payload.get("name") or plant_id,
                    payload.get("description"),
                    Json({"source": "dte", "plant_id": plant_id}),
                ),
            )

            cur.execute("DELETE FROM public.topology_links WHERE project_id = %s::uuid", (core_project_id,))
            cur.execute("DELETE FROM public.assets WHERE project_id = %s::uuid", (core_project_id,))
            cur.execute("DELETE FROM public.sectors WHERE project_id = %s::uuid", (core_project_id,))

            sector_map: dict[str, str] = {}
            asset_map: dict[str, str] = {}

            for unit in units:
                unit_id = str(unit.get("id") or "").strip()
                if not unit_id:
                    continue
                sector_id = _stable_uuid("sector", f"{plant_id}:{unit_id}")
                asset_id = _stable_uuid("asset", f"{plant_id}:{unit_id}")
                sector_map[unit_id] = sector_id
                asset_map[unit_id] = asset_id
                model_type = str(unit.get("type") or "programmable_node")
                name = unit.get("name") or unit_id

                cur.execute(
                    """
                    INSERT INTO public.sectors (
                        id, project_id, location_id, name, code, description, metadata, created_at, updated_at
                    )
                    VALUES (%s::uuid, %s::uuid, NULL, %s, %s, %s, %s::jsonb, now(), now())
                    ON CONFLICT (id) DO UPDATE
                    SET
                        project_id = EXCLUDED.project_id,
                        name = EXCLUDED.name,
                        code = EXCLUDED.code,
                        description = EXCLUDED.description,
                        metadata = EXCLUDED.metadata,
                        updated_at = now()
                    """,
                    (
                        sector_id,
                        core_project_id,
                        name,
                        f"dte-unit-{unit_id}",
                        unit.get("description"),
                        Json({"source": "dte", "unit_id": unit_id, "model_type": model_type}),
                    ),
                )

                cur.execute(
                    """
                    INSERT INTO public.assets (
                        id, project_id, sector_id, location_id, parent_asset_id,
                        asset_type, subtype, name, code, description, status,
                        role, serial_number, manufacturer, model, firmware_version, hardware_version,
                        mac_address, ip_address, last_seen_at, metadata, created_at, updated_at
                    )
                    VALUES (
                        %s::uuid, %s::uuid, %s::uuid, NULL, NULL,
                        CAST('programmable_node' AS asset_type_enum), %s, %s, %s, %s, CAST('active' AS asset_status_enum),
                        NULL, NULL, NULL, NULL, NULL, NULL,
                        NULL, NULL, NULL, %s::jsonb, now(), now()
                    )
                    ON CONFLICT (id) DO UPDATE
                    SET
                        project_id = EXCLUDED.project_id,
                        sector_id = EXCLUDED.sector_id,
                        subtype = EXCLUDED.subtype,
                        name = EXCLUDED.name,
                        code = EXCLUDED.code,
                        description = EXCLUDED.description,
                        status = EXCLUDED.status,
                        metadata = EXCLUDED.metadata,
                        updated_at = now()
                    """,
                    (
                        asset_id,
                        core_project_id,
                        sector_id,
                        model_type,
                        name,
                        f"dte-asset-{unit_id}",
                        unit.get("description"),
                        Json({"source": "dte", "unit_id": unit_id, "model_type": model_type}),
                    ),
                )

                link_contains_id = _stable_uuid("link_contains", f"{sector_id}:{asset_id}")
                cur.execute(
                    """
                    INSERT INTO public.topology_links (
                        id, project_id, source_asset_id, target_asset_id, source_sector_id, target_sector_id,
                        relation_type, connection_medium, protocol, ports, link_quality, status, metadata,
                        created_at, updated_at
                    )
                    VALUES (
                        %s::uuid, %s::uuid, NULL, %s::uuid, %s::uuid, NULL,
                        CAST('contains' AS topology_relation_enum), NULL, NULL, '[]'::jsonb, NULL,
                        CAST('active' AS link_status_enum), %s::jsonb, now(), now()
                    )
                    ON CONFLICT (id) DO UPDATE
                    SET
                        target_asset_id = EXCLUDED.target_asset_id,
                        source_sector_id = EXCLUDED.source_sector_id,
                        status = EXCLUDED.status,
                        metadata = EXCLUDED.metadata,
                        updated_at = now()
                    """,
                    (
                        link_contains_id,
                        core_project_id,
                        asset_id,
                        sector_id,
                        Json({"source": "dte"}),
                    ),
                )

            for conn_spec in connections:
                from_ref = conn_spec.get("from")
                to_ref = conn_spec.get("to")
                if not from_ref or not to_ref:
                    continue
                from_unit = str(from_ref).split(".", 1)[0]
                to_unit = str(to_ref).split(".", 1)[0]
                source_asset = asset_map.get(from_unit)
                target_asset = asset_map.get(to_unit)
                if not source_asset or not target_asset:
                    continue
                link_id = _stable_uuid("link_connects", f"{source_asset}:{target_asset}:{from_ref}:{to_ref}")
                cur.execute(
                    """
                    INSERT INTO public.topology_links (
                        id, project_id, source_asset_id, target_asset_id, source_sector_id, target_sector_id,
                        relation_type, connection_medium, protocol, ports, link_quality, status, metadata,
                        created_at, updated_at
                    )
                    VALUES (
                        %s::uuid, %s::uuid, %s::uuid, %s::uuid, NULL, NULL,
                        CAST('connects_to' AS topology_relation_enum), NULL, NULL, '[]'::jsonb, NULL,
                        CAST('active' AS link_status_enum), %s::jsonb, now(), now()
                    )
                    ON CONFLICT (id) DO UPDATE
                    SET
                        source_asset_id = EXCLUDED.source_asset_id,
                        target_asset_id = EXCLUDED.target_asset_id,
                        status = EXCLUDED.status,
                        metadata = EXCLUDED.metadata,
                        updated_at = now()
                    """,
                    (
                        link_id,
                        core_project_id,
                        source_asset,
                        target_asset,
                        Json({"source": "dte", "from": from_ref, "to": to_ref}),
                    ),
                )

        conn.commit()

    return {
        "plant_id": plant_id,
        "core_project_id": core_project_id,
        "units": len([u for u in units if u.get("id")]),
        "connections": len([c for c in connections if c.get("from") and c.get("to")]),
    }
