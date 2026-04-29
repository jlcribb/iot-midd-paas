"""API schemas for the Digital Twin Engine."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class CommandRequest(BaseModel):
    command: str = Field(..., description="Command name")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Command payload")


class CommandResponse(BaseModel):
    entity_id: str
    command: str
    accepted: bool
    state_machine: str


class TwinSummaryResponse(BaseModel):
    id: str
    plant_id: str
    type: str
    state_machine: str
    state: Dict[str, Any]


class TwinDetailResponse(BaseModel):
    id: str
    plant_id: str
    type: str
    state_machine: str
    config: Dict[str, Any]
    state: Dict[str, Any]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    last_updated: str


class EventResponse(BaseModel):
    timestamp: str
    plant_id: Optional[str] = None
    entity_id: str
    type: str
    payload: Dict[str, Any]


class PlantResponse(BaseModel):
    plant_id: str
    twin_count: int
    connection_count: int
    twins: list[str]
