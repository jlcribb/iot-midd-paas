"""Persistent export helpers for MVP benchmark artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .benchmark_formatter import (
    build_executive_summary,
    build_markdown_table,
    build_scorecard_view,
)
from .benchmark_suite import run_closed_loop_benchmark_suite


def build_benchmark_snapshot(benchmark_result: Dict[str, Any]) -> Dict[str, Any]:
    """Build a deterministic snapshot structure for persisted benchmark artifacts."""
    assessments = {
        item["scenario_id"]: item for item in benchmark_result["scenario_assessments"]
    }
    scenario_breakdown = []

    for scenario in benchmark_result["scenarios"]:
        scenario_meta = scenario["scenario"]
        scenario_breakdown.append(
            {
                "scenario": scenario_meta,
                "summary_metrics": scenario["summary_metrics"],
                "comparison_overview": scenario["comparison_overview"],
                "assessment": assessments[scenario_meta["scenario_id"]],
            }
        )

    return {
        "benchmark_name": benchmark_result["benchmark_name"],
        "scorecard": build_scorecard_view(benchmark_result),
        "markdown_table": build_markdown_table(benchmark_result),
        "executive_summary": build_executive_summary(benchmark_result),
        "scenario_breakdown": scenario_breakdown,
    }


def build_benchmark_markdown_report(snapshot: Dict[str, Any]) -> str:
    """Render a Markdown report suitable for docs and presentations."""
    lines = [
        "# MVP Benchmark Snapshot",
        "",
        "## Executive Summary",
        "",
        snapshot["executive_summary"],
        "",
        "## Scorecard",
        "",
    ]

    for item in snapshot["scorecard"]:
        lines.extend(
            [
                f"### {item['scenario_label']}",
                "",
                f"- Winner (absolute error): `{item['winner_absolute_error']}`",
                f"- Winner (squared error): `{item['winner_squared_error']}`",
                f"- Winner (lower effort): `{item['winner_lower_effort']}`",
                f"- Threshold: abs error `{item['threshold']['cumulative_absolute_error']}`, sq error `{item['threshold']['cumulative_squared_error']}`, effort `{item['threshold']['total_applied_effort']}`, avg dist `{item['threshold']['average_distance_to_setpoint']}`",
                f"- Proportional: abs error `{item['proportional']['cumulative_absolute_error']}`, sq error `{item['proportional']['cumulative_squared_error']}`, effort `{item['proportional']['total_applied_effort']}`, avg dist `{item['proportional']['average_distance_to_setpoint']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Benchmark Table",
            "",
            snapshot["markdown_table"],
            "",
            "## Scenario Breakdown",
            "",
        ]
    )

    for item in snapshot["scenario_breakdown"]:
        scenario = item["scenario"]
        assessment = item["assessment"]
        lines.extend(
            [
                f"### {scenario['label']}",
                "",
                f"- Scenario ID: `{scenario['scenario_id']}`",
                f"- Description: {scenario['description']}",
                f"- Setpoint: `{scenario['setpoint_value']}`",
                f"- Best absolute error: `{assessment['better_absolute_error']}`",
                f"- Best squared error: `{assessment['better_squared_error']}`",
                f"- Lower effort: `{assessment['lower_effort']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Regeneration",
            "",
            "Regenerate these artifacts with:",
            "",
            "```bash",
            "PYTHONPATH=apps/parametric-control-engine/src \\",
            "./venv/bin/python -m parametric_control_engine.examples.export_benchmark_artifacts",
            "```",
            "",
        ]
    )

    return "\n".join(lines)


def export_benchmark_artifacts(output_dir: Path) -> Dict[str, str]:
    """Generate and persist the benchmark snapshot as Markdown and JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark_result = run_closed_loop_benchmark_suite()
    snapshot = build_benchmark_snapshot(benchmark_result)
    markdown_report = build_benchmark_markdown_report(snapshot)

    json_path = output_dir / "mvp_benchmark.json"
    markdown_path = output_dir / "mvp_benchmark.md"

    json_path.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown_report + "\n", encoding="utf-8")

    return {
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
    }
