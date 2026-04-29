"""Experimental comparison between threshold and proportional control."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

from ..contracts.control_contracts import ControlEvaluationRequest
from ..evaluators.proportional import ProportionalEvaluator
from ..evaluators.threshold import ThresholdEvaluator
from ..models.control_models import (
    ControlledVariableDefinition,
    ControlParameters,
    MeasurementState,
    SetpointReference,
    ThresholdControlParameters,
)
from ..simulation.metrics import (
    build_comparison_overview,
    calculate_summary_metrics,
)


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Unsupported value for JSON serialization: {type(value)!r}")


def build_comparison_variable() -> ControlledVariableDefinition:
    return ControlledVariableDefinition(
        variable_id="tank-level-compare-01",
        name="tank_level",
        unit="percent",
        actuator_name="inlet_valve",
        increase_action_label="open_more",
        decrease_action_label="close_some",
        hold_action_label="hold_position",
        description="Escenario comparativo de nivel de tanque",
    )


def build_measurement_sequence() -> list[float]:
    return [40.0, 46.0, 52.0, 54.0, 55.0, 56.0, 60.0]


def build_threshold_parameters() -> ThresholdControlParameters:
    return ThresholdControlParameters(
        tolerance=2.0,
        increase_step=8.0,
        decrease_step=8.0,
        hold_signal=0.0,
    )


def build_proportional_parameters() -> ControlParameters:
    return ControlParameters(
        gain=1.0,
        deadband=1.5,
        min_action=0.0,
        max_action=12.0,
    )


def build_strategy_step(
    measurement_value: float,
    setpoint_value: float,
    response,
) -> dict:
    """Normalize one strategy result for side-by-side comparison."""
    return {
        "measurement": measurement_value,
        "setpoint": setpoint_value,
        "error": response.error,
        "distance_to_setpoint": abs(response.error),
        "action_kind": response.recommendation.kind.value,
        "action_label": response.recommendation.action_label,
        "applied_signal": response.applied_control_signal,
        "trace": [asdict(entry) for entry in response.trace],
        "response": asdict(response),
    }


def summarize_strategy(strategy_name: str, results: list[dict]) -> dict:
    """Backward-compatible wrapper kept for the comparison demo output."""
    return calculate_summary_metrics(strategy_name, results)


def run_threshold_vs_proportional_comparison() -> dict:
    variable = build_comparison_variable()
    setpoint = SetpointReference(
        value=55.0,
        metadata={"scenario": "tank-level-comparison"},
    )
    threshold_evaluator = ThresholdEvaluator()
    proportional_evaluator = ProportionalEvaluator()
    threshold_results = []
    proportional_results = []
    comparison_steps = []

    for index, measurement_value in enumerate(build_measurement_sequence(), start=1):
        measurement = MeasurementState(
            value=measurement_value,
            source="synthetic_sequence",
            metadata={"sequence_index": index},
        )
        threshold_request = ControlEvaluationRequest(
            variable=variable,
            measurement=measurement,
            setpoint=setpoint,
            parameters=build_threshold_parameters(),
            context={"strategy": "threshold", "sequence_index": index},
        )
        proportional_request = ControlEvaluationRequest(
            variable=variable,
            measurement=measurement,
            setpoint=setpoint,
            parameters=build_proportional_parameters(),
            context={"strategy": "proportional", "sequence_index": index},
        )

        threshold_response = threshold_evaluator.evaluate(threshold_request)
        proportional_response = proportional_evaluator.evaluate(proportional_request)

        threshold_step = build_strategy_step(
            measurement_value=measurement_value,
            setpoint_value=setpoint.value,
            response=threshold_response,
        )
        proportional_step = build_strategy_step(
            measurement_value=measurement_value,
            setpoint_value=setpoint.value,
            response=proportional_response,
        )
        threshold_results.append(threshold_step)
        proportional_results.append(proportional_step)
        comparison_steps.append(
            {
                "measurement": measurement_value,
                "setpoint": setpoint.value,
                "threshold": threshold_step,
                "proportional": proportional_step,
            }
        )

    threshold_summary = summarize_strategy("threshold", threshold_results)
    proportional_summary = summarize_strategy("proportional", proportional_results)
    summary_metrics = {
        "threshold": threshold_summary,
        "proportional": proportional_summary,
    }
    observed_differences = [
        "threshold aplica magnitudes fijas y concentra mayor esfuerzo total",
        "proportional modula la magnitud de la recomendacion segun el error",
        "threshold mantiene una banda de hold mas abrupta",
        "proportional entrega una respuesta mas gradual cerca del setpoint",
    ]

    return {
        "scenario": {
            "name": "tank-level-comparison",
            "variable_id": variable.variable_id,
            "measurements": build_measurement_sequence(),
            "setpoint": setpoint.value,
            "threshold_parameters": asdict(build_threshold_parameters()),
            "proportional_parameters": asdict(build_proportional_parameters()),
        },
        "comparison_steps": comparison_steps,
        "summary_metrics": summary_metrics,
        "comparison_overview": build_comparison_overview(summary_metrics),
        "observed_differences": observed_differences,
    }


def main() -> None:
    print(
        json.dumps(
            run_threshold_vs_proportional_comparison(),
            indent=2,
            default=_json_default,
        )
    )


if __name__ == "__main__":
    main()
