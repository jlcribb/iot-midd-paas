"""Governed consumer for versioned recommendations and simulated delivery only."""

from __future__ import annotations

import logging
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from parametric_control_engine.contracts.actuation_contracts import (
    ACTUATION_REQUEST_SCHEMA_VERSION,
    CONTROL_RECOMMENDATION_SCHEMA_VERSION,
    SIMULATED_GOVERNANCE_MODE,
    SIMULATED_TARGET_KIND,
    ActuationRequest,
    expires_at_from,
    parse_timestamp,
    stable_idempotency_key,
)

from iot_middleware.services.simulated_actuation_adapter import SimulatedActuationAdapter
from iot_middleware.storage.actuation_delivery_intent_repository import (
    ActuationDeliveryIntentRepository,
    DeliveryIntent,
    InvalidDeliveryTransition,
)
from iot_middleware.storage.db_handler import persist_control_audit_record


logger = logging.getLogger("simulated_actuation_consumer")
logging.basicConfig(
    level=os.getenv("SIMULATED_ACTUATION_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

SIMULATED_RECOMMENDATION_QUEUE = os.getenv(
    "SIMULATED_ACTUATION_RECOMMENDATION_QUEUE", "control.recommendations.simulated.v1"
)
SIMULATED_RECOMMENDATION_ROUTING_KEY = os.getenv(
    "SIMULATED_ACTUATION_RECOMMENDATION_ROUTING_KEY", SIMULATED_RECOMMENDATION_QUEUE
)
POLL_INTERVAL_SECONDS = float(os.getenv("SIMULATED_ACTUATION_POLL_INTERVAL_SECONDS", "1.0"))


class RecommendationCompatibilityError(ValueError):
    """Raised when a message cannot enter the versioned simulated route."""


@dataclass(frozen=True)
class ConsumerOutcome:
    status: str
    command_id: Optional[str] = None
    deduplicated: bool = False
    result: Optional[Dict[str, Any]] = None


def _optional_uuid(value: Any) -> Optional[str]:
    if not value:
        return None
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError) as exc:
        raise RecommendationCompatibilityError("source_asset_id must be a UUID when provided") from exc


def _payload(envelope: Dict[str, Any]) -> Dict[str, Any]:
    if envelope.get("message_type") != "control.recommendation":
        raise RecommendationCompatibilityError("unsupported message_type")
    if envelope.get("schema_version") != CONTROL_RECOMMENDATION_SCHEMA_VERSION:
        raise RecommendationCompatibilityError("legacy or unsupported recommendation schema")
    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        raise RecommendationCompatibilityError("recommendation payload must be an object")
    required = [
        "recommendation_id",
        "correlation_id",
        "project_id",
        "policy_id",
        "policy_version",
        "event_id",
        "variable_id",
        "action_label",
        "command_value",
        "created_at",
        "expires_at",
    ]
    missing = [field for field in required if payload.get(field) in (None, "")]
    if missing:
        raise RecommendationCompatibilityError(f"recommendation missing fields: {missing}")
    return payload


def build_simulated_request(envelope: Dict[str, Any]) -> ActuationRequest:
    payload = _payload(envelope)
    source_asset_id = _optional_uuid(payload.get("source_asset_id"))
    created_at = parse_timestamp(str(payload["created_at"]))
    expires_at = parse_timestamp(str(payload["expires_at"]))
    if expires_at <= created_at:
        raise RecommendationCompatibilityError("expires_at must be after created_at")
    target_reference = f"simulated:{payload.get('actuator_name') or 'control_output'}"
    operation = str(payload["action_label"])
    policy_version = int(payload["policy_version"])
    idempotency_key = stable_idempotency_key(
        project_id=str(payload["project_id"]),
        recommendation_id=str(payload["recommendation_id"]),
        target_kind=SIMULATED_TARGET_KIND,
        target_reference=target_reference,
        operation=operation,
        policy_version=policy_version,
    )
    return ActuationRequest(
        schema_version=ACTUATION_REQUEST_SCHEMA_VERSION,
        command_id=str(uuid.uuid4()),
        recommendation_id=str(payload["recommendation_id"]),
        correlation_id=str(payload["correlation_id"]),
        project_id=str(payload["project_id"]),
        policy_id=str(payload["policy_id"]),
        policy_version=policy_version,
        source_asset_id=source_asset_id,
        target_asset_id=None,
        target_kind=SIMULATED_TARGET_KIND,
        target_reference=target_reference,
        variable_id=str(payload["variable_id"]),
        operation=operation,
        requested_value=float(payload["command_value"]),
        created_at=created_at.isoformat(),
        expires_at=expires_at.isoformat(),
        governance_mode=SIMULATED_GOVERNANCE_MODE,
        idempotency_key=idempotency_key,
        simulated=True,
    )


def _audit_transition(action: str, intent: DeliveryIntent, *, result: Optional[Dict[str, Any]] = None) -> None:
    envelope = {
        "message_type": "control.actuation.audit",
        "schema_version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": intent.status,
        "project_id": intent.project_id,
        "correlation_id": intent.correlation_id,
        "payload": {
            "recommendation_id": intent.recommendation_id,
            "command_id": intent.command_id,
            "correlation_id": intent.correlation_id,
            "project_id": intent.project_id,
            "policy_id": intent.policy_id,
            "policy_version": intent.policy_version,
            "source_asset_id": intent.source_asset_id,
            "target_kind": intent.target_kind,
            "target_reference": intent.target_reference,
            "status": intent.status,
            "simulated": intent.simulated,
            "result": result,
        },
    }
    persist_control_audit_record(envelope, action=action, entity="simulated_actuation_consumer")


class SimulatedActuationConsumer:
    def __init__(
        self,
        repository: Optional[ActuationDeliveryIntentRepository] = None,
        adapter: Optional[SimulatedActuationAdapter] = None,
        audit: Callable[..., None] = _audit_transition,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self.repository = repository or ActuationDeliveryIntentRepository()
        self.adapter = adapter or SimulatedActuationAdapter()
        self.audit = audit
        self.now = now

    def process(self, envelope: Dict[str, Any]) -> ConsumerOutcome:
        try:
            request = build_simulated_request(envelope)
        except RecommendationCompatibilityError as exc:
            logger.warning("[SIMULATED_ACTUATION] skipped incompatible recommendation: %s", exc)
            return ConsumerOutcome(status="skipped_legacy")

        intent, created = self.repository.create_or_get(request)
        if not created:
            self.audit("CONTROL_ACTUATION_INTENT_REUSED", intent)
            return ConsumerOutcome(status=intent.status, command_id=intent.command_id, deduplicated=True)

        self.audit("CONTROL_ACTUATION_INTENT_CREATED", intent)
        if parse_timestamp(request.expires_at) <= self.now().astimezone(timezone.utc):
            intent = self.repository.transition(
                command_id=intent.command_id,
                from_statuses={"received"},
                to_status="expired",
            )
            self.audit("CONTROL_ACTUATION_EXPIRED", intent)
            return ConsumerOutcome(status="expired", command_id=intent.command_id)

        try:
            self.adapter.validate_target(request)
        except Exception as exc:
            intent = self.repository.transition(
                command_id=intent.command_id,
                from_statuses={"received"},
                to_status="rejected",
                last_error=str(exc),
            )
            self.audit("CONTROL_ACTUATION_REJECTED", intent)
            return ConsumerOutcome(status="rejected", command_id=intent.command_id)

        intent = self.repository.transition(
            command_id=intent.command_id,
            from_statuses={"received"},
            to_status="validated",
        )
        self.audit("CONTROL_ACTUATION_VALIDATED", intent)
        intent = self.repository.transition(
            command_id=intent.command_id,
            from_statuses={"validated"},
            to_status="ready_to_dispatch",
        )
        self.audit("CONTROL_ACTUATION_READY_TO_DISPATCH", intent)
        intent = self.repository.transition(
            command_id=intent.command_id,
            from_statuses={"ready_to_dispatch"},
            to_status="dispatched",
        )
        self.audit("CONTROL_ACTUATION_DISPATCHED_SIMULATED", intent)

        try:
            result = self.adapter.dispatch(request)
            intent = self.repository.transition(
                command_id=intent.command_id,
                from_statuses={"dispatched"},
                to_status="acknowledged",
            )
            normalized = self.adapter.normalize_result(result)
            self.audit("CONTROL_ACTUATION_ACKNOWLEDGED_SIMULATED", intent, result=normalized)
            return ConsumerOutcome(status="acknowledged", command_id=intent.command_id, result=normalized)
        except Exception as exc:
            intent = self.repository.transition(
                command_id=intent.command_id,
                from_statuses={"dispatched"},
                to_status="failed_final",
                last_error=str(exc),
            )
            self.audit("CONTROL_ACTUATION_FAILED_SIMULATED", intent)
            return ConsumerOutcome(status="failed_final", command_id=intent.command_id)


def _rabbitmq_client():
    """Reuse the existing runtime RabbitMQ configuration and reconnect logic."""
    from iot_middleware.services.control_engine_worker import _load_rabbitmq_client

    client, _ = _load_rabbitmq_client()
    return client


def consume_simulated_recommendations(
    *,
    max_messages: Optional[int] = None,
    idle_timeout_seconds: Optional[float] = None,
) -> int:
    client = _rabbitmq_client()
    if not client.declare_topic_queue(
        queue_name=SIMULATED_RECOMMENDATION_QUEUE,
        routing_keys=[SIMULATED_RECOMMENDATION_ROUTING_KEY],
        durable=True,
    ):
        raise ConnectionError("Could not declare simulated actuation recommendation queue")
    consumer = SimulatedActuationConsumer()
    processed = 0
    idle_started = time.monotonic()
    while True:
        message = client.get_json_message(SIMULATED_RECOMMENDATION_QUEUE, auto_ack=False)
        if message is None:
            if idle_timeout_seconds is not None and time.monotonic() - idle_started >= idle_timeout_seconds:
                return processed
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        idle_started = time.monotonic()
        try:
            consumer.process(message["payload"])
        finally:
            client.ack_message(message["delivery_tag"])
        processed += 1
        if max_messages is not None and processed >= max_messages:
            return processed


def main() -> None:
    logger.info(
        "Simulated Actuation Consumer started queue=%s routing_key=%s",
        SIMULATED_RECOMMENDATION_QUEUE,
        SIMULATED_RECOMMENDATION_ROUTING_KEY,
    )
    consume_simulated_recommendations()


if __name__ == "__main__":  # pragma: no cover
    main()
