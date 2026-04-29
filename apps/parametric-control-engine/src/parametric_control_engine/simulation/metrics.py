"""Shared metric helpers for open-loop and closed-loop comparison experiments."""

from __future__ import annotations


def calculate_summary_metrics(strategy_name: str, results: list[dict]) -> dict:
    """Compute reproducible summary metrics for one control strategy."""
    signals = [step["applied_signal"] for step in results]
    actions = [step["action_kind"] for step in results]
    errors = [step["error"] for step in results]
    nonzero_abs_signals = sorted(
        {round(abs(signal), 3) for signal in signals if abs(signal) > 0}
    )
    action_changes = sum(
        1 for current, nxt in zip(actions, actions[1:]) if current != nxt
    )
    cumulative_absolute_error = sum(abs(error) for error in errors)
    cumulative_squared_error = sum(error * error for error in errors)
    total_applied_effort = sum(abs(signal) for signal in signals)
    average_distance_to_setpoint = cumulative_absolute_error / len(results)

    return {
        "strategy": strategy_name,
        "steps": len(results),
        "hold_count": sum(1 for action in actions if action == "hold"),
        "action_change_count": action_changes,
        "cumulative_absolute_error": round(cumulative_absolute_error, 3),
        "cumulative_squared_error": round(cumulative_squared_error, 3),
        "total_applied_effort": round(total_applied_effort, 3),
        "average_distance_to_setpoint": round(average_distance_to_setpoint, 3),
        "average_abs_signal": round(total_applied_effort / len(results), 3),
        "unique_nonzero_signals": nonzero_abs_signals,
    }


def build_comparison_overview(summary_metrics: dict) -> list[dict]:
    """Create a compact overview block for quick presentation reads."""
    ordered_strategies = ["threshold", "proportional"]
    return [
        {
            "strategy": strategy,
            "cumulative_absolute_error": summary_metrics[strategy][
                "cumulative_absolute_error"
            ],
            "cumulative_squared_error": summary_metrics[strategy][
                "cumulative_squared_error"
            ],
            "total_applied_effort": summary_metrics[strategy]["total_applied_effort"],
            "action_change_count": summary_metrics[strategy]["action_change_count"],
            "average_distance_to_setpoint": summary_metrics[strategy][
                "average_distance_to_setpoint"
            ],
            "unique_nonzero_signals": summary_metrics[strategy]["unique_nonzero_signals"],
        }
        for strategy in ordered_strategies
    ]
