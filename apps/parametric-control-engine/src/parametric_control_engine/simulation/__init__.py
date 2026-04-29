"""Closed-loop simulation helpers for the parametric control engine MVP."""

from .first_order import (
    ClosedLoopSimulationConfig,
    FirstOrderPlantConfig,
    simulate_closed_loop_strategy,
    simulate_first_order_step,
)
from .benchmark_suite import (
    BenchmarkScenario,
    build_standard_benchmark_scenarios,
    run_closed_loop_benchmark_suite,
)
from .benchmark_formatter import (
    build_executive_summary,
    build_markdown_table,
    build_presentation_ready_benchmark,
    build_scorecard_view,
)
from .benchmark_exporter import (
    build_benchmark_markdown_report,
    build_benchmark_snapshot,
    export_benchmark_artifacts,
)
from .metrics import build_comparison_overview, calculate_summary_metrics

__all__ = [
    "BenchmarkScenario",
    "build_benchmark_markdown_report",
    "build_benchmark_snapshot",
    "build_executive_summary",
    "build_markdown_table",
    "build_presentation_ready_benchmark",
    "build_scorecard_view",
    "build_standard_benchmark_scenarios",
    "ClosedLoopSimulationConfig",
    "FirstOrderPlantConfig",
    "build_comparison_overview",
    "calculate_summary_metrics",
    "export_benchmark_artifacts",
    "run_closed_loop_benchmark_suite",
    "simulate_closed_loop_strategy",
    "simulate_first_order_step",
]
