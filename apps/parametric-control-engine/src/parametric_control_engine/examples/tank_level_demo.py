"""Runnable demo for the first monovariable parametric control evaluator."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

from ..contracts.control_contracts import ControlEvaluationRequest
from ..evaluators.proportional import ProportionalEvaluator
from ..models.control_models import (
    ControlledVariableDefinition,
    ControlParameters,
    MeasurementState,
    SetpointReference,
)


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Unsupported value for JSON serialization: {type(value)!r}")


def build_demo_request() -> ControlEvaluationRequest:
    """Create a simple tank-level control scenario for demonstrations."""
    return ControlEvaluationRequest(
        variable=ControlledVariableDefinition(
            variable_id="tank-level-01",
            name="tank_level",
            unit="percent",
            actuator_name="inlet_valve",
            increase_action_label="open_more",
            decrease_action_label="close_some",
            hold_action_label="hold_position",
            description="Nivel de tanque de proceso",
        ),
        measurement=MeasurementState(
            value=42.0,
            source="simulated_sensor",
            metadata={"asset_id": "tank-A"},
        ),
        setpoint=SetpointReference(
            value=55.0,
            metadata={"recipe": "batch-startup"},
        ),
        parameters=ControlParameters(
            gain=1.5,
            deadband=0.5,
            min_action=2.0,
            max_action=15.0,
        ),
        context={
            "project_id": "demo-project",
            "sector_id": "mixing-line",
            "evaluation_mode": "manual_demo",
        },
    )


def main() -> None:
    evaluator = ProportionalEvaluator()
    result = evaluator.evaluate(build_demo_request())
    print(json.dumps(asdict(result), indent=2, default=_json_default))


if __name__ == "__main__":
    main()
