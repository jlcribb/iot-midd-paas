"""Bounded, auditable delivery of versioned recommendations to a simulated target.

This boundary never emits physical commands.  RabbitMQ is used only to receive
versioned recommendations and quarantine terminal delivery failures.
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional

from parametric_control_engine.contracts.actuation_contracts import (
    ACTUATION_REQUEST_SCHEMA_VERSION,
    CONTROL_RECOMMENDATION_SCHEMA_VERSION,
    SIMULATED_GOVERNANCE_MODE,
    SIMULATED_TARGET_KIND,
    ActuationRequest,
    parse_timestamp,
    stable_idempotency_key,
)

from iot_middleware.services.simulated_actuation_adapter import SimulatedActuationAdapter
from iot_middleware.storage.actuation_delivery_intent_repository import (
    ActuationDeliveryIntentRepository,
    DeliveryIntent,
    InvalidDeliveryTransition,
)
from iot_middleware.storage.policy_actuation_binding_repository import PolicyActuationBindingRepository
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
SIMULATED_ACTUATION_DLX = os.getenv("SIMULATED_ACTUATION_DLX", "control.actuation.simulated.dlx")
SIMULATED_ACTUATION_DLQ = os.getenv("SIMULATED_ACTUATION_DLQ", "control.actuation.simulated.dlq.v1")
SIMULATED_ACTUATION_DLQ_ROUTING_KEY = os.getenv(
    "SIMULATED_ACTUATION_DLQ_ROUTING_KEY", SIMULATED_ACTUATION_DLQ
)
MAX_RETRY_ATTEMPTS = max(1, int(os.getenv("SIMULATED_ACTUATION_MAX_RETRY_ATTEMPTS", "3")))
RETRY_BASE_DELAY_SECONDS = max(0.0, float(os.getenv("SIMULATED_ACTUATION_RETRY_BASE_DELAY_SECONDS", "1")))
RETRY_MAX_DELAY_SECONDS = max(RETRY_BASE_DELAY_SECONDS, float(os.getenv("SIMULATED_ACTUATION_RETRY_MAX_DELAY_SECONDS", "30")))
RETRY_JITTER_SECONDS = max(0.0, float(os.getenv("SIMULATED_ACTUATION_RETRY_JITTER_SECONDS", "0")))
POLL_INTERVAL_SECONDS = float(os.getenv("SIMULATED_ACTUATION_POLL_INTERVAL_SECONDS", "1.0"))


class DeliveryError(Exception):
    """Explicit delivery taxonomy; classification never depends on exception text."""

    code = "delivery_error"
    retryable = False


class InvalidRecommendationError(DeliveryError):
    code = "invalid_recommendation"


class InvalidTargetError(DeliveryError):
    code = "invalid_target"


class ExpiredRecommendationError(DeliveryError):
    code = "recommendation_expired"


class TransientDeliveryError(DeliveryError):
    code = "transient_delivery_error"
    retryable = True


class PermanentDeliveryError(DeliveryError):
    code = "permanent_delivery_error"


class PersistenceDeliveryError(DeliveryError):
    code = "persistence_delivery_error"
    retryable = True


class RecommendationOnlyDelivery(Exception):
    """A valid recommendation without an opted-in target binding is not dispatchable."""


def classify_delivery_error(error: Exception) -> DeliveryError:
    if isinstance(error, DeliveryError):
        return error
    if isinstance(error, (TimeoutError, ConnectionError, OSError)):
        return TransientDeliveryError(str(error))
    return PermanentDeliveryError(str(error))


@dataclass(frozen=True)
class ConsumerOutcome:
    status: str
    command_id: Optional[str] = None
    deduplicated: bool = False
    result: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    should_dead_letter: bool = False
    persistence_failed: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConsumerMetrics:
    recommendations_received: int = 0
    valid: int = 0
    invalid: int = 0
    duplicate: int = 0
    expired: int = 0
    dispatch_success: int = 0
    dispatch_retry: int = 0
    dispatch_failed: int = 0
    dead_lettered: int = 0
    intents_created: int = 0
    intents_reused: int = 0
    audit_failures: int = 0

    def snapshot(self) -> Dict[str, int]:
        return self.__dict__.copy()


def _optional_uuid(value: Any) -> Optional[str]:
    if not value:
        return None
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError) as exc:
        raise InvalidRecommendationError("source_asset_id must be a UUID when provided") from exc


def _payload(envelope: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(envelope, dict) or envelope.get("message_type") != "control.recommendation":
        raise InvalidRecommendationError("unsupported message_type")
    if envelope.get("schema_version") != CONTROL_RECOMMENDATION_SCHEMA_VERSION:
        raise InvalidRecommendationError("legacy or unsupported recommendation schema")
    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        raise InvalidRecommendationError("recommendation payload must be an object")
    required = (
        "recommendation_id", "correlation_id", "project_id", "policy_id", "policy_version",
        "event_id", "variable_id", "action_label", "command_value", "created_at", "expires_at",
    )
    missing = [field for field in required if payload.get(field) in (None, "")]
    if missing:
        raise InvalidRecommendationError(f"recommendation missing fields: {missing}")
    return payload


def build_simulated_request(envelope: Dict[str, Any]) -> ActuationRequest:
    try:
        payload = _payload(envelope)
        source_asset_id = _optional_uuid(payload.get("source_asset_id"))
        created_at = parse_timestamp(str(payload["created_at"]))
        expires_at = parse_timestamp(str(payload["expires_at"]))
        if expires_at <= created_at:
            raise InvalidRecommendationError("expires_at must be after created_at")
        operation = str(payload["action_label"])
        policy_version = int(payload["policy_version"])
        target_binding = payload.get("actuation_binding")
        if target_binding is None:
            raise RecommendationOnlyDelivery()
        if not isinstance(target_binding, dict):
            raise InvalidRecommendationError("actuation_binding must be an object")
        target_asset_id = str(uuid.UUID(str(target_binding["target_asset_id"])))
        binding_id = str(uuid.UUID(str(target_binding["binding_id"])))
        control_point = str(target_binding["control_point"]).strip()
        operation = str(target_binding["operation"]).strip()
        binding_version = int(target_binding["version"])
        if not control_point or operation not in {"set", "increase", "decrease", "toggle"} or binding_version < 1:
            raise InvalidRecommendationError("invalid actuation_binding fields")
        idempotency_key = stable_idempotency_key(
            project_id=str(payload["project_id"]), recommendation_id=str(payload["recommendation_id"]),
            target_kind=SIMULATED_TARGET_KIND, target_reference=f"asset:{target_asset_id}:{control_point}",
            operation=operation, policy_version=policy_version, target_asset_id=target_asset_id,
            control_point=control_point, binding_version=binding_version,
        )
    except DeliveryError:
        raise
    except (TypeError, ValueError) as exc:
        raise InvalidRecommendationError("invalid versioned recommendation fields") from exc
    return ActuationRequest(
        schema_version=ACTUATION_REQUEST_SCHEMA_VERSION,
        command_id=str(uuid.uuid4()), recommendation_id=str(payload["recommendation_id"]),
        correlation_id=str(payload["correlation_id"]), project_id=str(payload["project_id"]),
        policy_id=str(payload["policy_id"]), policy_version=policy_version,
        source_asset_id=source_asset_id, target_kind=SIMULATED_TARGET_KIND,
        target_reference=f"asset:{target_asset_id}:{control_point}", variable_id=str(payload["variable_id"]), operation=operation,
        requested_value=float(payload["command_value"]), created_at=created_at.isoformat(),
        expires_at=expires_at.isoformat(), governance_mode=SIMULATED_GOVERNANCE_MODE,
        idempotency_key=idempotency_key, control_point=control_point,
        actuation_binding_id=binding_id, actuation_binding_version=binding_version,
        target_asset_id=target_asset_id, simulated=True,
    )


def request_from_intent(intent: DeliveryIntent) -> ActuationRequest:
    """Rebuild the immutable request from persisted data for a scheduled retry."""
    return ActuationRequest(
        schema_version=ACTUATION_REQUEST_SCHEMA_VERSION, command_id=intent.command_id,
        recommendation_id=intent.recommendation_id, correlation_id=intent.correlation_id,
        project_id=intent.project_id, policy_id=intent.policy_id, policy_version=intent.policy_version,
        source_asset_id=intent.source_asset_id, target_asset_id=intent.target_asset_id,
        target_kind=intent.target_kind, target_reference=intent.target_reference,
        variable_id=intent.variable_id, operation=intent.operation, requested_value=intent.requested_value,
        created_at=intent.created_at.astimezone(timezone.utc).isoformat(),
        expires_at=intent.expires_at.astimezone(timezone.utc).isoformat(),
        governance_mode=intent.governance_mode, idempotency_key=intent.idempotency_key,
        control_point=intent.control_point, actuation_binding_id=intent.actuation_binding_id,
        actuation_binding_version=intent.actuation_binding_version,
        simulated=intent.simulated,
    )


def _audit_transition(action: str, intent: DeliveryIntent, *, result: Optional[Dict[str, Any]] = None) -> None:
    envelope = {
        "message_type": "control.actuation.audit", "schema_version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(), "status": intent.status,
        "project_id": intent.project_id, "correlation_id": intent.correlation_id,
        "payload": {
            "recommendation_id": intent.recommendation_id, "command_id": intent.command_id,
            "correlation_id": intent.correlation_id, "project_id": intent.project_id,
            "policy_id": intent.policy_id, "policy_version": intent.policy_version,
            "source_asset_id": intent.source_asset_id, "target_kind": intent.target_kind,
            "target_asset_id": intent.target_asset_id, "target_reference": intent.target_reference,
            "control_point": intent.control_point, "actuation_binding_id": intent.actuation_binding_id,
            "actuation_binding_version": intent.actuation_binding_version, "status": intent.status,
            "attempt": intent.retry_count, "next_retry_at": intent.next_retry_at.isoformat() if intent.next_retry_at else None,
            "simulated": intent.simulated, "result": result,
        },
    }
    persist_control_audit_record(envelope, action=action, entity="simulated_actuation_consumer")


class SimulatedActuationConsumer:
    def __init__(
        self,
        repository: Optional[ActuationDeliveryIntentRepository] = None,
        adapter: Optional[SimulatedActuationAdapter] = None,
        binding_repository: Optional[PolicyActuationBindingRepository] = None,
        audit: Callable[..., None] = _audit_transition,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        metrics: Optional[ConsumerMetrics] = None,
        max_retry_attempts: int = MAX_RETRY_ATTEMPTS,
        retry_base_delay_seconds: float = RETRY_BASE_DELAY_SECONDS,
        retry_max_delay_seconds: float = RETRY_MAX_DELAY_SECONDS,
        retry_jitter_seconds: float = RETRY_JITTER_SECONDS,
        jitter: Callable[[float, float], float] = random.uniform,
    ) -> None:
        self.repository = repository or ActuationDeliveryIntentRepository()
        self.adapter = adapter or SimulatedActuationAdapter()
        self.binding_repository = binding_repository or PolicyActuationBindingRepository()
        self.audit = audit
        self.now = now
        self.metrics = metrics or ConsumerMetrics()
        self.max_retry_attempts = max(1, max_retry_attempts)
        self.retry_base_delay_seconds = max(0.0, retry_base_delay_seconds)
        self.retry_max_delay_seconds = max(self.retry_base_delay_seconds, retry_max_delay_seconds)
        self.retry_jitter_seconds = max(0.0, retry_jitter_seconds)
        self.jitter = jitter

    def _now(self) -> datetime:
        return self.now().astimezone(timezone.utc)

    def _audit(self, action: str, intent: DeliveryIntent, *, result: Optional[Dict[str, Any]] = None) -> None:
        try:
            self.audit(action, intent, result=result)
        except Exception as exc:  # audit is deliberately best-effort, never a dispatch decision
            self.metrics.audit_failures += 1
            logger.error("event=audit_failed action=%s command_id=%s error_type=%s", action, intent.command_id, type(exc).__name__)

    def _audit_invalid(self, envelope: Any, error_code: str, *, action: str = "CONTROL_ACTUATION_INVALID_RECOMMENDATION") -> None:
        """Audit malformed input without retaining its complete untrusted payload."""
        payload = envelope.get("payload") if isinstance(envelope, dict) else {}
        payload = payload if isinstance(payload, dict) else {}
        safe_payload = {
            key: payload.get(key)
            for key in ("recommendation_id", "correlation_id", "project_id")
            if payload.get(key) is not None
        }
        try:
            result = persist_control_audit_record(
                {
                    "message_type": "control.actuation.audit", "schema_version": "1.0",
                    "timestamp": self._now().isoformat(), "status": "rejected",
                    "project_id": safe_payload.get("project_id"),
                    "correlation_id": safe_payload.get("correlation_id"),
                    "payload": {**safe_payload, "status": "rejected", "error_code": error_code, "simulated": True},
                },
                action=action,
                entity="simulated_actuation_consumer",
            )
            if result.get("status") != "persisted":
                raise RuntimeError("audit persistence returned failure")
        except Exception as exc:
            self.metrics.audit_failures += 1
            logger.error("event=audit_failed action=%s error_type=%s", action, type(exc).__name__)

    def _validate_target_binding(self, request: ActuationRequest) -> None:
        binding = self.binding_repository.get_active(request.policy_id)
        if not binding:
            raise InvalidTargetError("active actuation binding no longer exists")
        if (
            binding.id != request.actuation_binding_id
            or binding.version != request.actuation_binding_version
            or binding.project_id != request.project_id
            or binding.source_asset_id != request.source_asset_id
            or binding.target_asset_id != request.target_asset_id
            or binding.control_point != request.control_point
            or binding.operation != request.operation
            or not self.binding_repository.supports(binding)
        ):
            raise InvalidTargetError("actuation binding is stale or unsupported")

    def audit_dead_lettered(self, outcome: ConsumerOutcome) -> None:
        if not outcome.command_id:
            return
        try:
            intent = self.repository.get_by_command_id(outcome.command_id)
        except Exception as exc:
            self.metrics.audit_failures += 1
            logger.error("event=audit_failed action=CONTROL_ACTUATION_DEAD_LETTERED error_type=%s", type(exc).__name__)
            return
        if intent is not None:
            self._audit("CONTROL_ACTUATION_DEAD_LETTERED", intent)

    def _retry_at(self, attempt: int) -> datetime:
        delay = min(self.retry_max_delay_seconds, self.retry_base_delay_seconds * (2 ** max(0, attempt - 1)))
        if self.retry_jitter_seconds:
            delay += self.jitter(0.0, self.retry_jitter_seconds)
        return self._now() + timedelta(seconds=delay)

    @staticmethod
    def _identity_metadata(intent: Optional[DeliveryIntent] = None, request: Optional[ActuationRequest] = None) -> Dict[str, Any]:
        source = intent or request
        if source is None:
            return {}
        return {
            "recommendation_id": source.recommendation_id,
            "correlation_id": source.correlation_id,
            "command_id": getattr(source, "command_id", None),
            "project_id": source.project_id,
            "attempts": getattr(intent, "retry_count", 0),
        }

    def _transition(self, **kwargs: Any) -> DeliveryIntent:
        try:
            return self.repository.transition(**kwargs)
        except InvalidDeliveryTransition:
            raise
        except Exception as exc:
            raise PersistenceDeliveryError("intent transition could not be persisted") from exc

    def _dispatch(self, intent: DeliveryIntent, request: ActuationRequest, *, from_statuses: set[str]) -> ConsumerOutcome:
        if parse_timestamp(request.expires_at) <= self._now():
            intent = self._transition(command_id=intent.command_id, from_statuses=from_statuses, to_status="expired")
            self.metrics.expired += 1
            self._audit("CONTROL_ACTUATION_EXPIRED", intent)
            logger.info("event=recommendation_expired command_id=%s", intent.command_id)
            return ConsumerOutcome(status="expired", command_id=intent.command_id, metadata=self._identity_metadata(intent))
        try:
            intent = self._transition(
                command_id=intent.command_id, from_statuses=from_statuses, to_status="dispatched",
                increment_retry_count=True, record_attempt=True,
            )
        except PersistenceDeliveryError:
            raise
        except InvalidDeliveryTransition:
            return ConsumerOutcome(status="retry_claimed", command_id=intent.command_id, deduplicated=True)
        self._audit("CONTROL_ACTUATION_DISPATCH_ATTEMPT", intent)
        logger.info("event=dispatch_attempt command_id=%s attempt=%s", intent.command_id, intent.retry_count)
        try:
            result = self.adapter.dispatch(request, attempt=intent.retry_count)
            intent = self._transition(command_id=intent.command_id, from_statuses={"dispatched"}, to_status="acknowledged")
            normalized = self.adapter.normalize_result(result)
            self.metrics.dispatch_success += 1
            self._audit("CONTROL_ACTUATION_ACKNOWLEDGED_SIMULATED", intent, result=normalized)
            logger.info("event=acknowledged command_id=%s attempt=%s", intent.command_id, intent.retry_count)
            return ConsumerOutcome(status="acknowledged", command_id=intent.command_id, result=normalized, metadata=self._identity_metadata(intent))
        except Exception as exc:
            failure = classify_delivery_error(exc)
            if failure.retryable and intent.retry_count < self.max_retry_attempts:
                retry_at = self._retry_at(intent.retry_count)
                intent = self._transition(
                    command_id=intent.command_id, from_statuses={"dispatched"}, to_status="retry_pending",
                    last_error=f"{failure.code}:{type(exc).__name__}", next_retry_at=retry_at,
                )
                self.metrics.dispatch_retry += 1
                self._audit("CONTROL_ACTUATION_RETRY_SCHEDULED", intent)
                logger.warning("event=retry_scheduled command_id=%s attempt=%s next_retry_at=%s error_code=%s", intent.command_id, intent.retry_count, retry_at.isoformat(), failure.code)
                return ConsumerOutcome(status="retry_pending", command_id=intent.command_id, error_code=failure.code, metadata=self._identity_metadata(intent))
            intent = self._transition(
                command_id=intent.command_id, from_statuses={"dispatched"}, to_status="failed_final",
                last_error=f"{failure.code}:{type(exc).__name__}",
            )
            self.metrics.dispatch_failed += 1
            action = "CONTROL_ACTUATION_RETRY_EXHAUSTED" if failure.retryable else "CONTROL_ACTUATION_FAILED_PERMANENT"
            self._audit(action, intent)
            logger.error("event=dispatch_failed command_id=%s attempt=%s error_code=%s", intent.command_id, intent.retry_count, failure.code)
            return ConsumerOutcome(status="failed_final", command_id=intent.command_id, error_code=failure.code, should_dead_letter=True, metadata=self._identity_metadata(intent))

    def process(self, envelope: Dict[str, Any]) -> ConsumerOutcome:
        self.metrics.recommendations_received += 1
        try:
            request = build_simulated_request(envelope)
        except RecommendationOnlyDelivery:
            self._audit_invalid(envelope, "recommendation_only", action="CONTROL_ACTUATION_RECOMMENDATION_ONLY")
            logger.info("event=recommendation_only")
            return ConsumerOutcome(status="recommendation_only")
        except DeliveryError as exc:
            self.metrics.invalid += 1
            self._audit_invalid(envelope, exc.code)
            logger.warning("event=recommendation_invalid error_code=%s", exc.code)
            return ConsumerOutcome(status="rejected", error_code=exc.code, should_dead_letter=True)
        try:
            self._validate_target_binding(request)
            intent, created = self.repository.create_or_get(request)
            if not created:
                self.metrics.duplicate += 1
                self.metrics.intents_reused += 1
                if intent.status == "retry_pending" and intent.next_retry_at and intent.next_retry_at <= self._now():
                    return self._dispatch(intent, replace(request, command_id=intent.command_id), from_statuses={"retry_pending"})
                self._audit("CONTROL_ACTUATION_INTENT_REUSED", intent)
                logger.info("event=intent_reused command_id=%s status=%s", intent.command_id, intent.status)
                return ConsumerOutcome(status=intent.status, command_id=intent.command_id, deduplicated=True, metadata=self._identity_metadata(intent))
            self.metrics.intents_created += 1
            self._audit("CONTROL_ACTUATION_INTENT_CREATED", intent)
            logger.info("event=intent_created command_id=%s", intent.command_id)
            if parse_timestamp(request.expires_at) <= self._now():
                intent = self._transition(command_id=intent.command_id, from_statuses={"received"}, to_status="expired")
                self.metrics.expired += 1
                self._audit("CONTROL_ACTUATION_EXPIRED", intent)
                return ConsumerOutcome(status="expired", command_id=intent.command_id, metadata=self._identity_metadata(intent))
            try:
                self.adapter.validate_target(request)
            except Exception as exc:
                failure = classify_delivery_error(InvalidTargetError(str(exc)))
                intent = self._transition(
                    command_id=intent.command_id, from_statuses={"received"}, to_status="rejected",
                    last_error=f"{failure.code}:{type(exc).__name__}",
                )
                self._audit("CONTROL_ACTUATION_REJECTED", intent)
                return ConsumerOutcome(status="rejected", command_id=intent.command_id, error_code=failure.code, should_dead_letter=True, metadata=self._identity_metadata(intent))
            intent = self._transition(command_id=intent.command_id, from_statuses={"received"}, to_status="validated")
            self.metrics.valid += 1
            self._audit("CONTROL_ACTUATION_VALIDATED", intent)
            intent = self._transition(command_id=intent.command_id, from_statuses={"validated"}, to_status="ready_to_dispatch")
            self._audit("CONTROL_ACTUATION_READY_TO_DISPATCH", intent)
            return self._dispatch(intent, request, from_statuses={"ready_to_dispatch"})
        except InvalidTargetError as exc:
            self.metrics.invalid += 1
            self._audit_invalid(envelope, exc.code, action="CONTROL_ACTUATION_INVALID_TARGET")
            logger.warning("event=target_invalid error_code=%s", exc.code)
            return ConsumerOutcome(status="rejected", error_code=exc.code, should_dead_letter=True)
        except PersistenceDeliveryError as exc:
            logger.error("event=persistence_failed error_code=%s", exc.code)
            return ConsumerOutcome(status="persistence_failed", error_code=exc.code, persistence_failed=True)
        except Exception as exc:
            logger.exception("event=unexpected_delivery_persistence_failure error_type=%s", type(exc).__name__)
            return ConsumerOutcome(
                status="persistence_failed",
                error_code=PersistenceDeliveryError.code,
                persistence_failed=True,
            )

    def process_due_retries(self, *, limit: int = 20) -> list[ConsumerOutcome]:
        outcomes = []
        for intent in self.repository.get_due_retries(now=self._now(), limit=limit):
            try:
                outcomes.append(self._dispatch(intent, request_from_intent(intent), from_statuses={"retry_pending"}))
            except PersistenceDeliveryError as exc:
                logger.error("event=scheduled_retry_persistence_failed command_id=%s error_code=%s", intent.command_id, exc.code)
        return outcomes


def _rabbitmq_client():
    from iot_middleware.services.control_engine_worker import _load_rabbitmq_client

    client, _ = _load_rabbitmq_client()
    return client


def declare_simulated_delivery_topology(client: Any, *, queue_name: str = SIMULATED_RECOMMENDATION_QUEUE, routing_key: str = SIMULATED_RECOMMENDATION_ROUTING_KEY, dlx: str = SIMULATED_ACTUATION_DLX, dlq: str = SIMULATED_ACTUATION_DLQ, dlq_routing_key: str = SIMULATED_ACTUATION_DLQ_ROUTING_KEY) -> bool:
    """Declare only the simulated delivery DLX/DLQ, idempotently and isolated from legacy queues."""
    return bool(
        client.declare_exchange(dlx, exchange_type="direct", durable=True)
        and client.declare_topic_queue(dlq, routing_keys=[dlq_routing_key], durable=True, exchange_name=dlx)
        and client.declare_topic_queue(
            queue_name, routing_keys=[routing_key], durable=True,
            arguments={"x-dead-letter-exchange": dlx, "x-dead-letter-routing-key": dlq_routing_key},
        )
    )


def _dead_letter_payload(outcome: ConsumerOutcome, message: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "message_type": "control.actuation.dead_letter", "schema_version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(), "reason": outcome.error_code or outcome.status,
        "original_routing_key": message.get("routing_key"), "attempts": (outcome.metadata or {}).get("attempts", 0),
        "recommendation_id": (outcome.metadata or {}).get("recommendation_id"),
        "correlation_id": (outcome.metadata or {}).get("correlation_id"),
        "command_id": (outcome.metadata or {}).get("command_id"),
    }


def consume_simulated_recommendations(*, max_messages: Optional[int] = None, idle_timeout_seconds: Optional[float] = None) -> int:
    client = _rabbitmq_client()
    if not declare_simulated_delivery_topology(client):
        raise ConnectionError("Could not declare simulated actuation delivery topology")
    consumer = SimulatedActuationConsumer()
    processed = 0
    idle_started = time.monotonic()
    while True:
        for retry_outcome in consumer.process_due_retries():
            if retry_outcome.should_dead_letter:
                published = client.publish_json(
                    routing_key=SIMULATED_ACTUATION_DLQ_ROUTING_KEY,
                    payload=_dead_letter_payload(
                        retry_outcome,
                        {"routing_key": SIMULATED_RECOMMENDATION_ROUTING_KEY},
                    ),
                    exchange_name=SIMULATED_ACTUATION_DLX,
                )
                if published:
                    consumer.metrics.dead_lettered += 1
                    consumer.audit_dead_lettered(retry_outcome)
                    logger.warning("event=dead_lettered command_id=%s reason=%s", retry_outcome.command_id, retry_outcome.error_code)
                else:
                    logger.error("event=dead_letter_publish_failed command_id=%s", retry_outcome.command_id)
        message = client.get_raw_message(SIMULATED_RECOMMENDATION_QUEUE, auto_ack=False)
        if message is None:
            if idle_timeout_seconds is not None and time.monotonic() - idle_started >= idle_timeout_seconds:
                return processed
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        idle_started = time.monotonic()
        try:
            try:
                envelope = json.loads(message["body"].decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                envelope = {}
            outcome = consumer.process(envelope)
            if outcome.should_dead_letter:
                published = client.publish_json(
                    routing_key=SIMULATED_ACTUATION_DLQ_ROUTING_KEY,
                    payload=_dead_letter_payload(outcome, message),
                    exchange_name=SIMULATED_ACTUATION_DLX,
                )
                if published:
                    consumer.metrics.dead_lettered += 1
                    consumer.audit_dead_lettered(outcome)
                    logger.warning("event=dead_lettered command_id=%s reason=%s", outcome.command_id, outcome.error_code)
                    client.ack_message(message["delivery_tag"])
                else:
                    # Broker-level DLX is the bounded fallback when enriched publication fails.
                    client.nack_message(message["delivery_tag"], requeue=False)
            elif outcome.persistence_failed:
                # No ACK before a durable broker decision. Never requeue indefinitely.
                client.nack_message(message["delivery_tag"], requeue=False)
            else:
                client.ack_message(message["delivery_tag"])
        except Exception:
            logger.exception("event=consumer_unhandled_failure")
            client.nack_message(message["delivery_tag"], requeue=False)
        processed += 1
        if max_messages is not None and processed >= max_messages:
            return processed


def main() -> None:
    logger.info("Simulated Actuation Consumer started queue=%s dlq=%s", SIMULATED_RECOMMENDATION_QUEUE, SIMULATED_ACTUATION_DLQ)
    consume_simulated_recommendations()


if __name__ == "__main__":  # pragma: no cover
    main()
