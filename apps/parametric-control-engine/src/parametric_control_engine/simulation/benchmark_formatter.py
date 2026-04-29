"""Presentation-ready formatting helpers for the closed-loop benchmark suite."""

from __future__ import annotations

from typing import Any, Dict, List


def build_scorecard_view(benchmark_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build a compact scorecard grouped by scenario for slides and docs."""
    scorecard = []
    assessments = {
        item["scenario_id"]: item for item in benchmark_result["scenario_assessments"]
    }

    for scenario in benchmark_result["scenarios"]:
        scenario_meta = scenario["scenario"]
        metrics = scenario["summary_metrics"]
        assessment = assessments[scenario_meta["scenario_id"]]
        scorecard.append(
            {
                "scenario_id": scenario_meta["scenario_id"],
                "scenario_label": scenario_meta["label"],
                "winner_absolute_error": assessment["better_absolute_error"],
                "winner_squared_error": assessment["better_squared_error"],
                "winner_lower_effort": assessment["lower_effort"],
                "threshold": {
                    "cumulative_absolute_error": metrics["threshold"][
                        "cumulative_absolute_error"
                    ],
                    "cumulative_squared_error": metrics["threshold"][
                        "cumulative_squared_error"
                    ],
                    "total_applied_effort": metrics["threshold"][
                        "total_applied_effort"
                    ],
                    "average_distance_to_setpoint": metrics["threshold"][
                        "average_distance_to_setpoint"
                    ],
                },
                "proportional": {
                    "cumulative_absolute_error": metrics["proportional"][
                        "cumulative_absolute_error"
                    ],
                    "cumulative_squared_error": metrics["proportional"][
                        "cumulative_squared_error"
                    ],
                    "total_applied_effort": metrics["proportional"][
                        "total_applied_effort"
                    ],
                    "average_distance_to_setpoint": metrics["proportional"][
                        "average_distance_to_setpoint"
                    ],
                },
            }
        )

    return scorecard


def build_markdown_table(benchmark_result: Dict[str, Any]) -> str:
    """Render the compact benchmark table as Markdown."""
    headers = [
        "Scenario",
        "Strategy",
        "Abs Error",
        "Sq Error",
        "Effort",
        "Avg Dist",
        "Action Changes",
        "Holds",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in benchmark_result["benchmark_table"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["scenario_label"],
                    row["strategy"],
                    str(row["cumulative_absolute_error"]),
                    str(row["cumulative_squared_error"]),
                    str(row["total_applied_effort"]),
                    str(row["average_distance_to_setpoint"]),
                    str(row["action_change_count"]),
                    str(row["hold_count"]),
                ]
            )
            + " |"
        )

    return "\n".join(lines)


def build_executive_summary(benchmark_result: Dict[str, Any]) -> str:
    """Produce a short executive interpretation block for pitch materials."""
    assessments = benchmark_result["scenario_assessments"]
    proportional_wins = sum(
        1 for item in assessments if item["better_absolute_error"] == "proportional"
    )
    threshold_wins = sum(
        1 for item in assessments if item["better_absolute_error"] == "threshold"
    )
    lower_effort_proportional = sum(
        1 for item in assessments if item["lower_effort"] == "proportional"
    )

    return (
        "Executive summary:\n"
        f"- Proportional achieved lower cumulative absolute error in {proportional_wins} of {len(assessments)} benchmark scenarios.\n"
        f"- Threshold achieved lower cumulative absolute error in {threshold_wins} of {len(assessments)} benchmark scenarios.\n"
        f"- Proportional delivered lower total applied effort in {lower_effort_proportional} of {len(assessments)} scenarios.\n"
        "- The benchmark shows a clear MVP tradeoff: threshold can reduce error faster in some scenarios, while proportional is generally smoother and more effort-efficient."
    )


def build_presentation_ready_benchmark(benchmark_result: Dict[str, Any]) -> Dict[str, Any]:
    """Bundle all presentation-friendly benchmark outputs."""
    return {
        "benchmark_name": benchmark_result["benchmark_name"],
        "scorecard": build_scorecard_view(benchmark_result),
        "markdown_table": build_markdown_table(benchmark_result),
        "executive_summary": build_executive_summary(benchmark_result),
    }
