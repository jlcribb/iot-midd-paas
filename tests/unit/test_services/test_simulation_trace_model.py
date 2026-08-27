from __future__ import annotations

import pytest

from iot_middleware.services.simulation_trace_model import canonical_trace_evidence


def output(sequence: int, value: float = 8.0, timestamp: str | None = None):
    return {"sequence": sequence, "virtual_timestamp": timestamp or f"2026-08-26T00:0{sequence}:00+00:00",
            "process_value": value, "setpoint": 10.0, "control_output": 2.0, "actuator_state": "INCREASE", "constraint_state": None}


def test_trace_hash_is_ordered_canonical_and_sensitive_to_semantic_points():
    first = canonical_trace_evidence(experiment_fingerprint="a" * 64, outputs=[output(1), output(2, 10.0)])
    repeated = canonical_trace_evidence(experiment_fingerprint="a" * 64, outputs=[output(1), output(2, 10.0)])
    changed = canonical_trace_evidence(experiment_fingerprint="a" * 64, outputs=[output(1), output(2, 11.0)])
    assert first.trace_hash == repeated.trace_hash
    assert first.trace_hash != changed.trace_hash
    assert first.point_count == 2 and first.simulation_duration_seconds == 60.0


@pytest.mark.parametrize("changed", [
    lambda rows: rows.__setitem__(1, output(1)),
    lambda rows: rows.__setitem__(1, output(2, timestamp="2026-08-26T00:00:30+00:00")),
    lambda rows: rows[0].__setitem__("process_value", float("nan")),
    lambda rows: rows[0].__setitem__("control_output", float("inf")),
    lambda rows: rows[0].pop("setpoint"),
])
def test_trace_rejects_malformed_or_missing_primary_evidence(changed):
    rows = [output(1), output(2, 10.0)]
    changed(rows)
    with pytest.raises(ValueError):
        canonical_trace_evidence(experiment_fingerprint="a" * 64, outputs=rows)
