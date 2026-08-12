"""Consumer for persisted-outbox simulated dispatch events, with separate downstream DLQ."""

from __future__ import annotations

import json
import time
from typing import Any

from parametric_control_engine.contracts.actuation_contracts import ActuationRequest
from iot_middleware.services.simulated_actuation_consumer import (
    SIMULATED_ACTUATION_DLX, SIMULATED_ACTUATION_DLQ, SIMULATED_ACTUATION_DLQ_ROUTING_KEY,
    SimulatedActuationConsumer, _dead_letter_payload,
)

DISPATCH_QUEUE = "control.actuation.simulated.dispatch.v1"


def declare_dispatch_topology(client: Any) -> bool:
    return bool(client.declare_exchange(SIMULATED_ACTUATION_DLX, exchange_type="direct", durable=True)
        and client.declare_topic_queue(SIMULATED_ACTUATION_DLQ, routing_keys=[SIMULATED_ACTUATION_DLQ_ROUTING_KEY], durable=True, exchange_name=SIMULATED_ACTUATION_DLX)
        and client.declare_topic_queue(DISPATCH_QUEUE, routing_keys=[DISPATCH_QUEUE], durable=True, arguments={"x-dead-letter-exchange": SIMULATED_ACTUATION_DLX, "x-dead-letter-routing-key": SIMULATED_ACTUATION_DLQ_ROUTING_KEY}))


def process_dispatch_message(client: Any, message: dict[str, Any], consumer: SimulatedActuationConsumer) -> str:
    """Terminal downstream failures use the dispatch DLQ, never the outbox."""
    try:
        event = json.loads(message["body"].decode("utf-8"))
        if event.get("message_type") != "control.actuation.simulated.dispatch" or event.get("simulated") is not True or event.get("physical_effects") is not False:
            raise ValueError("invalid_simulated_dispatch_event")
        request = ActuationRequest(**event["payload"])
        intent = consumer.repository.get_by_command_id(request.command_id)
        if intent is None:
            raise ValueError("intent_missing")
        outcome = consumer._dispatch(intent, request, from_statuses={"ready_to_dispatch"})
        if outcome.should_dead_letter:
            if not client.publish_json(routing_key=SIMULATED_ACTUATION_DLQ_ROUTING_KEY, payload=_dead_letter_payload(outcome, message), exchange_name=SIMULATED_ACTUATION_DLX):
                client.nack_message(message["delivery_tag"], requeue=False)
                return "dlq_publish_failed"
            client.ack_message(message["delivery_tag"])
            consumer.audit_dead_lettered(outcome)
            return "dead_lettered"
        if outcome.persistence_failed:
            client.nack_message(message["delivery_tag"], requeue=False)
            return "persistence_failed"
        client.ack_message(message["delivery_tag"])
        return outcome.status
    except Exception:
        client.nack_message(message["delivery_tag"], requeue=False)
        return "invalid"


def main() -> None:
    from iot_middleware.services.control_engine_worker import _load_rabbitmq_client
    client, _ = _load_rabbitmq_client()
    if not declare_dispatch_topology(client):
        raise ConnectionError("Could not declare simulated dispatch topology")
    consumer = SimulatedActuationConsumer(dispatch_immediately=True)
    while True:
        message = client.get_raw_message(DISPATCH_QUEUE, auto_ack=False)
        if message is None:
            time.sleep(1)
            continue
        process_dispatch_message(client, message, consumer)


if __name__ == "__main__":
    main()
