from datetime import datetime, timezone

import pytest

from parametric_control_engine.adapters.event_adapter import EventDrivenRecommendationAdapter
from parametric_control_engine.contracts.event_adapter_contracts import (
    MonovariableControlBinding,
    TelemetryStateEvent,
)
from parametric_control_engine.models.control_models import (
    ActionKind,
    ControlledVariableDefinition,
    ControlParameters,
    SetpointReference,
)


def build_binding() -> MonovariableControlBinding:
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
        setpoint=SetpointReference(value=55.0),
        parameters=ControlParameters(gain=1.2, deadband=0.5, min_action=2.0, max_action=12.0),
        recommendation_channel="runtime.control.recommendations",
        context={"project_id": "demo-project"},
    )


def build_event(**overrides) -> TelemetryStateEvent:
    data = {
        "event_id": "evt-1001",
        "variable_id": "tank-level-01",
        "value": 43.5,
        "source": "mqtt://plant/tank-A/level",
        "event_kind": "telemetry.observed",
        "observed_at": datetime(2026, 4, 21, 12, 0, tzinfo=timezone.utc),
        "quality": "validated",
        "metadata": {"asset_id": "tank-A"},
        "context": {"correlation_id": "corr-42"},
    }
    data.update(overrides)
    return TelemetryStateEvent(**data)


def test_event_adapter_builds_control_request_from_event():
    adapter = EventDrivenRecommendationAdapter(build_binding())

    request, adapter_trace = adapter.to_evaluation_request(build_event())

    assert request.variable.variable_id == "tank-level-01"
    assert request.measurement.value == pytest.approx(43.5)
    assert request.measurement.source == "mqtt://plant/tank-A/level"
    assert request.setpoint.value == pytest.approx(55.0)
    assert request.parameters.gain == pytest.approx(1.2)
    assert request.context["project_id"] == "demo-project"
    assert request.context["correlation_id"] == "corr-42"
    assert request.context["event_id"] == "evt-1001"
    assert adapter_trace[0].step == "trace_initialized"
    assert adapter_trace[-1].step == "control_request_built"


def test_event_adapter_returns_runtime_ready_recommendation():
    adapter = EventDrivenRecommendationAdapter(build_binding())

    result = adapter.evaluate_event(build_event())

    assert result.event_id == "evt-1001"
    assert result.variable_id == "tank-level-01"
    assert result.recommendation_channel == "runtime.control.recommendations"
    assert result.evaluation.error == pytest.approx(11.5)
    assert result.evaluation.applied_control_signal == pytest.approx(12.0)
    assert result.evaluation.recommendation.kind == ActionKind.INCREASE
    assert result.runtime_payload["recommendation_kind"] == "increase"
    assert result.runtime_payload["binding_channel"] == "runtime.control.recommendations"
    assert result.runtime_payload["trace_steps"][-1] == "recommendation_built"
    assert result.adapter_trace[1].step == "event_received"


def test_event_adapter_rejects_mismatched_variable_binding():
    adapter = EventDrivenRecommendationAdapter(build_binding())

    with pytest.raises(ValueError, match="does not match"):
        adapter.to_evaluation_request(build_event(variable_id="other-variable"))
