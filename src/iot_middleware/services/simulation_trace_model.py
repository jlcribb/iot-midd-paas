"""Canonical, immutable process evidence for one completed simulation run.

This is deliberately experiment-scoped evidence, not operational telemetry.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

TRACE_SCHEMA_VERSION = 1
TIME_REPRESENTATION = "elapsed_seconds_from_first_virtual_timestamp:v1"


@dataclass(frozen=True)
class SimulationTracePoint:
    sequence_number: int
    simulation_time_seconds: float
    process_value: float
    setpoint: float
    control_output: float
    actuator_state: str
    constraint_state: str | None

    def semantic_dict(self) -> dict[str, Any]:
        return {"sequence_number": self.sequence_number, "simulation_time_seconds": self.simulation_time_seconds,
                "process_value": self.process_value, "setpoint": self.setpoint, "control_output": self.control_output,
                "actuator_state": self.actuator_state, "constraint_state": self.constraint_state}


@dataclass(frozen=True)
class SimulationTraceEvidence:
    trace_schema_version: int
    time_representation: str
    trace_hash: str
    point_count: int
    simulation_duration_seconds: float
    points: list[SimulationTracePoint]


def canonical_trace_evidence(*, experiment_fingerprint: str, outputs: Iterable[dict[str, Any]]) -> SimulationTraceEvidence:
    """Validate raw replay outputs and create a content-addressed trace.

    No interpolation, filling, or mutation occurs here.  Invalid/incomplete
    evidence aborts materialization rather than manufacturing a KPI input.
    """
    ordered = list(outputs)
    if not ordered:
        raise ValueError("simulation trace requires at least one point")
    timestamps = [_timestamp(output.get("virtual_timestamp")) for output in ordered]
    first = timestamps[0]
    points: list[SimulationTracePoint] = []
    previous_time = -1.0
    for expected, (output, timestamp) in enumerate(zip(ordered, timestamps), start=1):
        sequence = _positive_integer(output.get("sequence"), "sequence")
        if sequence != expected:
            raise ValueError("simulation trace sequence must be contiguous and deterministic")
        simulation_time = _finite((timestamp - first).total_seconds(), "simulation_time_seconds")
        if simulation_time < previous_time:
            raise ValueError("simulation trace time must be monotonic")
        previous_time = simulation_time
        points.append(SimulationTracePoint(
            sequence_number=sequence, simulation_time_seconds=simulation_time,
            process_value=_finite(output.get("process_value"), "process_value"),
            setpoint=_finite(output.get("setpoint"), "setpoint"),
            control_output=_finite(output.get("control_output"), "control_output"),
            actuator_state=_nonempty(output.get("actuator_state"), "actuator_state"),
            constraint_state=_optional_string(output.get("constraint_state")),
        ))
    representation = {"trace_schema_version": TRACE_SCHEMA_VERSION, "experiment_fingerprint": experiment_fingerprint,
                      "time_representation": TIME_REPRESENTATION, "points": [point.semantic_dict() for point in points]}
    trace_hash = hashlib.sha256(_canonical_json(representation).encode("utf-8")).hexdigest()
    return SimulationTraceEvidence(TRACE_SCHEMA_VERSION, TIME_REPRESENTATION, trace_hash, len(points), points[-1].simulation_time_seconds, points)


def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str): raise ValueError("simulation trace virtual timestamp is required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None: raise ValueError("simulation trace virtual timestamp must include timezone")
    return parsed
def _finite(value: Any, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise ValueError(f"simulation trace {name} must be finite")
    return float(value)
def _positive_integer(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1: raise ValueError(f"simulation trace {name} must be positive")
    return value
def _nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip(): raise ValueError(f"simulation trace {name} is required")
    return value
def _optional_string(value: Any) -> str | None:
    if value is None: return None
    if not isinstance(value, str): raise ValueError("simulation trace constraint_state must be a string or null")
    return value
def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
