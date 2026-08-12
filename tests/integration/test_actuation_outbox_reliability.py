"""PostgreSQL-backed reliability proofs for the transactional simulated-actuation outbox.

Run deliberately with RUN_OUTBOX_INTEGRATION=1; every test owns and removes its
temporary project, intents and outbox rows.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from parametric_control_engine.contracts.actuation_contracts import ActuationRequest
from iot_middleware.services import actuation_outbox_publisher as publisher_module
from iot_middleware.services.actuation_outbox_publisher import ActuationOutboxPublisher
from iot_middleware.storage.actuation_delivery_intent_repository import ActuationDeliveryIntentRepository
from iot_middleware.storage.actuation_outbox_repository import ActuationOutboxRepository
from iot_middleware.storage.db_handler import _get_control_settings_connection_url, _get_control_settings_engine

pytestmark = pytest.mark.skipif(os.getenv("RUN_OUTBOX_INTEGRATION") != "1", reason="requires local PostgreSQL")


class Broker:
    def __init__(self, outcomes): self.outcomes, self.messages = list(outcomes), []
    def publish_json(self, **kwargs):
        self.messages.append(kwargs)
        outcome = self.outcomes.pop(0) if self.outcomes else True
        if isinstance(outcome, Exception): raise outcome
        return outcome


def request(project_id: str, command_id: str | None = None) -> ActuationRequest:
    now = datetime.now(timezone.utc)
    return ActuationRequest(
        schema_version="1.0", command_id=command_id or str(uuid.uuid4()), recommendation_id=f"recommendation::{uuid.uuid4()}",
        correlation_id=str(uuid.uuid4()), project_id=project_id, policy_id="prompt062-policy", policy_version=1,
        source_asset_id=str(uuid.uuid4()), target_asset_id=str(uuid.uuid4()), target_kind="simulated",
        target_reference="asset:target:relay_1", variable_id="tank_level", operation="set", requested_value=1.0,
        created_at=now.isoformat(), expires_at=(now + timedelta(minutes=5)).isoformat(), governance_mode="simulated",
        idempotency_key=f"actuation::{uuid.uuid4()}", control_point="relay_1", actuation_binding_id=str(uuid.uuid4()),
        actuation_binding_version=1, simulated=True,
    )


@pytest.fixture
def subject(monkeypatch):
    engine = _get_control_settings_engine(_get_control_settings_connection_url())
    project_id = str(uuid.uuid4())
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO public.projects (id,name,status) VALUES (CAST(:id AS uuid),:name,'active')"), {"id": project_id, "name": f"prompt062-{project_id}"})
    monkeypatch.setattr(publisher_module, "_audit", lambda *args, **kwargs: None)
    try:
        yield engine, project_id, ActuationDeliveryIntentRepository(engine), ActuationOutboxRepository(engine)
    finally:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM public.control_actuation_outbox WHERE project_id=CAST(:id AS uuid)"), {"id": project_id})
            connection.execute(text("DELETE FROM public.control_actuation_delivery_intents WHERE project_id=CAST(:id AS uuid)"), {"id": project_id})
            connection.execute(text("DELETE FROM public.projects WHERE id=CAST(:id AS uuid)"), {"id": project_id})


def create_received(intent_repo, req):
    intent, created = intent_repo.create_or_get(req)
    assert created and intent.status == "received"
    return intent


def test_atomic_rollback_when_outbox_insert_fails(subject):
    engine, project_id, intents, _ = subject
    req = request(project_id); create_received(intents, req)
    class FailingOutbox:
        def insert_for_request(self, connection, request): raise RuntimeError("injected_outbox_insert_failure")
    with pytest.raises(RuntimeError, match="injected_outbox"):
        intents.prepare_dispatch_with_outbox(req, outbox_repository=FailingOutbox())
    assert intents.get_by_command_id(req.command_id).status == "received"
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM public.control_actuation_outbox WHERE command_id=CAST(:id AS uuid)"), {"id": req.command_id}).scalar_one() == 0


def test_atomic_commit_and_duplicate_creation_are_coherent(subject):
    engine, project_id, intents, outbox = subject
    req = request(project_id); create_received(intents, req)
    intent, event = intents.prepare_dispatch_with_outbox(req)
    assert intent.status == "ready_to_dispatch"
    assert event.command_id == req.command_id and event.payload["event_id"] == event.event_id
    with engine.begin() as c:
        duplicate = outbox.insert_for_request(c, req)
    assert duplicate.event_id == event.event_id
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM public.control_actuation_outbox WHERE command_id=CAST(:id AS uuid)"), {"id": req.command_id}).scalar_one() == 1


def test_publish_failure_retry_recovery_crash_and_exhaustion(subject):
    engine, project_id, intents, outbox = subject
    req = request(project_id); create_received(intents, req); _, event = intents.prepare_dispatch_with_outbox(req)
    failing = ActuationOutboxPublisher(outbox, Broker([False]), max_attempts=3, retry_base_delay_seconds=0)
    assert failing.publish_once() == [("pending", event.event_id)]
    retained = outbox.get(event.event_id)
    assert retained.status == "pending" and retained.attempt_count == 1 and retained.last_error
    recovered = ActuationOutboxPublisher(outbox, Broker([True]), max_attempts=3, retry_base_delay_seconds=0)
    assert recovered.publish_once() == [("published", event.event_id)]
    assert outbox.get(event.event_id).status == "published"

    req2 = request(project_id); create_received(intents, req2); _, crash_event = intents.prepare_dispatch_with_outbox(req2)
    class CrashRepository(ActuationOutboxRepository):
        def __init__(self, engine): super().__init__(engine); self.crashed = False
        def mark_published(self, event_id):
            if not self.crashed:
                self.crashed = True; raise RuntimeError("injected_crash_after_publish")
            return super().mark_published(event_id)
    crash_repo = CrashRepository(engine)
    first = ActuationOutboxPublisher(crash_repo, Broker([True]), max_attempts=3, retry_base_delay_seconds=0)
    assert first.publish_once() == [("pending", crash_event.event_id)]
    assert crash_repo.get(crash_event.event_id).event_id == crash_event.event_id
    second = ActuationOutboxPublisher(crash_repo, Broker([True]), max_attempts=3, retry_base_delay_seconds=0)
    assert second.publish_once() == [("published", crash_event.event_id)]

    req3 = request(project_id); create_received(intents, req3); _, failed_event = intents.prepare_dispatch_with_outbox(req3)
    exhausted = ActuationOutboxPublisher(outbox, Broker([False, False, False]), max_attempts=3, retry_base_delay_seconds=0)
    for _ in range(3): exhausted.publish_once()
    failed = outbox.get(failed_event.event_id)
    assert failed.status == "failed" and failed.attempt_count == 3 and failed.last_error


def test_leases_claims_and_metrics_are_recoverable(subject):
    engine, project_id, intents, outbox = subject
    req1, req2 = request(project_id), request(project_id)
    create_received(intents, req1); create_received(intents, req2)
    _, event1 = intents.prepare_dispatch_with_outbox(req1); _, event2 = intents.prepare_dispatch_with_outbox(req2)
    first = outbox.claim(limit=1, lease_seconds=30)
    second = outbox.claim(limit=1, lease_seconds=30)
    assert len(first) == len(second) == 1 and first[0].event_id != second[0].event_id
    assert outbox.claim(limit=2, lease_seconds=30) == []
    with engine.begin() as c:
        c.execute(text("UPDATE public.control_actuation_outbox SET lease_until=NOW()-interval '1 second' WHERE event_id=CAST(:id AS uuid)"), {"id": first[0].event_id})
    recovered = outbox.claim(limit=1, lease_seconds=30)
    assert recovered[0].event_id == first[0].event_id
    metrics = outbox.metrics()
    assert metrics["pending_count"] >= 0 and metrics["published_count"] >= 0 and metrics["failed_count"] >= 0
    assert metrics["oldest_pending_age_seconds"] is not None
