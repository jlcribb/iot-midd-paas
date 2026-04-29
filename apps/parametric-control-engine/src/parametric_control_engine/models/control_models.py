"""Core domain models for the parametric control engine MVP."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Union


class ActionKind(str, Enum):
    """Normalized action categories for the first monovariable MVP."""

    INCREASE = "increase"
    DECREASE = "decrease"
    HOLD = "hold"


@dataclass(frozen=True)
class ControlledVariableDefinition:
    """Defines the process variable and the actuator vocabulary for recommendations."""

    variable_id: str
    name: str
    unit: str
    actuator_name: str
    increase_action_label: str = "increase"
    decrease_action_label: str = "decrease"
    hold_action_label: str = "hold"
    controller_direction: float = 1.0
    description: str = ""


@dataclass(frozen=True)
class MeasurementState:
    """Observed process value plus lightweight telemetry metadata."""

    value: float
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    quality: str = "raw"
    source: str = "manual"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SetpointReference:
    """Target reference for the controlled variable."""

    value: float
    label: str = "setpoint"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ControlParameters:
    """Configurable parameters for the monovariable proportional control policy."""

    gain: float
    deadband: float = 0.0
    min_action: float = 0.0
    max_action: Optional[float] = None


@dataclass(frozen=True)
class ThresholdControlParameters:
    """Fixed-step threshold controller parameters for comparison experiments."""

    tolerance: float
    increase_step: float
    decrease_step: float
    hold_signal: float = 0.0


ControlParameterSet = Union[ControlParameters, ThresholdControlParameters]


@dataclass(frozen=True)
class TraceEntry:
    """Single trace item emitted during control evaluation."""

    step: str
    data: Dict[str, Any]


@dataclass(frozen=True)
class ActionRecommendation:
    """Human and machine-readable control recommendation."""

    kind: ActionKind
    actuator_name: str
    action_label: str
    command_value: float
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)
