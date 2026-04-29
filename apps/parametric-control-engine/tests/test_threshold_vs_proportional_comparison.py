from parametric_control_engine.examples.threshold_vs_proportional_demo import (
    run_threshold_vs_proportional_comparison,
)
from parametric_control_engine.simulation.metrics import calculate_summary_metrics


def test_threshold_vs_proportional_comparison_returns_structured_steps():
    result = run_threshold_vs_proportional_comparison()

    assert result["scenario"]["name"] == "tank-level-comparison"
    assert len(result["comparison_steps"]) == len(result["scenario"]["measurements"])
    assert result["comparison_steps"][0]["threshold"]["response"]["evaluator_name"] == "threshold"
    assert result["comparison_steps"][0]["proportional"]["response"]["evaluator_name"] == "proportional"
    assert "comparison_overview" in result
    assert len(result["comparison_overview"]) == 2


def test_calculate_summary_metrics_returns_expected_aggregates():
    summary = calculate_summary_metrics(
        "test-strategy",
        [
            {
                "error": 3.0,
                "distance_to_setpoint": 3.0,
                "applied_signal": 8.0,
                "action_kind": "increase",
            },
            {
                "error": -1.0,
                "distance_to_setpoint": 1.0,
                "applied_signal": 0.0,
                "action_kind": "hold",
            },
            {
                "error": -4.0,
                "distance_to_setpoint": 4.0,
                "applied_signal": -5.0,
                "action_kind": "decrease",
            },
        ],
    )

    assert summary["cumulative_absolute_error"] == 8.0
    assert summary["cumulative_squared_error"] == 26.0
    assert summary["total_applied_effort"] == 13.0
    assert summary["action_change_count"] == 2
    assert summary["average_distance_to_setpoint"] == 2.667
    assert summary["unique_nonzero_signals"] == [5.0, 8.0]


def test_threshold_vs_proportional_summary_shows_expected_behavior_difference():
    result = run_threshold_vs_proportional_comparison()

    threshold_summary = result["summary_metrics"]["threshold"]
    proportional_summary = result["summary_metrics"]["proportional"]

    assert threshold_summary["unique_nonzero_signals"] == [8.0]
    assert len(proportional_summary["unique_nonzero_signals"]) > 1
    assert threshold_summary["total_applied_effort"] > proportional_summary["total_applied_effort"]
    assert threshold_summary["average_abs_signal"] > proportional_summary["average_abs_signal"]
    assert threshold_summary["cumulative_absolute_error"] == proportional_summary["cumulative_absolute_error"]
    assert threshold_summary["average_distance_to_setpoint"] == proportional_summary["average_distance_to_setpoint"]
    assert threshold_summary["hold_count"] >= proportional_summary["hold_count"]
