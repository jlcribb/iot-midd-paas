from parametric_control_engine.simulation.benchmark_suite import (
    build_standard_benchmark_scenarios,
    run_closed_loop_benchmark_suite,
)


def test_build_standard_benchmark_scenarios_returns_three_named_cases():
    scenarios = build_standard_benchmark_scenarios()

    assert len(scenarios) == 3
    assert [scenario.scenario_id for scenario in scenarios] == [
        "large_initial_error",
        "sustained_disturbance",
        "near_setpoint_operation",
    ]


def test_closed_loop_benchmark_suite_returns_table_and_assessments():
    result = run_closed_loop_benchmark_suite()

    assert result["benchmark_name"] == "closed-loop-mvp-benchmark"
    assert len(result["scenarios"]) == 3
    assert len(result["benchmark_table"]) == 6
    assert len(result["scenario_assessments"]) == 3
    assert len(result["interpretation"]) >= 3


def test_closed_loop_benchmark_suite_contains_one_row_per_strategy_and_scenario():
    result = run_closed_loop_benchmark_suite()

    scenarios = {row["scenario_id"] for row in result["benchmark_table"]}
    strategies = {row["strategy"] for row in result["benchmark_table"]}

    assert scenarios == {
        "large_initial_error",
        "sustained_disturbance",
        "near_setpoint_operation",
    }
    assert strategies == {"threshold", "proportional"}
