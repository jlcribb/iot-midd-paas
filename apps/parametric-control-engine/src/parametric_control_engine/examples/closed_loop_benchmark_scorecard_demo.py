"""Presentation-ready benchmark demo with scorecard and Markdown output."""

from __future__ import annotations

import json

from ..simulation.benchmark_formatter import build_presentation_ready_benchmark
from ..simulation.benchmark_suite import run_closed_loop_benchmark_suite


def main() -> None:
    benchmark = run_closed_loop_benchmark_suite()
    presentation = build_presentation_ready_benchmark(benchmark)

    print("=== SCORECARD ===")
    print(json.dumps(presentation["scorecard"], indent=2))
    print()
    print("=== MARKDOWN TABLE ===")
    print(presentation["markdown_table"])
    print()
    print("=== EXECUTIVE SUMMARY ===")
    print(presentation["executive_summary"])


if __name__ == "__main__":
    main()
