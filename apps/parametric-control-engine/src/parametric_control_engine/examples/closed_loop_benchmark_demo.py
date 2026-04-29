"""Runnable benchmark demo for the closed-loop MVP scenarios."""

from __future__ import annotations

import json
from datetime import datetime

from ..simulation.benchmark_suite import run_closed_loop_benchmark_suite


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Unsupported value for JSON serialization: {type(value)!r}")


def main() -> None:
    print(
        json.dumps(
            run_closed_loop_benchmark_suite(),
            indent=2,
            default=_json_default,
        )
    )


if __name__ == "__main__":
    main()
