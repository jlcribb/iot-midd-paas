"""
Router para exponer estructura core (public schema): projects, sectors, assets, topology_links.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text


router = APIRouter()


def _to_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _is_active_from_metadata(metadata: Any) -> bool:
    parsed = _to_dict(metadata)
    raw = parsed.get("is_active")
    if raw is None:
        return True
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _get_db_handler(request: Request):
    db_handler = request.app.state.db_handler
    if not db_handler:
        raise HTTPException(status_code=500, detail="Base de datos no inicializada")
    return db_handler


@router.get("/projects")
async def list_core_projects(
    request: Request,
    active: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    db_handler = _get_db_handler(request)
    with db_handler.get_session() as session:
        projects = session.execute(
            text(
                """
                SELECT
                    p.id::text AS id,
                    p.name,
                    p.description,
                    p.status::text AS status,
                    p.metadata,
                    p.created_at,
                    p.updated_at
                FROM public.projects p
                ORDER BY p.created_at DESC
                """
            )
        ).mappings().all()

        sector_counts = session.execute(
            text(
                """
                SELECT
                    s.project_id::text AS project_id,
                    count(*)::int AS total_sectors
                FROM public.sectors s
                GROUP BY s.project_id
                """
            )
        ).mappings().all()
        sector_map = {row["project_id"]: int(row["total_sectors"]) for row in sector_counts}

        asset_counts = session.execute(
            text(
                """
                SELECT
                    a.project_id::text AS project_id,
                    count(*)::int AS total_assets,
                    count(*) FILTER (WHERE a.status::text = 'active')::int AS active_assets
                FROM public.assets a
                GROUP BY a.project_id
                """
            )
        ).mappings().all()
        asset_map = {
            row["project_id"]: {
                "total_assets": int(row["total_assets"]),
                "active_assets": int(row["active_assets"]),
            }
            for row in asset_counts
        }

        payload: List[Dict[str, Any]] = []
        for row in projects:
            metadata = _to_dict(row["metadata"])
            status = str(row["status"])
            if active is True and status == "archived":
                continue
            if active is False and status != "archived":
                continue
            counts = asset_map.get(row["id"], {"total_assets": 0, "active_assets": 0})
            payload.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "status": status,
                    "legacy_project_id": metadata.get("legacy_project_id"),
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    "total_sectors": int(sector_map.get(row["id"], 0)),
                    "total_assets": counts["total_assets"],
                    "active_assets": counts["active_assets"],
                }
            )
        return payload


@router.get("/sectors")
async def list_core_sectors(
    request: Request,
    project_id: Optional[str] = None,
    legacy_project_id: Optional[str] = None,
    active: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    db_handler = _get_db_handler(request)
    with db_handler.get_session() as session:
        rows = session.execute(
            text(
                """
                SELECT
                    s.id::text AS id,
                    s.project_id::text AS project_id,
                    p.name AS project_name,
                    p.metadata->>'legacy_project_id' AS legacy_project_id,
                    s.name,
                    s.code,
                    s.description,
                    s.metadata,
                    s.created_at,
                    s.updated_at
                FROM public.sectors s
                JOIN public.projects p ON p.id = s.project_id
                WHERE (:project_id IS NULL OR s.project_id = CAST(:project_id AS uuid))
                  AND (:legacy_project_id IS NULL OR p.metadata->>'legacy_project_id' = :legacy_project_id)
                ORDER BY p.name, s.name
                """
            ),
            {
                "project_id": project_id,
                "legacy_project_id": legacy_project_id,
            },
        ).mappings().all()

        payload: List[Dict[str, Any]] = []
        for row in rows:
            metadata = _to_dict(row["metadata"])
            is_active = _is_active_from_metadata(metadata)
            if active is not None and bool(active) != bool(is_active):
                continue
            payload.append(
                {
                    "id": row["id"],
                    "project_id": row["project_id"],
                    "project_name": row["project_name"],
                    "legacy_project_id": row["legacy_project_id"],
                    "legacy_unit_id": metadata.get("legacy_unit_id"),
                    "name": row["name"],
                    "code": row["code"],
                    "description": row["description"],
                    "is_active": is_active,
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                }
            )
        return payload


@router.get("/assets")
async def list_core_assets(
    request: Request,
    project_id: Optional[str] = None,
    legacy_project_id: Optional[str] = None,
    sector_id: Optional[str] = None,
    active: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    db_handler = _get_db_handler(request)
    with db_handler.get_session() as session:
        rows = session.execute(
            text(
                """
                SELECT
                    a.id::text AS id,
                    a.project_id::text AS project_id,
                    p.name AS project_name,
                    p.metadata->>'legacy_project_id' AS legacy_project_id,
                    a.sector_id::text AS sector_id,
                    s.name AS sector_name,
                    a.asset_type::text AS asset_type,
                    a.subtype,
                    a.name,
                    a.code,
                    a.description,
                    a.status::text AS status,
                    a.metadata,
                    a.created_at,
                    a.updated_at
                FROM public.assets a
                JOIN public.projects p ON p.id = a.project_id
                JOIN public.sectors s ON s.id = a.sector_id
                WHERE (:project_id IS NULL OR a.project_id = CAST(:project_id AS uuid))
                  AND (:legacy_project_id IS NULL OR p.metadata->>'legacy_project_id' = :legacy_project_id)
                  AND (:sector_id IS NULL OR a.sector_id = CAST(:sector_id AS uuid))
                ORDER BY p.name, s.name, a.name
                """
            ),
            {
                "project_id": project_id,
                "legacy_project_id": legacy_project_id,
                "sector_id": sector_id,
            },
        ).mappings().all()

        payload: List[Dict[str, Any]] = []
        for row in rows:
            metadata = _to_dict(row["metadata"])
            status = str(row["status"])
            is_active = status == "active"
            if active is not None and bool(active) != bool(is_active):
                continue
            payload.append(
                {
                    "id": row["id"],
                    "project_id": row["project_id"],
                    "project_name": row["project_name"],
                    "legacy_project_id": row["legacy_project_id"],
                    "legacy_dispositivo_proyecto_id": metadata.get("legacy_dispositivo_proyecto_id"),
                    "legacy_unit_id": metadata.get("legacy_unidad_id"),
                    "sector_id": row["sector_id"],
                    "sector_name": row["sector_name"],
                    "asset_type": row["asset_type"],
                    "subtype": row["subtype"],
                    "name": row["name"],
                    "code": row["code"],
                    "description": row["description"],
                    "status": status,
                    "is_active": is_active,
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                }
            )
        return payload


@router.get("/stats")
async def get_core_stats(request: Request) -> Dict[str, Any]:
    projects = await list_core_projects(request)
    sectors = await list_core_sectors(request)
    assets = await list_core_assets(request)
    return {
        "total_projects": len(projects),
        "active_projects": len([p for p in projects if p["status"] == "active"]),
        "archived_projects": len([p for p in projects if p["status"] == "archived"]),
        "total_sectors": len(sectors),
        "active_sectors": len([s for s in sectors if s["is_active"]]),
        "total_assets": len(assets),
        "active_assets": len([a for a in assets if a["is_active"]]),
        "projects": projects,
    }
