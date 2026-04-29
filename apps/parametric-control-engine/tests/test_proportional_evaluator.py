import pytest

from parametric_control_engine.contracts.control_contracts import ControlEvaluationRequest
from parametric_control_engine.evaluators.proportional import ProportionalEvaluator
from parametric_control_engine.models.control_models import (
    ActionKind,
    ControlledVariableDefinition,
    ControlParameters,
    MeasurementState,
    SetpointReference,
)


def build_request(**overrides) -> ControlEvaluationRequest:
    variable = overrides.pop(
        "variable",
        ControlledVariableDefinition(
            variable_id="loop-01",
            name="tank_level",
            unit="percent",
            actuator_name="inlet_valve",
            increase_action_label="open_more",
            decrease_action_label="close_some",
            hold_action_label="hold_position",
        ),
    )
    measurement = overrides.pop("measurement", MeasurementState(value=42.0))
    setpoint = overrides.pop("setpoint", SetpointReference(value=50.0))
    parameters = overrides.pop(
        "parameters",
        ControlParameters(gain=1.5, deadband=0.5, min_action=0.0, max_action=25.0),
    )
    context = overrides.pop("context", {"test_case": "default"})

    if overrides:
        unexpected = ", ".join(sorted(overrides))
        raise ValueError(f"Unexpected override keys: {unexpected}")

    return ControlEvaluationRequest(
        variable=variable,
        measurement=measurement,
        setpoint=setpoint,
        parameters=parameters,
        context=context,
    )


def test_proportional_evaluator_returns_increase_action_with_trace():
    evaluator = ProportionalEvaluator()

    result = evaluator.evaluate(build_request())

    assert result.error == pytest.approx(8.0)
    assert result.raw_control_signal == pytest.approx(12.0)
    assert result.applied_control_signal == pytest.approx(12.0)
    assert result.recommendation.kind == ActionKind.INCREASE
    assert result.recommendation.action_label == "open_more"
    assert result.trace[0].step == "trace_initialized"
    assert [entry.step for entry in result.trace][-1] == "recommendation_built"


def test_proportional_evaluator_holds_inside_deadband():
    evaluator = ProportionalEvaluator()

    result = evaluator.evaluate(
        build_request(
            measurement=MeasurementState(value=49.8),
            setpoint=SetpointReference(value=50.0),
        )
    )

    assert result.error == pytest.approx(0.2)
    assert result.applied_control_signal == pytest.approx(0.0)
    assert result.recommendation.kind == ActionKind.HOLD
    assert result.recommendation.action_label == "hold_position"
    assert result.trace[4].data["constraint_reason"] == "deadband_hold"


def test_proportional_evaluator_applies_minimum_action_floor():
    evaluator = ProportionalEvaluator()

    result = evaluator.evaluate(
        build_request(
            measurement=MeasurementState(value=49.7),
            setpoint=SetpointReference(value=50.0),
            parameters=ControlParameters(
                gain=1.0,
                deadband=0.1,
                min_action=2.0,
                max_action=10.0,
            ),
        )
    )

    assert result.error == pytest.approx(0.3)
    assert result.raw_control_signal == pytest.approx(result.error)
    assert result.applied_control_signal == pytest.approx(2.0)
    assert result.recommendation.kind == ActionKind.INCREASE
    assert result.trace[4].data["constraint_reason"] == "min_action_floor"


def test_proportional_evaluator_clamps_maximum_action():
    evaluator = ProportionalEvaluator()

    result = evaluator.evaluate(
        build_request(
            measurement=MeasurementState(value=10.0),
            setpoint=SetpointReference(value=30.0),
            parameters=ControlParameters(
                gain=2.0,
                deadband=0.0,
                min_action=0.0,
                max_action=25.0,
            ),
        )
    )

    assert result.error == pytest.approx(20.0)
    assert result.raw_control_signal == pytest.approx(40.0)
    assert result.applied_control_signal == pytest.approx(25.0)
    assert result.trace[4].data["constraint_reason"] == "max_action_clamp"


def test_proportional_evaluator_supports_reverse_controller_direction():
    evaluator = ProportionalEvaluator()

    result = evaluator.evaluate(
        build_request(
            variable=ControlledVariableDefinition(
                variable_id="loop-02",
                name="cooling_temperature",
                unit="celsius",
                actuator_name="cooling_valve",
                increase_action_label="open_more",
                decrease_action_label="close_some",
                hold_action_label="hold_position",
                controller_direction=-1.0,
            ),
            measurement=MeasurementState(value=60.0),
            setpoint=SetpointReference(value=50.0),
            parameters=ControlParameters(
                gain=1.0,
                deadband=0.0,
                min_action=0.0,
                max_action=20.0,
            ),
        )
    )

    assert result.error == pytest.approx(-10.0)
    assert result.raw_control_signal == pytest.approx(-10.0)
    assert result.applied_control_signal == pytest.approx(10.0)
    assert result.recommendation.kind == ActionKind.INCREASE
