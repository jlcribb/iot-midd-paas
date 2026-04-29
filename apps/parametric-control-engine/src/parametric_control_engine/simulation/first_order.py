"""Minimal first-order closed-loop plant simulation for reproducible experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List

from ..contracts.control_contracts import ControlEvaluationRequest
from ..models.control_models import MeasurementState, SetpointReference


@dataclass(frozen=True)
class FirstOrderPlantConfig:
    """Transparent first-order plant with a control-shaped desired level."""

    baseline_level: float
    control_gain: float
    response_rate: float
    min_value: float = 0.0
    max_value: float = 100.0


@dataclass(frozen=True)
class ClosedLoopSimulationConfig:
    """Configuration for a closed-loop synthetic scenario."""

    initial_value: float
    horizon: int
    disturbance_sequence: List[float]


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def simulate_first_order_step(
    current_value: float,
    applied_signal: float,
    disturbance: float,
    plant_config: FirstOrderPlantConfig,
) -> Dict[str, float]:
    """Advance the first-order plant one step.

    The plant moves toward a desired level shaped by:
    - a baseline level,
    - the controller output,
    - an additive disturbance.
    """

    desired_level = (
        plant_config.baseline_level
        + plant_config.control_gain * applied_signal
        + disturbance
    )
    next_value = current_value + plant_config.response_rate * (
        desired_level - current_value
    )
    next_value = clamp(next_value, plant_config.min_value, plant_config.max_value)
    return {
        "desired_level": round(desired_level, 3),
        "next_value": round(next_value, 3),
    }


def simulate_closed_loop_strategy(
    *,
    strategy_name: str,
    evaluator,
    variable,
    parameters,
    setpoint_value: float,
    plant_config: FirstOrderPlantConfig,
    simulation_config: ClosedLoopSimulationConfig,
) -> Dict[str, Any]:
    """Run one evaluator against the same plant over a finite horizon."""

    if simulation_config.horizon != len(simulation_config.disturbance_sequence):
        raise ValueError(
            "Simulation horizon must match disturbance_sequence length"
        )

    steps: List[Dict[str, Any]] = []
    state_series = [round(simulation_config.initial_value, 3)]
    current_value = simulation_config.initial_value
    setpoint = SetpointReference(value=setpoint_value)

    for index, disturbance in enumerate(
        simulation_config.disturbance_sequence,
        start=1,
    ):
        measurement = MeasurementState(
            value=current_value,
            source="first_order_closed_loop",
            metadata={"step_index": index},
        )
        request = ControlEvaluationRequest(
            variable=variable,
            measurement=measurement,
            setpoint=setpoint,
            parameters=parameters,
            context={
                "strategy": strategy_name,
                "step_index": index,
                "disturbance": disturbance,
            },
        )
        response = evaluator.evaluate(request)
        plant_step = simulate_first_order_step(
            current_value=current_value,
            applied_signal=response.applied_control_signal,
            disturbance=disturbance,
            plant_config=plant_config,
        )
        next_value = plant_step["next_value"]
        state_series.append(next_value)
        step = {
            "step_index": index,
            "measurement": round(current_value, 3),
            "setpoint": setpoint_value,
            "error": round(response.error, 3),
            "distance_to_setpoint": round(abs(response.error), 3),
            "action_kind": response.recommendation.kind.value,
            "action_label": response.recommendation.action_label,
            "applied_signal": round(response.applied_control_signal, 3),
            "disturbance": disturbance,
            "desired_level": plant_step["desired_level"],
            "next_measurement": next_value,
            "trace": [asdict(entry) for entry in response.trace],
            "response": asdict(response),
        }
        steps.append(step)
        current_value = next_value

    return {
        "strategy": strategy_name,
        "initial_value": simulation_config.initial_value,
        "setpoint": setpoint_value,
        "state_series": state_series,
        "steps": steps,
    }
