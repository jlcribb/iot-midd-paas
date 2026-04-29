"""End-to-end pipeline demo for the parametric control engine MVP."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

from ..adapters.event_adapter import EventDrivenRecommendationAdapter
from ..adapters.recommendation_sink_adapter import RecommendationSinkAdapter
from ..examples.event_driven_demo import build_demo_binding, build_demo_event


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Unsupported value for JSON serialization: {type(value)!r}")


def main() -> None:
    event_adapter = EventDrivenRecommendationAdapter(build_demo_binding())
    sink_adapter = RecommendationSinkAdapter()
    recommendation = event_adapter.evaluate_event(build_demo_event())
    sink_output = sink_adapter.build_sink_output(recommendation)
    print(json.dumps(asdict(sink_output), indent=2, default=_json_default))


if __name__ == "__main__":
    main()
