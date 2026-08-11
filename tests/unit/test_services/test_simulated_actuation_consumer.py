from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from iot_middleware.services.simulated_actuation_adapter import SimulatedActuationAdapter
from iot_middleware.services.simulated_actuation_consumer import (
    ConsumerMetrics,
    SimulatedActuationConsumer,
    declare_simulated_delivery_topology,
)
from iot_middleware.storage.actuation_delivery_intent_repository import DeliveryIntent, InvalidDeliveryTransition, VALID_TRANSITIONS
from iot_middleware.storage.policy_actuation_binding_repository import PolicyActuationBinding


PROJECT_ID = "00000000-0000-0000-0000-000000000001"
SOURCE_ASSET_ID = "00000000-0000-0000-0000-000000000011"
TARGET_ASSET_ID = "00000000-0000-0000-0000-000000000012"
BINDING_ID = "00000000-0000-0000-0000-000000000013"


class InMemoryBindingRepository:
    def __init__(self, binding=None):
        self.binding = binding or PolicyActuationBinding(
            id=BINDING_ID, policy_id="policy-test-1", project_id=PROJECT_ID,
            source_asset_id=SOURCE_ASSET_ID, target_asset_id=TARGET_ASSET_ID,
            control_point="relay_1", operation="increase", version=1,
            target_asset_type="actuator",
            target_metadata={"control_capabilities": [{"key": "relay_1", "operations": ["increase"]}]},
        )

    def get_active(self, policy_id):
        return self.binding if self.binding and policy_id == self.binding.policy_id else None

    @staticmethod
    def supports(binding):
        return binding.target_asset_type == "actuator"


class InMemoryIntentRepository:
    def __init__(self):
        self.by_key = {}
        self.transitions = []

    def create_or_get(self, request):
        existing = self.by_key.get(request.idempotency_key)
        if existing:
            return existing, False
        intent = DeliveryIntent(
            id="00000000-0000-0000-0000-000000000031", command_id=request.command_id,
            recommendation_id=request.recommendation_id, correlation_id=request.correlation_id,
            project_id=request.project_id, policy_id=request.policy_id, policy_version=request.policy_version,
            source_asset_id=request.source_asset_id, target_asset_id=request.target_asset_id,
            target_kind=request.target_kind, target_reference=request.target_reference,
            control_point=request.control_point, actuation_binding_id=request.actuation_binding_id,
            actuation_binding_version=request.actuation_binding_version,
            variable_id=request.variable_id, operation=request.operation, requested_value=request.requested_value,
            idempotency_key=request.idempotency_key, governance_mode=request.governance_mode,
            status="received", retry_count=0, last_attempt_at=None, next_retry_at=None,
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
            expires_at=datetime.fromisoformat(request.expires_at), last_error=None, simulated=True,
        )
        self.by_key[request.idempotency_key] = intent
        return intent, True

    def transition(self, *, command_id, from_statuses, to_status, last_error=None, increment_retry_count=False, next_retry_at=None, record_attempt=False):
        intent = next(item for item in self.by_key.values() if item.command_id == command_id)
        if intent.status not in from_statuses or to_status not in VALID_TRANSITIONS[intent.status]:
            raise InvalidDeliveryTransition(f"{intent.status} -> {to_status}")
        transitioned = replace(
            intent, status=to_status, last_error=last_error, next_retry_at=next_retry_at,
            retry_count=intent.retry_count + int(increment_retry_count),
            last_attempt_at=datetime.now(timezone.utc) if record_attempt else intent.last_attempt_at,
            updated_at=datetime.now(timezone.utc),
        )
        self.by_key[intent.idempotency_key] = transitioned
        self.transitions.append((intent.status, to_status))
        return transitioned

    def get_due_retries(self, *, now, limit):
        return [
            intent for intent in self.by_key.values()
            if intent.status == "retry_pending" and intent.next_retry_at <= now
        ][:limit]

    def prepare_dispatch_with_outbox(self, request):
        intent = next(item for item in self.by_key.values() if item.command_id == request.command_id)
        intent = self.transition(command_id=intent.command_id, from_statuses={"received"}, to_status="validated")
        intent = self.transition(command_id=intent.command_id, from_statuses={"validated"}, to_status="ready_to_dispatch")
        return intent, type("Event", (), {"event_id": "00000000-0000-0000-0000-000000000014"})()


def recommendation(*, expires_at: str, schema_version: str = "1.0", actuation_binding=True):
    return {
        "message_type": "control.recommendation", "schema_version": schema_version,
        "payload": {
            "recommendation_id": "recommendation::test-1", "correlation_id": "corr-test-1",
            "project_id": PROJECT_ID, "policy_id": "policy-test-1", "policy_version": 2,
            "event_id": "evt-test-1", "variable_id": "tank_level", "action_label": "increase",
            "command_value": 3.5, "actuator_name": "pump", "source_asset_id": SOURCE_ASSET_ID,
            "created_at": "2026-08-11T00:00:00+00:00", "expires_at": expires_at,
            **({"actuation_binding": {
                "binding_id": BINDING_ID, "target_asset_id": TARGET_ASSET_ID,
                "control_point": "relay_1", "operation": "increase", "version": 1,
            }} if actuation_binding else {}),
        },
    }


def consumer(repo, *, adapter=None, binding_repo=None, now=None, audits=None, max_attempts=3):
    return SimulatedActuationConsumer(
        repository=repo, adapter=adapter, binding_repository=binding_repo or InMemoryBindingRepository(), now=now or (lambda: datetime(2026, 8, 11, 0, 1, tzinfo=timezone.utc)),
        audit=lambda action, intent, **kwargs: (audits if audits is not None else []).append((action, intent.status, intent.retry_count)),
        metrics=ConsumerMetrics(), max_retry_attempts=max_attempts, retry_base_delay_seconds=1, retry_jitter_seconds=0,
    )


def test_valid_recommendation_creates_one_acknowledged_simulated_intent():
    repo, audits = InMemoryIntentRepository(), []
    outcome = consumer(repo, audits=audits).process(recommendation(expires_at="2026-08-11T00:05:00+00:00"))
    assert outcome.status == "acknowledged"
    assert outcome.result["simulated"] is True
    assert len(repo.by_key) == 1
    assert repo.transitions == [("received", "validated"), ("validated", "ready_to_dispatch"), ("ready_to_dispatch", "dispatched"), ("dispatched", "acknowledged")]
    assert audits[-1][:2] == ("CONTROL_ACTUATION_ACKNOWLEDGED_SIMULATED", "acknowledged")


def test_transient_failure_retries_with_stable_command_and_acknowledges():
    repo, audits = InMemoryIntentRepository(), []
    current = [datetime(2026, 8, 11, 0, 1, tzinfo=timezone.utc)]
    subject = consumer(
        repo, audits=audits, now=lambda: current[0],
        adapter=SimulatedActuationAdapter(test_failure_plan=("transient",)),
    )
    first = subject.process(recommendation(expires_at="2026-08-11T00:05:00+00:00"))
    intent = next(iter(repo.by_key.values()))
    assert first.status == "retry_pending"
    assert intent.retry_count == 1
    command_id = intent.command_id
    current[0] = intent.next_retry_at + timedelta(milliseconds=1)
    outcomes = subject.process_due_retries()
    final = next(iter(repo.by_key.values()))
    assert outcomes[0].status == "acknowledged"
    assert final.command_id == command_id
    assert final.retry_count == 2
    assert final.status == "acknowledged"
    assert ("dispatched", "retry_pending") in repo.transitions
    assert ("retry_pending", "dispatched") in repo.transitions
    assert any(action == "CONTROL_ACTUATION_RETRY_SCHEDULED" for action, *_ in audits)


def test_retry_exhaustion_is_terminal_and_requires_dead_letter():
    repo = InMemoryIntentRepository()
    current = [datetime(2026, 8, 11, 0, 1, tzinfo=timezone.utc)]
    subject = consumer(repo, now=lambda: current[0], adapter=SimulatedActuationAdapter(test_failure_plan=("transient", "transient", "transient")), max_attempts=3)
    outcome = subject.process(recommendation(expires_at="2026-08-11T00:05:00+00:00"))
    for _ in range(2):
        intent = next(iter(repo.by_key.values()))
        current[0] = intent.next_retry_at + timedelta(milliseconds=1)
        outcome = subject.process_due_retries()[0]
    intent = next(iter(repo.by_key.values()))
    assert outcome.status == "failed_final"
    assert outcome.should_dead_letter is True
    assert intent.retry_count == 3
    assert intent.status == "failed_final"


def test_permanent_failure_is_terminal_without_retry():
    repo = InMemoryIntentRepository()
    subject = consumer(repo, adapter=SimulatedActuationAdapter(test_failure_plan=("permanent",)))
    outcome = subject.process(recommendation(expires_at="2026-08-11T00:05:00+00:00"))
    intent = next(iter(repo.by_key.values()))
    assert outcome.status == "failed_final"
    assert outcome.should_dead_letter is True
    assert intent.retry_count == 1
    assert "retry_pending" not in [status for _, status in repo.transitions]


def test_expired_recommendation_is_terminal_without_dead_letter_or_dispatch():
    repo = InMemoryIntentRepository()
    outcome = consumer(repo, now=lambda: datetime(2026, 8, 11, 0, 6, tzinfo=timezone.utc)).process(recommendation(expires_at="2026-08-11T00:05:00+00:00"))
    assert outcome.status == "expired"
    assert outcome.should_dead_letter is False
    assert repo.transitions == [("received", "expired")]


def test_legacy_or_invalid_schema_is_quarantined_without_creating_intent():
    repo = InMemoryIntentRepository()
    outcome = consumer(repo).process(recommendation(expires_at="2026-08-11T00:05:00+00:00", schema_version="0.1"))
    assert outcome.status == "rejected"
    assert outcome.should_dead_letter is True
    assert outcome.error_code == "invalid_recommendation"
    assert repo.by_key == {}


def test_recommendation_without_governed_target_is_audited_without_intent_or_dead_letter():
    repo = InMemoryIntentRepository()
    outcome = consumer(repo).process(recommendation(expires_at="2026-08-11T00:05:00+00:00", actuation_binding=False))
    assert outcome.status == "recommendation_only"
    assert outcome.should_dead_letter is False
    assert repo.by_key == {}


def test_stale_target_binding_is_quarantined_without_creating_intent():
    repo = InMemoryIntentRepository()
    binding = InMemoryBindingRepository().binding
    stale = replace(binding, version=2)
    outcome = consumer(repo, binding_repo=InMemoryBindingRepository(stale)).process(recommendation(expires_at="2026-08-11T00:05:00+00:00"))
    assert outcome.status == "rejected"
    assert outcome.error_code == "invalid_target"
    assert outcome.should_dead_letter is True
    assert repo.by_key == {}


def test_duplicate_while_retry_pending_reuses_intent_without_parallel_dispatch():
    repo = InMemoryIntentRepository()
    current = [datetime(2026, 8, 11, 0, 1, tzinfo=timezone.utc)]
    subject = consumer(repo, now=lambda: current[0], adapter=SimulatedActuationAdapter(test_failure_plan=("transient",)))
    first = subject.process(recommendation(expires_at="2026-08-11T00:05:00+00:00"))
    duplicate = subject.process(recommendation(expires_at="2026-08-11T00:05:00+00:00"))
    intent = next(iter(repo.by_key.values()))
    assert first.status == "retry_pending"
    assert duplicate.deduplicated is True
    assert duplicate.command_id == intent.command_id
    assert intent.retry_count == 1
    assert repo.transitions.count(("retry_pending", "dispatched")) == 0


def test_invalid_state_transition_is_rejected():
    repo = InMemoryIntentRepository()
    outcome = consumer(repo).process(recommendation(expires_at="2026-08-11T00:05:00+00:00"))
    with pytest.raises(InvalidDeliveryTransition):
        repo.transition(command_id=outcome.command_id, from_statuses={"received"}, to_status="dispatched")


def test_simulated_delivery_topology_is_scoped_to_its_own_dlx_and_dlq():
    calls = []

    class Client:
        def declare_exchange(self, *args, **kwargs):
            calls.append(("exchange", args, kwargs))
            return True

        def declare_topic_queue(self, *args, **kwargs):
            calls.append(("queue", args, kwargs))
            return True

    assert declare_simulated_delivery_topology(Client()) is True
    assert calls[0][0] == "exchange"
    assert calls[0][1][0] == "control.actuation.simulated.dlx"
    assert calls[1][1][0] == "control.actuation.simulated.dlq.v1"
    assert calls[2][1][0] == "control.recommendations.simulated.v1"
    assert calls[2][2]["arguments"]["x-dead-letter-exchange"] == "control.actuation.simulated.dlx"
