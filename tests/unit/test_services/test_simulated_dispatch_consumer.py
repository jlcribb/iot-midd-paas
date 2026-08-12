import json

from iot_middleware.services.simulated_actuation_consumer import ConsumerOutcome
from iot_middleware.services.simulated_dispatch_consumer import DISPATCH_QUEUE, declare_dispatch_topology, process_dispatch_message


class Client:
    def __init__(self): self.calls = []
    def declare_exchange(self, *args, **kwargs): self.calls.append(("exchange", args, kwargs)); return True
    def declare_topic_queue(self, *args, **kwargs): self.calls.append(("queue", args, kwargs)); return True
    def publish_json(self, **kwargs): self.calls.append(("publish", (), kwargs)); return True
    def ack_message(self, tag): self.calls.append(("ack", (tag,), {})); return True
    def nack_message(self, tag, **kwargs): self.calls.append(("nack", (tag,), kwargs)); return True


class Repository:
    def get_by_command_id(self, command_id): return object()


class Consumer:
    def __init__(self, outcome): self.repository = Repository(); self.outcome = outcome; self.audited = False
    def _dispatch(self, intent, request, **kwargs): return self.outcome
    def audit_dead_lettered(self, outcome): self.audited = True


def message():
    return {"delivery_tag": 7, "routing_key": DISPATCH_QUEUE, "body": json.dumps({
        "message_type": "control.actuation.simulated.dispatch", "schema_version": "1.0", "event_id": "event-1", "simulated": True, "physical_effects": False,
        "payload": {"schema_version": "1.0", "command_id": "00000000-0000-0000-0000-000000000021", "recommendation_id": "recommendation::one", "correlation_id": "corr-1", "project_id": "00000000-0000-0000-0000-000000000001", "policy_id": "policy-1", "policy_version": 1, "source_asset_id": "00000000-0000-0000-0000-000000000011", "target_asset_id": "00000000-0000-0000-0000-000000000012", "target_kind": "simulated", "target_reference": "asset:00000000-0000-0000-0000-000000000012:relay_1", "variable_id": "tank_level", "operation": "set", "requested_value": 1.0, "created_at": "2026-08-12T00:00:00+00:00", "expires_at": "2026-08-12T00:05:00+00:00", "governance_mode": "simulated", "idempotency_key": "actuation::one", "control_point": "relay_1", "actuation_binding_id": "00000000-0000-0000-0000-000000000013", "actuation_binding_version": 1, "simulated": True},
    }).encode()}


def test_dispatch_topology_has_its_own_queue_and_existing_dlq():
    client = Client()
    assert declare_dispatch_topology(client)
    assert any(call[0] == "queue" and call[1][0] == DISPATCH_QUEUE for call in client.calls)


def test_terminal_dispatch_failure_is_dead_lettered_without_outbox_retry():
    client = Client()
    consumer = Consumer(ConsumerOutcome(status="failed_final", command_id="command-1", should_dead_letter=True, error_code="permanent_delivery_error"))
    assert process_dispatch_message(client, message(), consumer) == "dead_lettered"
    assert any(call[0] == "publish" for call in client.calls) and any(call[0] == "ack" for call in client.calls)
    assert not any(call[0] == "nack" for call in client.calls) and consumer.audited


def test_retry_exhausted_dispatch_is_also_dead_lettered_without_outbox_republish():
    client = Client()
    consumer = Consumer(ConsumerOutcome(status="failed_final", command_id="command-1", should_dead_letter=True, error_code="transient_delivery_error"))
    assert process_dispatch_message(client, message(), consumer) == "dead_lettered"
    assert any(call[0] == "publish" for call in client.calls) and any(call[0] == "ack" for call in client.calls)


def test_duplicate_dispatch_is_acknowledged_without_second_adapter_effect():
    client = Client()
    consumer = Consumer(ConsumerOutcome(status="retry_claimed", command_id="command-1", deduplicated=True))
    assert process_dispatch_message(client, message(), consumer) == "retry_claimed"
    assert any(call[0] == "ack" for call in client.calls) and not any(call[0] == "publish" for call in client.calls)
