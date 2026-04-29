from parametric_control_engine.examples.closed_loop_threshold_vs_proportional_demo import (
    run_closed_loop_threshold_vs_proportional_comparison,
)


def test_closed_loop_comparison_returns_divergent_error_metrics():
    result = run_closed_loop_threshold_vs_proportional_comparison()

    threshold_summary = result["summary_metrics"]["threshold"]
    proportional_summary = result["summary_metrics"]["proportional"]

    assert result["scenario"]["name"] == "tank-level-closed-loop-comparison"
    assert len(result["trajectories"]["threshold"]["state_series"]) == (
        result["scenario"]["simulation_config"]["horizon"] + 1
    )
    assert threshold_summary["cumulative_absolute_error"] != proportional_summary["cumulative_absolute_error"]
    assert threshold_summary["cumulative_squared_error"] != proportional_summary["cumulative_squared_error"]


def test_closed_loop_comparison_keeps_proportional_more_efficient_in_reference_scenario():
    result = run_closed_loop_threshold_vs_proportional_comparison()

    threshold_summary = result["summary_metrics"]["threshold"]
    proportional_summary = result["summary_metrics"]["proportional"]

    assert threshold_summary["total_applied_effort"] > proportional_summary["total_applied_effort"]
    assert len(proportional_summary["unique_nonzero_signals"]) > 1
    assert len(result["comparison_overview"]) == 2
