"""At-least-once publisher for persisted simulated dispatch events."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

from iot_middleware.storage.actuation_outbox_repository import ActuationOutboxRepository, OutboxEvent
from iot_middleware.storage.db_handler import persist_control_audit_record


def _audit(action: str, event: OutboxEvent, *, error: str | None = None) -> None:
    """Best-effort audit of meaningful publisher events, never empty poll cycles."""
    try:
        persist_control_audit_record({
            "message_type": "control.actuation.outbox.audit", "schema_version": "1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(), "project_id": event.project_id,
            "correlation_id": event.correlation_id,
            "payload": {
                "event_id": event.event_id, "command_id": event.command_id,
                "recommendation_id": event.recommendation_id, "correlation_id": event.correlation_id,
                "project_id": event.project_id, "target_asset_id": event.target_asset_id,
                "control_point": event.control_point, "binding_id": event.binding_id,
                "binding_version": event.binding_version, "attempt": event.attempt_count,
                "error": error, "simulated": True, "physical_effects": False,
            },
        }, action=action, entity="actuation_outbox_publisher")
    except Exception:
        # The event state remains authoritative; audit failure cannot undo a broker decision.
        pass


class ActuationOutboxPublisher:
    def __init__(self, repository=None, client=None, *, max_attempts: int = 3, retry_base_delay_seconds: float = 1.0) -> None:
        self.repository = repository or ActuationOutboxRepository()
        self.client = client
        self.max_attempts = max(1, max_attempts)
        self.retry_base_delay_seconds = max(0.0, retry_base_delay_seconds)
        self.metrics = {"publish_attempts": 0, "publish_success": 0, "publish_failures": 0, "retries": 0, "failed": 0}

    def publish_once(self, limit: int = 20) -> list[tuple[str, str]]:
        if self.client is None:
            from iot_middleware.services.control_engine_worker import _load_rabbitmq_client
            self.client, _ = _load_rabbitmq_client()
        result = []
        for event in self.repository.claim(limit=limit):
            self.metrics["publish_attempts"] += 1
            _audit("CONTROL_ACTUATION_OUTBOX_PUBLISH_ATTEMPT", event)
            try:
                if not self.client.publish_json(routing_key=event.routing_key, payload=event.payload):
                    raise ConnectionError("broker_publish_false")
                self.repository.mark_published(event.event_id)
                self.metrics["publish_success"] += 1
                _audit("CONTROL_ACTUATION_OUTBOX_PUBLISH_SUCCEEDED", event)
                result.append(("published", event.event_id))
            except Exception as exc:
                self.metrics["publish_failures"] += 1
                status = self.repository.retry_or_fail(event, exc, max_attempts=self.max_attempts, base_delay_seconds=self.retry_base_delay_seconds)
                if status == "failed":
                    self.metrics["failed"] += 1
                    _audit("CONTROL_ACTUATION_OUTBOX_RETRY_EXHAUSTED", event, error=str(exc))
                else:
                    self.metrics["retries"] += 1
                    _audit("CONTROL_ACTUATION_OUTBOX_RETRY_SCHEDULED", event, error=str(exc))
                _audit("CONTROL_ACTUATION_OUTBOX_PUBLISH_FAILED", event, error=str(exc))
                result.append((status, event.event_id))
        return result


def main() -> None:
    publisher = ActuationOutboxPublisher(
        max_attempts=int(os.getenv("ACTUATION_OUTBOX_MAX_ATTEMPTS", "3")),
        retry_base_delay_seconds=float(os.getenv("ACTUATION_OUTBOX_RETRY_BASE_DELAY_SECONDS", "1")),
    )
    interval = float(os.getenv("ACTUATION_OUTBOX_POLL_INTERVAL_SECONDS", "1"))
    while True:
        publisher.publish_once()
        time.sleep(max(0.1, interval))


if __name__ == "__main__":
    main()
