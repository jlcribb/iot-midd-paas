#!/usr/bin/env python3

"""
Smoke helper for control_engine_worker.

This does not require RabbitMQ/MQTT.
It invokes the worker directly with a representative telemetry event.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENGINE_SRC = os.path.join(REPO_ROOT, "apps", "parametric-control-engine", "src")
SRC_ROOT = os.path.join(REPO_ROOT, "src")

for path in [SRC_ROOT, ENGINE_SRC]:
    if path not in sys.path:
        sys.path.insert(0, path)


os.environ.setdefault("CONTROL_WORKER_FORCE_ENABLED", "true")
os.environ.setdefault("CONTROL_WORKER_PUBLISH_MODE", "stdout")


from iot_middleware.services.control_engine_worker import run_once_from_json


def main() -> None:
    event = {
        "project_id": os.getenv(
            "CONTROL_TEST_PROJECT_ID",
            "00000000-0000-0000-0000-000000000001",
        ),
        "variable": os.getenv("CONTROL_TEST_VARIABLE", "tank_level"),
        "value": float(os.getenv("CONTROL_TEST_VALUE", "72.5")),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context": {
            "sector": os.getenv("CONTROL_TEST_SECTOR", "tank_A"),
        },
    }

    print("[SMOKE] input event:")
    print(json.dumps(event, indent=2, ensure_ascii=False))

    result = run_once_from_json(json.dumps(event))

    print("[SMOKE] result:")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
