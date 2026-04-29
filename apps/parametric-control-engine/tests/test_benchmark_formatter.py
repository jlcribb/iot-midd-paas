from parametric_control_engine.simulation.benchmark_formatter import (
    build_executive_summary,
    build_markdown_table,
    build_presentation_ready_benchmark,
    build_scorecard_view,
)
from parametric_control_engine.simulation.benchmark_suite import (
    run_closed_loop_benchmark_suite,
)


def test_build_scorecard_view_returns_one_entry_per_scenario():
    benchmark = run_closed_loop_benchmark_suite()

    scorecard = build_scorecard_view(benchmark)

    assert len(scorecard) == 3
    assert scorecard[0]["scenario_id"] == "large_initial_error"
    assert "winner_absolute_error" in scorecard[0]
    assert "threshold" in scorecard[0]
    assert "proportional" in scorecard[0]


def test_build_markdown_table_contains_expected_headers_and_rows():
    benchmark = run_closed_loop_benchmark_suite()

    markdown = build_markdown_table(benchmark)

    assert "| Scenario | Strategy | Abs Error | Sq Error | Effort | Avg Dist | Action Changes | Holds |" in markdown
    assert "Large Initial Error" in markdown
    assert "proportional" in markdown


def test_build_presentation_ready_benchmark_bundles_outputs():
    benchmark = run_closed_loop_benchmark_suite()

    presentation = build_presentation_ready_benchmark(benchmark)

    assert presentation["benchmark_name"] == "closed-loop-mvp-benchmark"
    assert len(presentation["scorecard"]) == 3
    assert presentation["markdown_table"].startswith("| Scenario |")
    assert presentation["executive_summary"].startswith("Executive summary:")


def test_build_executive_summary_mentions_tradeoff():
    benchmark = run_closed_loop_benchmark_suite()

    summary = build_executive_summary(benchmark)

    assert "Proportional achieved lower cumulative absolute error" in summary
    assert "tradeoff" in summary
