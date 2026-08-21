from copy import deepcopy

import pytest

from iot_middleware.services.simulation_result_model import canonical_result_evidence


EXPERIMENT = "a" * 64


def output(sequence, event_id, *, value=2.0, recommendation=True, actionable=False):
    return {"sequence": sequence, "event_id": event_id, "virtual_timestamp": f"2026-08-21T00:0{sequence}:00+00:00",
            "evaluation_outcome": "RECOMMENDED" if recommendation else "NO_RECOMMENDATION", "has_recommendation": recommendation,
            "actionable": actionable, "recommendation_only": recommendation and not actionable,
            "reason_code": "ACTIONABLE_FROZEN_TARGET" if actionable else "RECOMMENDATION_ONLY_NO_FROZEN_TARGET" if recommendation else "NO_RECOMMENDATION_HOLD",
            "recommendation_kind": "increase" if recommendation else None, "action_label": "increase" if recommendation else None,
            "command_value": value if recommendation else None, "run_id": "volatile", "created_at": "volatile"}


def test_same_deterministic_outputs_have_same_fingerprint_without_run_metadata():
    first = [output(1, "11111111-1111-4111-8111-111111111111"), output(2, "22222222-2222-4222-8222-222222222222", actionable=True)]
    second = deepcopy(first)
    second[0]["run_id"] = "another-run"; second[1]["created_at"] = "later"
    assert canonical_result_evidence(experiment_fingerprint=EXPERIMENT, outputs=first).result_fingerprint == canonical_result_evidence(experiment_fingerprint=EXPERIMENT, outputs=second).result_fingerprint


def test_changed_deterministic_output_changes_result_fingerprint():
    first = [output(1, "11111111-1111-4111-8111-111111111111")]
    changed = deepcopy(first); changed[0]["command_value"] = 99.0
    assert canonical_result_evidence(experiment_fingerprint=EXPERIMENT, outputs=first).result_fingerprint != canonical_result_evidence(experiment_fingerprint=EXPERIMENT, outputs=changed).result_fingerprint


def test_recommendation_only_is_evidence_not_failure_and_sequence_is_strict():
    evidence = canonical_result_evidence(experiment_fingerprint=EXPERIMENT, outputs=[output(1, "11111111-1111-4111-8111-111111111111")])
    assert evidence.recommendation_only_count == 1 and evidence.failed_domain_event_count == 0
    with pytest.raises(ValueError, match="contiguous"):
        canonical_result_evidence(experiment_fingerprint=EXPERIMENT, outputs=[output(2, "11111111-1111-4111-8111-111111111111")])
