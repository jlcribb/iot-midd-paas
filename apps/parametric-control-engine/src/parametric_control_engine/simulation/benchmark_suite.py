"""Small closed-loop benchmark suite for comparing control strategies."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List

from ..evaluators.proportional import ProportionalEvaluator
from ..evaluators.threshold import ThresholdEvaluator
from ..examples.threshold_vs_proportional_demo import (
    build_comparison_variable,
    build_proportional_parameters,
    build_threshold_parameters,
)
from .first_order import (
    ClosedLoopSimulationConfig,
    FirstOrderPlantConfig,
    simulate_closed_loop_strategy,
)
from .metrics import build_comparison_overview, calculate_summary_metrics


@dataclass(frozen=True)
class BenchmarkScenario:
    """A compact, explicit closed-loop benchmark scenario."""

    scenario_id: str
    label: str
    description: str
    setpoint_value: float
    plant_config: FirstOrderPlantConfig
    simulation_config: ClosedLoopSimulationConfig


def build_standard_benchmark_scenarios() -> List[BenchmarkScenario]:
    """Define the three standard synthetic scenarios for the MVP benchmark."""
    return [
        BenchmarkScenario(
            scenario_id="large_initial_error",
            label="Large Initial Error",
            description="Empieza muy por debajo del setpoint, sin perturbaciones.",
            setpoint_value=55.0,
            plant_config=FirstOrderPlantConfig(
                baseline_level=45.0,
                control_gain=1.6,
                response_rate=0.35,
                min_value=0.0,
                max_value=100.0,
            ),
            simulation_config=ClosedLoopSimulationConfig(
                initial_value=25.0,
                horizon=10,
                disturbance_sequence=[0.0] * 10,
            ),
        ),
        BenchmarkScenario(
            scenario_id="sustained_disturbance",
            label="Sustained Disturbance",
            description="Opera cerca del objetivo pero recibe perturbaciones negativas sostenidas.",
            setpoint_value=55.0,
            plant_config=FirstOrderPlantConfig(
                baseline_level=45.0,
                control_gain=1.6,
                response_rate=0.35,
                min_value=0.0,
                max_value=100.0,
            ),
            simulation_config=ClosedLoopSimulationConfig(
                initial_value=50.0,
                horizon=10,
                disturbance_sequence=[0.0, 0.0, -3.0, -3.0, -3.0, -3.0, -3.0, 0.0, 0.0, 0.0],
            ),
        ),
        BenchmarkScenario(
            scenario_id="near_setpoint_operation",
            label="Near Setpoint Operation",
            description="Opera muy cerca del setpoint con perturbaciones pequeñas.",
            setpoint_value=55.0,
            plant_config=FirstOrderPlantConfig(
                baseline_level=45.0,
                control_gain=1.6,
                response_rate=0.35,
                min_value=0.0,
                max_value=100.0,
            ),
            simulation_config=ClosedLoopSimulationConfig(
                initial_value=54.0,
                horizon=10,
                disturbance_sequence=[0.3, -0.2, 0.4, -0.5, 0.2, 0.0, -0.3, 0.4, 0.0, -0.2],
            ),
        ),
    ]


def build_benchmark_table_rows(
    scenario: BenchmarkScenario,
    summary_metrics: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Build compact table rows for quick benchmark comparisons."""
    return [
        {
            "scenario_id": scenario.scenario_id,
            "scenario_label": scenario.label,
            "strategy": strategy,
            "cumulative_absolute_error": metrics["cumulative_absolute_error"],
            "cumulative_squared_error": metrics["cumulative_squared_error"],
            "total_applied_effort": metrics["total_applied_effort"],
            "action_change_count": metrics["action_change_count"],
            "average_distance_to_setpoint": metrics["average_distance_to_setpoint"],
            "hold_count": metrics["hold_count"],
        }
        for strategy, metrics in summary_metrics.items()
    ]


def build_scenario_assessment(
    scenario: BenchmarkScenario,
    summary_metrics: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Summarize which strategy is better on key metrics for one scenario."""
    threshold = summary_metrics["threshold"]
    proportional = summary_metrics["proportional"]

    return {
        "scenario_id": scenario.scenario_id,
        "scenario_label": scenario.label,
        "better_absolute_error": (
            "threshold"
            if threshold["cumulative_absolute_error"]
            < proportional["cumulative_absolute_error"]
            else "proportional"
        ),
        "better_squared_error": (
            "threshold"
            if threshold["cumulative_squared_error"]
            < proportional["cumulative_squared_error"]
            else "proportional"
        ),
        "lower_effort": (
            "threshold"
            if threshold["total_applied_effort"] < proportional["total_applied_effort"]
            else "proportional"
        ),
    }


def run_closed_loop_benchmark_suite() -> Dict[str, Any]:
    """Run the standard suite across threshold and proportional strategies."""
    variable = build_comparison_variable()
    threshold_evaluator = ThresholdEvaluator()
    proportional_evaluator = ProportionalEvaluator()
    scenarios = build_standard_benchmark_scenarios()

    scenario_results = []
    benchmark_table = []
    scenario_assessments = []

    for scenario in scenarios:
        threshold_run = simulate_closed_loop_strategy(
            strategy_name="threshold",
            evaluator=threshold_evaluator,
            variable=variable,
            parameters=build_threshold_parameters(),
            setpoint_value=scenario.setpoint_value,
            plant_config=scenario.plant_config,
            simulation_config=scenario.simulation_config,
        )
        proportional_run = simulate_closed_loop_strategy(
            strategy_name="proportional",
            evaluator=proportional_evaluator,
            variable=variable,
            parameters=build_proportional_parameters(),
            setpoint_value=scenario.setpoint_value,
            plant_config=scenario.plant_config,
            simulation_config=scenario.simulation_config,
        )

        summary_metrics = {
            "threshold": calculate_summary_metrics("threshold", threshold_run["steps"]),
            "proportional": calculate_summary_metrics(
                "proportional",
                proportional_run["steps"],
            ),
        }

        scenario_results.append(
            {
                "scenario": {
                    "scenario_id": scenario.scenario_id,
                    "label": scenario.label,
                    "description": scenario.description,
                    "setpoint_value": scenario.setpoint_value,
                    "plant_config": asdict(scenario.plant_config),
                    "simulation_config": asdict(scenario.simulation_config),
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
            }
        )
        benchmark_table.extend(build_benchmark_table_rows(scenario, summary_metrics))
        scenario_assessments.append(build_scenario_assessment(scenario, summary_metrics))

    interpretation = [
        "threshold suele destacar cuando se prioriza correccion rapida con reglas fijas y aceptando mayor esfuerzo.",
        "proportional suele destacar cuando se prioriza menor esfuerzo y una respuesta mas graduada.",
        "cerca del setpoint, proportional tiende a evitar escalones bruscos.",
        "frente a perturbaciones sostenidas, la comparacion debe mirar error y esfuerzo juntos, no una sola metrica.",
    ]

    return {
        "benchmark_name": "closed-loop-mvp-benchmark",
        "scenarios": scenario_results,
        "benchmark_table": benchmark_table,
        "scenario_assessments": scenario_assessments,
        "interpretation": interpretation,
    }
