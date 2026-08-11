#!/usr/bin/env python3
"""Run safe RabbitMQ/PostgreSQL E2E checks for simulated delivery reliability.

This smoke only creates simulated intents and a quarantined DLQ message. It
never emits MQTT commands and never consumes legacy recommendation queues.
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from iot_middleware.services.simulated_actuation_adapter import SimulatedActuationAdapter
from iot_middleware.services.simulated_actuation_consumer import (
    SIMULATED_ACTUATION_DLX,
    SIMULATED_ACTUATION_DLQ,
    SIMULATED_ACTUATION_DLQ_ROUTING_KEY,
    SIMULATED_RECOMMENDATION_QUEUE,
    SIMULATED_RECOMMENDATION_ROUTING_KEY,
    SimulatedActuationConsumer,
    _dead_letter_payload,
    _rabbitmq_client,
    declare_simulated_delivery_topology,
)
from iot_middleware.storage.actuation_delivery_intent_repository import ActuationDeliveryIntentRepository


def envelope(project_id: str, suffix: str) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "message_type": "control.recommendation",
        "schema_version": "1.0",
        "payload": {
            "recommendation_id": f"recommendation::delivery-smoke::{suffix}",
            "correlation_id": f"delivery-smoke::{suffix}",
            "project_id": project_id,
            "policy_id": "delivery-smoke-policy",
            "policy_version": 1,
            "event_id": f"delivery-smoke-event::{suffix}",
            "variable_id": "delivery_smoke_variable",
            "action_label": "simulate",
            "command_value": 1.0,
            "actuator_name": "delivery-smoke",
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=5)).isoformat(),
        },
    }


def queue_depth(client, queue_name: str) -> int:
    return client.channel.queue_declare(queue=queue_name, passive=True).method.message_count


def consume_one(client, consumer: SimulatedActuationConsumer):
    message = client.get_raw_message(SIMULATED_RECOMMENDATION_QUEUE, auto_ack=False)
    if message is None:
        raise RuntimeError("expected simulated recommendation was not present")
    outcome = consumer.process(json.loads(message["body"].decode("utf-8")))
    if outcome.should_dead_letter:
        if not client.publish_json(
            routing_key=SIMULATED_ACTUATION_DLQ_ROUTING_KEY,
            payload=_dead_letter_payload(outcome, message),
            exchange_name=SIMULATED_ACTUATION_DLX,
        ):
            raise RuntimeError("could not publish E2E terminal failure to DLQ")
        consumer.audit_dead_lettered(outcome)
    if not client.ack_message(message["delivery_tag"]):
        raise RuntimeError("could not ACK E2E simulated recommendation")
    return outcome


def route_scheduled_dead_letter(client, consumer, outcome) -> None:
    if not outcome.should_dead_letter:
        return
    if not client.publish_json(
        routing_key=SIMULATED_ACTUATION_DLQ_ROUTING_KEY,
        payload=_dead_letter_payload(outcome, {"routing_key": SIMULATED_RECOMMENDATION_ROUTING_KEY}),
        exchange_name=SIMULATED_ACTUATION_DLX,
    ):
        raise RuntimeError("could not publish exhausted retry to DLQ")
    consumer.audit_dead_lettered(outcome)


def run_case(client, project_id: str, failure_plan: tuple[str, ...], expected: str):
    repository = ActuationDeliveryIntentRepository()
    consumer = SimulatedActuationConsumer(
        repository=repository,
        adapter=SimulatedActuationAdapter(test_failure_plan=failure_plan),
        retry_base_delay_seconds=0,
        retry_max_delay_seconds=0,
        retry_jitter_seconds=0,
    )
    payload = envelope(project_id, str(uuid.uuid4()))
    if not client.publish_json(
        routing_key=SIMULATED_RECOMMENDATION_ROUTING_KEY,
        payload=payload,
    ):
        raise RuntimeError("could not publish E2E simulated recommendation")
    outcome = consume_one(client, consumer)
    while outcome.status == "retry_pending":
        due = consumer.process_due_retries(limit=1)
        if not due:
            raise RuntimeError("retry was not due")
        outcome = due[0]
        route_scheduled_dead_letter(client, consumer, outcome)
    if outcome.status != expected:
        raise RuntimeError(f"expected {expected}, got {outcome.status}")
    intent = repository.get_by_command_id(outcome.command_id)
    if intent is None:
        raise RuntimeError("E2E intent was not persisted")
    return outcome, intent


def main() -> int:
    client = _rabbitmq_client()
    if not declare_simulated_delivery_topology(client):
        raise RuntimeError("could not declare simulated delivery topology")
    repository = ActuationDeliveryIntentRepository()
    with repository._engine.connect() as connection:  # smoke-only lookup; no data is changed here
        project_id = str(connection.execute(text("SELECT id FROM public.projects ORDER BY id LIMIT 1")).scalar_one())
    before_dlq = queue_depth(client, SIMULATED_ACTUATION_DLQ)
    transient, transient_intent = run_case(client, project_id, ("transient",), "acknowledged")
    exhausted, exhausted_intent = run_case(client, project_id, ("transient", "transient", "transient"), "failed_final")
    after_dlq = queue_depth(client, SIMULATED_ACTUATION_DLQ)
    if transient_intent.retry_count != 2 or exhausted_intent.retry_count != 3:
        raise RuntimeError("unexpected persisted retry counts")
    if after_dlq != before_dlq + 1:
        raise RuntimeError("exactly one exhausted retry should be quarantined")
    if queue_depth(client, SIMULATED_RECOMMENDATION_QUEUE) != 0:
        raise RuntimeError("simulated delivery queue was not drained")
    print(
        "SIMULATED_DELIVERY_E2E_PASS "
        f"transient_command={transient.command_id} transient_attempts={transient_intent.retry_count} "
        f"exhausted_command={exhausted.command_id} exhausted_attempts={exhausted_intent.retry_count} "
        f"dlq_before={before_dlq} dlq_after={after_dlq}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"SIMULATED_DELIVERY_E2E_FAIL error={type(exc).__name__}", file=sys.stderr)
        raise
