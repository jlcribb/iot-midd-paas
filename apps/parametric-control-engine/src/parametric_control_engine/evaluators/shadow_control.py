"""Non-actuating adapter around the canonical parametric evaluators."""

from __future__ import annotations

from typing import Any

from ..contracts.control_contracts import ControlEvaluationRequest
from ..models.control_models import (
    ControlParameters,
    ControlledVariableDefinition,
    MeasurementState,
    SetpointReference,
    ThresholdControlParameters,
)
from .proportional import ProportionalEvaluator
from .threshold import ThresholdEvaluator


class ShadowControlEvaluationError(ValueError):
    """A factual, non-actuating evaluation failure."""


def evaluate_shadow_control(*, strategy_type: str, configuration: dict[str, Any], input_snapshot: dict[str, Any], required_inputs: list[str], limits: dict[str, Any]) -> dict[str, Any]:
    for name in required_inputs:
        if not isinstance(input_snapshot.get(name), (int, float)):
            raise ShadowControlEvaluationError("INPUT_UNAVAILABLE")
    if not required_inputs:
        raise ShadowControlEvaluationError("INPUT_UNAVAILABLE")
    minimum, maximum = limits.get("min_output"), limits.get("max_output")
    if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)) or minimum > maximum:
        raise ShadowControlEvaluationError("OUTPUT_LIMIT_VIOLATION")
    parameters = configuration.get("parameters") if isinstance(configuration, dict) else None
    if not isinstance(parameters, dict):
        raise ShadowControlEvaluationError("POLICY_EVALUATION_ERROR")
    variable_name = required_inputs[0]
    variable = ControlledVariableDefinition(
        variable_id=variable_name, name=variable_name, unit=str(parameters.get("variable_unit") or "units"),
        actuator_name=str(parameters.get("actuator_name") or "shadow_output"),
        controller_direction=float(parameters.get("controller_direction") or 1.0),
    )
    try:
        if strategy_type == "proportional":
            evaluator, control_parameters = ProportionalEvaluator(), ControlParameters(
                gain=float(parameters["gain"]), deadband=float(parameters.get("deadband", 0.0)),
                min_action=float(parameters.get("min_action", 0.0)),
                max_action=float(parameters["max_action"]) if parameters.get("max_action") is not None else None,
            )
        elif strategy_type == "threshold":
            evaluator, control_parameters = ThresholdEvaluator(), ThresholdControlParameters(
                tolerance=float(parameters["tolerance"]), increase_step=float(parameters["increase_step"]),
                decrease_step=float(parameters["decrease_step"]), hold_signal=float(parameters.get("hold_signal", 0.0)),
            )
        else:
            raise ShadowControlEvaluationError("POLICY_EVALUATOR_UNAVAILABLE")
        response = evaluator.evaluate(ControlEvaluationRequest(
            variable=variable, measurement=MeasurementState(value=float(input_snapshot[variable_name]), source="governed-shadow"),
            setpoint=SetpointReference(value=float(parameters["setpoint_value"])), parameters=control_parameters,
            context={"execution_mode": "SHADOW", "physical_effects": False},
        ))
    except ShadowControlEvaluationError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise ShadowControlEvaluationError("POLICY_EVALUATION_ERROR") from exc
    raw = response.raw_control_signal
    bounded = max(float(minimum), min(float(maximum), response.applied_control_signal))
    return {
        "raw_output": {"value": raw},
        "bounded_output": {"value": bounded},
        "constraint_results": {"saturated": bounded != raw, "policy_constraint_applied": response.applied_control_signal != raw,
                               "limits": {"min_output": minimum, "max_output": maximum}, "physical_effects": False},
        "evaluator": {"name": response.evaluator_name, "trace": [{"step": item.step, "data": item.data} for item in response.trace]},
    }
