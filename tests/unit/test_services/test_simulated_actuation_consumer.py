from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from iot_middleware.services.simulated_actuation_adapter import SimulatedActuationAdapter
from iot_middleware.services.simulated_actuation_consumer import SimulatedActuationConsumer
from iot_middleware.storage.actuation_delivery_intent_repository import DeliveryIntent, InvalidDeliveryTransition, VALID_TRANSITIONS


PROJECT_ID = "00000000-0000-0000-0000-000000000001"
SOURCE_ASSET_ID = "00000000-0000-0000-0000-000000000011"


class InMemoryIntentRepository:
    def __init__(self):
        self.by_key = {}
        self.transitions = []

    def create_or_get(self, request):
        existing = self.by_key.get(request.idempotency_key)
        if existing:
            return existing, False
        intent = DeliveryIntent(
            id="00000000-0000-0000-0000-000000000031",
            command_id=request.command_id,
            recommendation_id=request.recommendation_id,
            correlation_id=request.correlation_id,
            project_id=request.project_id,
            policy_id=request.policy_id,
            policy_version=request.policy_version,
            source_asset_id=request.source_asset_id,
            target_asset_id=request.target_asset_id,
            target_kind=request.target_kind,
            target_reference=request.target_reference,
            variable_id=request.variable_id,
            operation=request.operation,
            requested_value=request.requested_value,
            idempotency_key=request.idempotency_key,
            governance_mode=request.governance_mode,
            status="received",
            retry_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=datetime.fromisoformat(request.expires_at),
            last_error=None,
            simulated=True,
        )
        self.by_key[request.idempotency_key] = intent
        return intent, True

    def transition(self, *, command_id, from_statuses, to_status, last_error=None):
        intent = next(item for item in self.by_key.values() if item.command_id == command_id)
        if intent.status not in from_statuses or to_status not in VALID_TRANSITIONS[intent.status]:
            raise InvalidDeliveryTransition(f"{intent.status} -> {to_status}")
        transitioned = replace(intent, status=to_status, last_error=last_error, updated_at=datetime.now(timezone.utc))
        self.by_key[intent.idempotency_key] = transitioned
        self.transitions.append((intent.status, to_status))
        return transitioned


def recommendation(*, expires_at: str, schema_version: str = "1.0"):
    return {
        "message_type": "control.recommendation",
        "schema_version": schema_version,
        "payload": {
            "recommendation_id": "recommendation::test-1",
            "correlation_id": "corr-test-1",
            "project_id": PROJECT_ID,
            "policy_id": "policy-test-1",
            "policy_version": 2,
            "event_id": "evt-test-1",
            "variable_id": "tank_level",
            "action_label": "increase",
            "command_value": 3.5,
            "actuator_name": "pump",
            "source_asset_id": SOURCE_ASSET_ID,
            "created_at": "2026-08-11T00:00:00+00:00",
            "expires_at": expires_at,
        },
    }


def test_valid_recommendation_creates_one_acknowledged_simulated_intent():
    repo = InMemoryIntentRepository()
    audits = []
    consumer = SimulatedActuationConsumer(
        repository=repo,
        audit=lambda action, intent, **kwargs: audits.append((action, intent.status)),
        now=lambda: datetime(2026, 8, 11, 0, 1, tzinfo=timezone.utc),
    )

    outcome = consumer.process(recommendation(expires_at="2026-08-11T00:05:00+00:00"))

    assert outcome.status == "acknowledged"
    assert outcome.result["simulated"] is True
    assert len(repo.by_key) == 1
    assert repo.transitions == [
        ("received", "validated"),
        ("validated", "ready_to_dispatch"),
        ("ready_to_dispatch", "dispatched"),
        ("dispatched", "acknowledged"),
    ]
    assert audits[-1] == ("CONTROL_ACTUATION_ACKNOWLEDGED_SIMULATED", "acknowledged")


def test_duplicate_recommendation_reuses_command_without_second_dispatch():
    repo = InMemoryIntentRepository()
    consumer = SimulatedActuationConsumer(
        repository=repo,
        audit=lambda *args, **kwargs: None,
        now=lambda: datetime(2026, 8, 11, 0, 1, tzinfo=timezone.utc),
    )
    envelope = recommendation(expires_at="2026-08-11T00:05:00+00:00")

    first = consumer.process(envelope)
    second = consumer.process(envelope)

    assert len(repo.by_key) == 1
    assert first.command_id == second.command_id
    assert second.deduplicated is True
    assert len(repo.transitions) == 4


def test_expired_recommendation_persists_expired_without_dispatch():
    repo = InMemoryIntentRepository()
    consumer = SimulatedActuationConsumer(
        repository=repo,
        audit=lambda *args, **kwargs: None,
        now=lambda: datetime(2026, 8, 11, 0, 6, tzinfo=timezone.utc),
    )

    outcome = consumer.process(recommendation(expires_at="2026-08-11T00:05:00+00:00"))

    assert outcome.status == "expired"
    assert repo.transitions == [("received", "expired")]


def test_legacy_or_invalid_schema_is_skipped_without_intent():
    repo = InMemoryIntentRepository()
    consumer = SimulatedActuationConsumer(repository=repo, audit=lambda *args, **kwargs: None)

    outcome = consumer.process(recommendation(expires_at="2026-08-11T00:05:00+00:00", schema_version="0.1"))

    assert outcome.status == "skipped_legacy"
    assert repo.by_key == {}


def test_simulated_adapter_failure_is_terminal_without_retry_loop():
    class FailingAdapter(SimulatedActuationAdapter):
        def dispatch(self, request, *, attempt=1):
            raise RuntimeError("simulated adapter failure")

    repo = InMemoryIntentRepository()
    consumer = SimulatedActuationConsumer(
        repository=repo,
        adapter=FailingAdapter(),
        audit=lambda *args, **kwargs: None,
        now=lambda: datetime(2026, 8, 11, 0, 1, tzinfo=timezone.utc),
    )

    outcome = consumer.process(recommendation(expires_at="2026-08-11T00:05:00+00:00"))

    assert outcome.status == "failed_final"
    assert repo.transitions[-1] == ("dispatched", "failed_final")


def test_invalid_state_transition_is_rejected():
    repo = InMemoryIntentRepository()
    consumer = SimulatedActuationConsumer(
        repository=repo,
        audit=lambda *args, **kwargs: None,
        now=lambda: datetime(2026, 8, 11, 0, 1, tzinfo=timezone.utc),
    )
    request = consumer.process(recommendation(expires_at="2026-08-11T00:05:00+00:00"))

    with pytest.raises(InvalidDeliveryTransition):
        repo.transition(
            command_id=request.command_id,
            from_statuses={"received"},
            to_status="dispatched",
        )
