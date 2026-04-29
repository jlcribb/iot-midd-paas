"""Generate persistent benchmark artifacts under docs/benchmark."""

from __future__ import annotations

import json
from pathlib import Path

from ..simulation.benchmark_exporter import export_benchmark_artifacts


def main() -> None:
    repo_root = Path(__file__).resolve().parents[5]
    output_dir = repo_root / "docs" / "benchmark"
    result = export_benchmark_artifacts(output_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
