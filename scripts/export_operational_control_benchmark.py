#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

for path in [str(REPO_ROOT), str(SRC_ROOT)]:
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault("REPO_ROOT", str(REPO_ROOT))

from iot_middleware.services.operational_control_benchmark import (  # noqa: E402
    export_operational_control_benchmark_artifacts,
)


def main() -> int:
    artifacts = export_operational_control_benchmark_artifacts(
        REPO_ROOT / "docs" / "benchmark"
    )
    print(json.dumps(artifacts, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
