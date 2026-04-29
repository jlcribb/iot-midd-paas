import pytest

from parametric_control_engine.simulation.first_order import (
    ClosedLoopSimulationConfig,
    FirstOrderPlantConfig,
    simulate_closed_loop_strategy,
    simulate_first_order_step,
)
from parametric_control_engine.evaluators.proportional import ProportionalEvaluator
from parametric_control_engine.examples.threshold_vs_proportional_demo import (
    build_comparison_variable,
    build_proportional_parameters,
)


def test_simulate_first_order_step_moves_toward_control_shaped_target():
    config = FirstOrderPlantConfig(
        baseline_level=45.0,
        control_gain=1.5,
        response_rate=0.4,
        min_value=0.0,
        max_value=100.0,
    )

    result = simulate_first_order_step(
        current_value=35.0,
        applied_signal=10.0,
        disturbance=-2.0,
        plant_config=config,
    )

    assert result["desired_level"] == pytest.approx(58.0)
    assert result["next_value"] == pytest.approx(44.2)


def test_closed_loop_simulation_returns_state_series_and_steps():
    result = simulate_closed_loop_strategy(
        strategy_name="proportional",
        evaluator=ProportionalEvaluator(),
        variable=build_comparison_variable(),
        parameters=build_proportional_parameters(),
        setpoint_value=55.0,
        plant_config=FirstOrderPlantConfig(
            baseline_level=45.0,
            control_gain=1.6,
            response_rate=0.35,
            min_value=0.0,
            max_value=100.0,
        ),
        simulation_config=ClosedLoopSimulationConfig(
            initial_value=35.0,
            horizon=3,
            disturbance_sequence=[0.0, -1.5, 0.0],
        ),
    )

    assert result["strategy"] == "proportional"
    assert len(result["steps"]) == 3
    assert len(result["state_series"]) == 4
    assert result["steps"][0]["measurement"] == pytest.approx(35.0)
    assert "next_measurement" in result["steps"][0]
