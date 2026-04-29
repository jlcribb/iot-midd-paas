"""FastAPI router for core backend REST API."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, Request

from .errors import DomainError, map_sqlalchemy_error
from .schemas import (
    CreateAssetPayload,
    CreateLocationPayload,
    CreateProjectPayload,
    CreateSectorPayload,
    CreateTopologyLinkPayload,
    ProvisionNodeBundlePayload,
    UpdateAssetPayload,
    UpdateLocationPayload,
    UpdateProjectPayload,
    UpdateSectorPayload,
    UpdateTopologyLinkPayload,
)
from .services import AssetService, LocationService, ProjectService, SectorService, TopologyService


logger = logging.getLogger(__name__)
router = APIRouter()


def _build_services(request: Request) -> Dict[str, Any]:
    db_handler = request.app.state.db_handler
    if not db_handler:
        raise HTTPException(status_code=500, detail={"error": "db_not_initialized", "message": "database not initialized"})
    return {
        "projects": ProjectService(db_handler),
        "sectors": SectorService(db_handler),
        "locations": LocationService(db_handler),
        "assets": AssetService(db_handler),
        "topology": TopologyService(db_handler),
    }


def _raise_from_exception(exc: Exception) -> None:
    if isinstance(exc, DomainError):
        raise HTTPException(status_code=exc.status_code, detail=exc.to_payload())
    mapped = map_sqlalchemy_error(exc)
    if isinstance(mapped, DomainError):
        raise HTTPException(status_code=mapped.status_code, detail=mapped.to_payload())
    raise HTTPException(status_code=500, detail={"error": "internal_error", "message": str(exc)})


@router.post("/projects")
async def create_project(request: Request, payload: CreateProjectPayload):
    try:
        return _build_services(request)["projects"].create(payload.model_dump())
    except Exception as exc:
        _raise_from_exception(exc)


@router.get("/projects")
async def list_projects(
    request: Request,
    status: Optional[str] = Query(default=None),
    include_archived: bool = Query(default=True),
):
    try:
        return _build_services(request)["projects"].list(status=status, include_archived=include_archived)
    except Exception as exc:
        _raise_from_exception(exc)


@router.get("/projects/{project_id}")
async def get_project(request: Request, project_id: str):
    try:
        return _build_services(request)["projects"].get_by_id(project_id)
    except Exception as exc:
        _raise_from_exception(exc)


@router.patch("/projects/{project_id}")
async def update_project(request: Request, project_id: str, payload: UpdateProjectPayload):
    try:
        return _build_services(request)["projects"].update(project_id, payload.model_dump(exclude_unset=True))
    except Exception as exc:
        _raise_from_exception(exc)


@router.post("/sectors")
async def create_sector(request: Request, payload: CreateSectorPayload):
    try:
        return _build_services(request)["sectors"].create(payload.model_dump())
    except Exception as exc:
        _raise_from_exception(exc)


@router.get("/projects/{project_id}/sectors")
async def list_project_sectors(
    request: Request,
    project_id: str,
    active_only: bool = Query(default=True),
):
    try:
        return _build_services(request)["sectors"].list_by_project(project_id, active_only=active_only)
    except Exception as exc:
        _raise_from_exception(exc)


@router.get("/sectors/{sector_id}")
async def get_sector(request: Request, sector_id: str):
    try:
        return _build_services(request)["sectors"].get_by_id(sector_id)
    except Exception as exc:
        _raise_from_exception(exc)


@router.patch("/sectors/{sector_id}")
async def update_sector(request: Request, sector_id: str, payload: UpdateSectorPayload):
    try:
        return _build_services(request)["sectors"].update(sector_id, payload.model_dump(exclude_unset=True))
    except Exception as exc:
        _raise_from_exception(exc)


@router.delete("/sectors/{sector_id}")
async def delete_sector(request: Request, sector_id: str):
    try:
        return _build_services(request)["sectors"].soft_delete(sector_id)
    except Exception as exc:
        _raise_from_exception(exc)


@router.post("/locations")
async def create_location(request: Request, payload: CreateLocationPayload):
    try:
        return _build_services(request)["locations"].create(payload.model_dump())
    except Exception as exc:
        _raise_from_exception(exc)


@router.get("/locations/{location_id}")
async def get_location(request: Request, location_id: str):
    try:
        return _build_services(request)["locations"].get_by_id(location_id)
    except Exception as exc:
        _raise_from_exception(exc)


@router.patch("/locations/{location_id}")
async def update_location(request: Request, location_id: str, payload: UpdateLocationPayload):
    try:
        return _build_services(request)["locations"].update(location_id, payload.model_dump(exclude_unset=True))
    except Exception as exc:
        _raise_from_exception(exc)


@router.get("/locations")
async def list_locations(
    request: Request,
    q: Optional[str] = Query(default=None),
    city: Optional[str] = Query(default=None),
):
    try:
        return _build_services(request)["locations"].list(query=q, city=city)
    except Exception as exc:
        _raise_from_exception(exc)


@router.post("/assets")
async def create_asset(request: Request, payload: CreateAssetPayload):
    try:
        return _build_services(request)["assets"].create(payload.model_dump())
    except Exception as exc:
        _raise_from_exception(exc)


@router.get("/assets/{asset_id}")
async def get_asset(request: Request, asset_id: str):
    try:
        return _build_services(request)["assets"].get_by_id(asset_id)
    except Exception as exc:
        _raise_from_exception(exc)


@router.patch("/assets/{asset_id}")
async def update_asset(request: Request, asset_id: str, payload: UpdateAssetPayload):
    try:
        return _build_services(request)["assets"].update(asset_id, payload.model_dump(exclude_unset=True))
    except Exception as exc:
        _raise_from_exception(exc)


@router.delete("/assets/{asset_id}")
async def delete_asset(request: Request, asset_id: str):
    try:
        return _build_services(request)["assets"].soft_delete(asset_id)
    except Exception as exc:
        _raise_from_exception(exc)


@router.get("/projects/{project_id}/assets")
async def list_project_assets(
    request: Request,
    project_id: str,
    active_only: bool = Query(default=True),
):
    try:
        return _build_services(request)["assets"].list_by_project(project_id, active_only=active_only)
    except Exception as exc:
        _raise_from_exception(exc)


@router.get("/sectors/{sector_id}/assets")
async def list_sector_assets(
    request: Request,
    sector_id: str,
    active_only: bool = Query(default=True),
):
    try:
        return _build_services(request)["assets"].list_by_sector(sector_id, active_only=active_only)
    except Exception as exc:
        _raise_from_exception(exc)


@router.get("/assets/{asset_id}/children")
async def list_asset_children(request: Request, asset_id: str):
    try:
        return _build_services(request)["assets"].list_children(asset_id)
    except Exception as exc:
        _raise_from_exception(exc)


@router.get("/assets/{asset_id}/tree")
async def get_asset_tree(request: Request, asset_id: str):
    try:
        return _build_services(request)["assets"].get_asset_tree(asset_id)
    except Exception as exc:
        _raise_from_exception(exc)


@router.get("/assets/{asset_id}/devices")
async def get_node_devices(request: Request, asset_id: str):
    try:
        return _build_services(request)["assets"].get_node_devices(asset_id)
    except Exception as exc:
        _raise_from_exception(exc)


@router.get("/projects/{project_id}/assets/offline")
async def get_offline_assets(
    request: Request,
    project_id: str,
    offline_minutes: int = Query(default=15, ge=1, le=1440),
):
    try:
        return _build_services(request)["assets"].get_offline_assets(project_id, offline_minutes=offline_minutes)
    except Exception as exc:
        _raise_from_exception(exc)


@router.post("/projects/{project_id}/provisioning/node-bundle")
async def provision_node_bundle(request: Request, project_id: str, payload: ProvisionNodeBundlePayload):
    try:
        return _build_services(request)["assets"].provision_node_bundle(project_id, payload.model_dump())
    except Exception as exc:
        _raise_from_exception(exc)


@router.post("/topology-links")
async def create_topology_link(request: Request, payload: CreateTopologyLinkPayload):
    try:
        return _build_services(request)["topology"].create(payload.model_dump())
    except Exception as exc:
        _raise_from_exception(exc)


@router.get("/topology-links/{link_id}")
async def get_topology_link(request: Request, link_id: str):
    try:
        return _build_services(request)["topology"].get_by_id(link_id)
    except Exception as exc:
        _raise_from_exception(exc)


@router.patch("/topology-links/{link_id}")
async def update_topology_link(request: Request, link_id: str, payload: UpdateTopologyLinkPayload):
    try:
        return _build_services(request)["topology"].update(link_id, payload.model_dump(exclude_unset=True))
    except Exception as exc:
        _raise_from_exception(exc)


@router.delete("/topology-links/{link_id}")
async def delete_topology_link(request: Request, link_id: str):
    try:
        _build_services(request)["topology"].delete(link_id)
        return {"deleted": True, "id": link_id}
    except Exception as exc:
        _raise_from_exception(exc)


@router.get("/projects/{project_id}/topology")
async def get_project_topology(request: Request, project_id: str):
    try:
        return _build_services(request)["topology"].get_project_topology(project_id)
    except Exception as exc:
        _raise_from_exception(exc)
