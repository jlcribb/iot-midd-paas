"""Contracts for the event-to-recommendation adapter layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from .control_contracts import ControlEvaluationResponse
from ..models.control_models import (
    ControlledVariableDefinition,
    ControlParameterSet,
    SetpointReference,
    TraceEntry,
)


@dataclass(frozen=True)
class TelemetryStateEvent:
    """Minimal external event contract accepted by the adapter layer."""

    event_id: str
    variable_id: str
    value: float
    source: str
    event_kind: str = "telemetry.observed"
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    quality: str = "raw"
    metadata: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MonovariableControlBinding:
    """Static binding between one incoming variable and one control policy."""

    variable: ControlledVariableDefinition
    setpoint: SetpointReference
    parameters: ControlParameterSet
    recommendation_channel: str = "control.recommendations"
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EventDrivenRecommendation:
    """Structured output prepared for future runtime integration."""

    event_id: str
    variable_id: str
    recommendation_channel: str
    evaluation: ControlEvaluationResponse
    adapter_trace: List[TraceEntry]
    runtime_payload: Dict[str, Any]
