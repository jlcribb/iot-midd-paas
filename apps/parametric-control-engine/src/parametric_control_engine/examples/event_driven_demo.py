"""Event-driven demo for the parametric control engine MVP."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

from ..adapters.event_adapter import EventDrivenRecommendationAdapter
from ..contracts.event_adapter_contracts import (
    MonovariableControlBinding,
    TelemetryStateEvent,
)
from ..models.control_models import (
    ControlledVariableDefinition,
    ControlParameters,
    SetpointReference,
)


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Unsupported value for JSON serialization: {type(value)!r}")


def build_demo_binding() -> MonovariableControlBinding:
    return MonovariableControlBinding(
        variable=ControlledVariableDefinition(
            variable_id="tank-level-01",
            name="tank_level",
            unit="percent",
            actuator_name="inlet_valve",
            increase_action_label="open_more",
            decrease_action_label="close_some",
            hold_action_label="hold_position",
        ),
        setpoint=SetpointReference(value=55.0, metadata={"recipe": "batch-startup"}),
        parameters=ControlParameters(gain=1.2, deadband=0.5, min_action=2.0, max_action=12.0),
        recommendation_channel="runtime.control.recommendations",
        context={"project_id": "demo-project", "sector_id": "mixing-line"},
    )


def build_demo_event() -> TelemetryStateEvent:
    return TelemetryStateEvent(
        event_id="evt-1001",
        variable_id="tank-level-01",
        value=43.5,
        source="mqtt://plant/tank-A/level",
        quality="validated",
        metadata={"asset_id": "tank-A", "topic": "plant/tank-A/level"},
        context={"ingestion_path": "mqtt", "correlation_id": "corr-42"},
    )


def main() -> None:
    adapter = EventDrivenRecommendationAdapter(build_demo_binding())
    result = adapter.evaluate_event(build_demo_event())
    print(json.dumps(asdict(result), indent=2, default=_json_default))


if __name__ == "__main__":
    main()
