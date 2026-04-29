"""Input and output contracts for monovariable control evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from ..models.control_models import (
    ActionRecommendation,
    ControlParameterSet,
    ControlledVariableDefinition,
    MeasurementState,
    SetpointReference,
    TraceEntry,
)


@dataclass(frozen=True)
class ControlEvaluationRequest:
    """Immutable input contract for a single control evaluation."""

    variable: ControlledVariableDefinition
    measurement: MeasurementState
    setpoint: SetpointReference
    parameters: ControlParameterSet
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ControlEvaluationResponse:
    """Output contract containing recommendation and trace data."""

    variable_id: str
    evaluator_name: str
    error: float
    raw_control_signal: float
    applied_control_signal: float
    recommendation: ActionRecommendation
    trace: List[TraceEntry]
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
