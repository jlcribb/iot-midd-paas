"""FastAPI routes for digital twin control and observability."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from ..core.engine import DigitalTwinEngine
from .schemas import (
    CommandRequest,
    CommandResponse,
    EventResponse,
    PlantResponse,
    TwinDetailResponse,
    TwinSummaryResponse,
)


router = APIRouter()


def _get_engine(request: Request) -> DigitalTwinEngine:
    engine = getattr(request.app.state, "dte_engine", None)
    if engine is None:
        raise HTTPException(status_code=500, detail="Digital Twin Engine is not initialized")
    return engine


@router.get("/twins", response_model=list[TwinSummaryResponse])
async def get_twins(request: Request) -> list[TwinSummaryResponse]:
    engine = _get_engine(request)
    twins = []
    for twin in engine.list_twins():
        twins.append(
            TwinSummaryResponse(
                id=twin["id"],
                plant_id=twin["plant_id"],
                type=twin["type"],
                state_machine=twin["state_machine"],
                state=twin["state"],
            )
        )
    return twins


@router.get("/twins/{entity_id}", response_model=TwinDetailResponse)
async def get_twin(request: Request, entity_id: str) -> TwinDetailResponse:
    engine = _get_engine(request)
    twin = engine.get_twin(entity_id)
    if twin is None:
        raise HTTPException(status_code=404, detail=f"Twin '{entity_id}' not found")
    payload = twin.to_dict()
    return TwinDetailResponse(
        id=payload["id"],
        plant_id=payload["plant_id"],
        type=payload["type"],
        state_machine=payload["state_machine"],
        config=payload["config"],
        state=payload["state"],
        inputs=payload["inputs"],
        outputs=payload["outputs"],
        last_updated=payload["last_updated"],
    )


@router.post("/twins/{entity_id}/command", response_model=CommandResponse)
async def command_twin(request: Request, entity_id: str, body: CommandRequest) -> CommandResponse:
    engine = _get_engine(request)
    try:
        result = await engine.dispatch_command(entity_id, body.command, body.payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CommandResponse(**result)


@router.get("/events", response_model=list[EventResponse])
async def get_events(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    entity_id: Optional[str] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
) -> list[EventResponse]:
    engine = _get_engine(request)
    if engine.store is None:
        return []
    rows = engine.store.get_events(limit=limit, entity_id=entity_id, event_type=event_type)
    return [EventResponse(**row) for row in rows]


@router.get("/plants", response_model=list[PlantResponse])
async def get_plants(request: Request) -> list[PlantResponse]:
    engine = _get_engine(request)
    return [PlantResponse(**row) for row in engine.list_plants()]


@router.post("/engine/speed")
async def set_simulation_speed(request: Request, factor: float = Query(..., gt=0)) -> dict[str, float]:
    engine = _get_engine(request)
    engine.set_simulation_speed(factor)
    return {"simulation_speed": engine.simulation_speed}


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    _ = _get_engine(request)
    return {"status": "ok"}
