"""Canonical, immutable evidence derived only from simulation run outputs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable


CANONICAL_RESULT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class SimulationResultEvidence:
    canonical_result_schema_version: int
    experiment_fingerprint: str
    result_fingerprint: str
    processed_events: int
    evaluation_count: int
    recommendation_count: int
    actionable_recommendation_count: int
    recommendation_only_count: int
    failed_domain_event_count: int
    first_virtual_timestamp: datetime | None
    last_virtual_timestamp: datetime | None
    canonical_outputs: list[dict[str, Any]]


def canonical_result_evidence(*, experiment_fingerprint: str, outputs: Iterable[dict[str, Any]]) -> SimulationResultEvidence:
    """Build deterministic result evidence without run metadata or live reads."""
    ordered = list(outputs)
    canonical_outputs = [_canonical_output(output, expected_sequence=index) for index, output in enumerate(ordered, start=1)]
    recommendation_count = sum(item["recommendation_state"] != "NO_RECOMMENDATION" for item in canonical_outputs)
    actionable_count = sum(item["actionable"] for item in canonical_outputs)
    recommendation_only_count = sum(item["recommendation_state"] == "RECOMMENDATION_ONLY" for item in canonical_outputs)
    failed_count = sum(item["evaluation_outcome"] == "FAILED" for item in canonical_outputs)
    representation = {
        "canonical_result_schema_version": CANONICAL_RESULT_SCHEMA_VERSION,
        "experiment_fingerprint": experiment_fingerprint,
        "outputs": canonical_outputs,
    }
    fingerprint = hashlib.sha256(_canonical_json(representation).encode("utf-8")).hexdigest()
    timestamps = [datetime.fromisoformat(item["virtual_timestamp"].replace("Z", "+00:00")) for item in canonical_outputs]
    return SimulationResultEvidence(
        canonical_result_schema_version=CANONICAL_RESULT_SCHEMA_VERSION,
        experiment_fingerprint=experiment_fingerprint,
        result_fingerprint=fingerprint,
        processed_events=len(canonical_outputs), evaluation_count=len(canonical_outputs),
        recommendation_count=recommendation_count, actionable_recommendation_count=actionable_count,
        recommendation_only_count=recommendation_only_count, failed_domain_event_count=failed_count,
        first_virtual_timestamp=timestamps[0] if timestamps else None,
        last_virtual_timestamp=timestamps[-1] if timestamps else None,
        canonical_outputs=canonical_outputs,
    )


def _canonical_output(output: dict[str, Any], *, expected_sequence: int) -> dict[str, Any]:
    sequence = int(output["sequence"])
    if sequence != expected_sequence:
        raise ValueError("simulation run outputs must have contiguous deterministic sequence")
    recommendation = bool(output.get("has_recommendation"))
    actionable = bool(output.get("actionable"))
    recommendation_only = bool(output.get("recommendation_only"))
    if actionable and not recommendation:
        raise ValueError("actionable output requires a recommendation")
    if recommendation_only != (recommendation and not actionable):
        raise ValueError("recommendation-only state contradicts deterministic output")
    return {
        "sequence": sequence,
        "source_event_id": str(output["event_id"]),
        "virtual_timestamp": str(output["virtual_timestamp"]),
        "evaluation_outcome": str(output["evaluation_outcome"]),
        "recommendation_state": "RECOMMENDATION_ONLY" if recommendation_only else "RECOMMENDATION" if recommendation else "NO_RECOMMENDATION",
        "actionable": actionable,
        "reason_code": str(output["reason_code"]),
        "recommendation_kind": output.get("recommendation_kind"),
        "action_label": output.get("action_label"),
        "command_value": output.get("command_value"),
    }


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
