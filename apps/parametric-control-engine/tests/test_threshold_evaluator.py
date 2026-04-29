import pytest

from parametric_control_engine.contracts.control_contracts import ControlEvaluationRequest
from parametric_control_engine.evaluators.threshold import ThresholdEvaluator
from parametric_control_engine.models.control_models import (
    ActionKind,
    ControlledVariableDefinition,
    MeasurementState,
    SetpointReference,
    ThresholdControlParameters,
)


def build_request(**overrides) -> ControlEvaluationRequest:
    variable = overrides.pop(
        "variable",
        ControlledVariableDefinition(
            variable_id="tank-threshold-01",
            name="tank_level",
            unit="percent",
            actuator_name="inlet_valve",
            increase_action_label="open_more",
            decrease_action_label="close_some",
            hold_action_label="hold_position",
        ),
    )
    measurement = overrides.pop("measurement", MeasurementState(value=46.0))
    setpoint = overrides.pop("setpoint", SetpointReference(value=55.0))
    parameters = overrides.pop(
        "parameters",
        ThresholdControlParameters(
            tolerance=2.0,
            increase_step=8.0,
            decrease_step=8.0,
            hold_signal=0.0,
        ),
    )
    context = overrides.pop("context", {"test_case": "threshold"})

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


def test_threshold_evaluator_increases_below_band():
    evaluator = ThresholdEvaluator()

    result = evaluator.evaluate(build_request())

    assert result.error == pytest.approx(9.0)
    assert result.applied_control_signal == pytest.approx(8.0)
    assert result.recommendation.kind == ActionKind.INCREASE
    assert result.trace[3].data["decision_reason"] == "below_lower_band"


def test_threshold_evaluator_holds_inside_band():
    evaluator = ThresholdEvaluator()

    result = evaluator.evaluate(build_request(measurement=MeasurementState(value=56.0)))

    assert result.error == pytest.approx(-1.0)
    assert result.applied_control_signal == pytest.approx(0.0)
    assert result.recommendation.kind == ActionKind.HOLD
    assert result.trace[3].data["decision_reason"] == "inside_threshold_band"


def test_threshold_evaluator_decreases_above_band():
    evaluator = ThresholdEvaluator()

    result = evaluator.evaluate(build_request(measurement=MeasurementState(value=60.0)))

    assert result.error == pytest.approx(-5.0)
    assert result.applied_control_signal == pytest.approx(-8.0)
    assert result.recommendation.kind == ActionKind.DECREASE
    assert result.trace[3].data["decision_reason"] == "above_upper_band"
