"""Closed-loop experimental comparison using a minimal first-order plant."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

from ..evaluators.proportional import ProportionalEvaluator
from ..evaluators.threshold import ThresholdEvaluator
from ..examples.threshold_vs_proportional_demo import (
    build_comparison_variable,
    build_proportional_parameters,
    build_threshold_parameters,
)
from ..simulation.first_order import (
    ClosedLoopSimulationConfig,
    FirstOrderPlantConfig,
    simulate_closed_loop_strategy,
)
from ..simulation.metrics import (
    build_comparison_overview,
    calculate_summary_metrics,
)


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Unsupported value for JSON serialization: {type(value)!r}")


def build_closed_loop_plant_config() -> FirstOrderPlantConfig:
    return FirstOrderPlantConfig(
        baseline_level=45.0,
        control_gain=1.6,
        response_rate=0.35,
        min_value=0.0,
        max_value=100.0,
    )


def build_closed_loop_simulation_config() -> ClosedLoopSimulationConfig:
    disturbance_sequence = [0.0, 0.0, -1.5, -1.5, 0.0, 2.0, 2.0, 0.0, -2.5, 0.0]
    return ClosedLoopSimulationConfig(
        initial_value=35.0,
        horizon=len(disturbance_sequence),
        disturbance_sequence=disturbance_sequence,
    )


def run_closed_loop_threshold_vs_proportional_comparison() -> dict:
    variable = build_comparison_variable()
    plant_config = build_closed_loop_plant_config()
    simulation_config = build_closed_loop_simulation_config()
    setpoint_value = 55.0

    threshold_run = simulate_closed_loop_strategy(
        strategy_name="threshold",
        evaluator=ThresholdEvaluator(),
        variable=variable,
        parameters=build_threshold_parameters(),
        setpoint_value=setpoint_value,
        plant_config=plant_config,
        simulation_config=simulation_config,
    )
    proportional_run = simulate_closed_loop_strategy(
        strategy_name="proportional",
        evaluator=ProportionalEvaluator(),
        variable=variable,
        parameters=build_proportional_parameters(),
        setpoint_value=setpoint_value,
        plant_config=plant_config,
        simulation_config=simulation_config,
    )

    summary_metrics = {
        "threshold": calculate_summary_metrics("threshold", threshold_run["steps"]),
        "proportional": calculate_summary_metrics("proportional", proportional_run["steps"]),
    }

    observed_differences = [
        "closed-loop permite que el error evolucione segun la accion aplicada",
        "threshold corrige con escalones fijos y tiende a sobrecorregir cerca del setpoint",
        "proportional reduce esfuerzo y suaviza la aproximacion al objetivo",
        "las metricas de error ya pueden divergir entre estrategias en este escenario",
    ]

    return {
        "scenario": {
            "name": "tank-level-closed-loop-comparison",
            "variable_id": variable.variable_id,
            "setpoint": setpoint_value,
            "plant_config": asdict(plant_config),
            "simulation_config": asdict(simulation_config),
            "threshold_parameters": asdict(build_threshold_parameters()),
            "proportional_parameters": asdict(build_proportional_parameters()),
        },
        "trajectories": {
            "threshold": {
                "state_series": threshold_run["state_series"],
                "steps": threshold_run["steps"],
            },
            "proportional": {
                "state_series": proportional_run["state_series"],
                "steps": proportional_run["steps"],
            },
        },
        "summary_metrics": summary_metrics,
        "comparison_overview": build_comparison_overview(summary_metrics),
        "observed_differences": observed_differences,
    }


def main() -> None:
    print(
        json.dumps(
            run_closed_loop_threshold_vs_proportional_comparison(),
            indent=2,
            default=_json_default,
        )
    )


if __name__ == "__main__":
    main()
