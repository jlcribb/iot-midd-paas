from parametric_control_engine.simulation.benchmark_exporter import (
    build_benchmark_markdown_report,
    build_benchmark_snapshot,
)
from parametric_control_engine.simulation.benchmark_suite import (
    run_closed_loop_benchmark_suite,
)


def test_build_benchmark_snapshot_contains_required_sections():
    benchmark = run_closed_loop_benchmark_suite()

    snapshot = build_benchmark_snapshot(benchmark)

    assert snapshot["benchmark_name"] == "closed-loop-mvp-benchmark"
    assert "scorecard" in snapshot
    assert "markdown_table" in snapshot
    assert "executive_summary" in snapshot
    assert "scenario_breakdown" in snapshot
    assert len(snapshot["scenario_breakdown"]) == 3


def test_build_benchmark_markdown_report_contains_regeneration_command():
    benchmark = run_closed_loop_benchmark_suite()
    snapshot = build_benchmark_snapshot(benchmark)

    report = build_benchmark_markdown_report(snapshot)

    assert "# MVP Benchmark Snapshot" in report
    assert "## Executive Summary" in report
    assert "## Benchmark Table" in report
    assert "python -m parametric_control_engine.examples.export_benchmark_artifacts" in report
