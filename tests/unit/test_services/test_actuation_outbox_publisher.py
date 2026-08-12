from datetime import datetime, timezone

from iot_middleware.services import actuation_outbox_publisher as module
from iot_middleware.services.actuation_outbox_publisher import ActuationOutboxPublisher
from iot_middleware.storage.actuation_outbox_repository import OutboxEvent


def event(attempt_count=1):
    return OutboxEvent("row-1", "00000000-0000-0000-0000-000000000041", "00000000-0000-0000-0000-000000000021", "recommendation::one", "corr-1", "00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000012", "relay_1", "00000000-0000-0000-0000-000000000013", 1, {"simulated": True, "physical_effects": False}, "publishing", attempt_count, "control.actuation.simulated.dispatch.v1", None, datetime.now(timezone.utc), None, None, datetime.now(timezone.utc))


class Repo:
    def __init__(self, item, final="pending"): self.item, self.final, self.published = item, final, []
    def claim(self, **kwargs): return [self.item]
    def mark_published(self, event_id): self.published.append(event_id)
    def retry_or_fail(self, *args, **kwargs): return self.final


class Client:
    def __init__(self, result): self.result = result
    def publish_json(self, **kwargs):
        if isinstance(self.result, Exception): raise self.result
        return self.result


def test_publisher_audits_attempt_and_success(monkeypatch):
    actions = []
    monkeypatch.setattr(module, "_audit", lambda action, *args, **kwargs: actions.append(action))
    repo = Repo(event()); publisher = ActuationOutboxPublisher(repo, Client(True))
    assert publisher.publish_once() == [("published", repo.item.event_id)]
    assert actions == ["CONTROL_ACTUATION_OUTBOX_PUBLISH_ATTEMPT", "CONTROL_ACTUATION_OUTBOX_PUBLISH_SUCCEEDED"]


def test_publisher_audits_failure_retry_and_exhaustion(monkeypatch):
    actions = []
    monkeypatch.setattr(module, "_audit", lambda action, *args, **kwargs: actions.append(action))
    retry_repo = Repo(event(), "pending")
    assert ActuationOutboxPublisher(retry_repo, Client(False)).publish_once() == [("pending", retry_repo.item.event_id)]
    assert {"CONTROL_ACTUATION_OUTBOX_PUBLISH_FAILED", "CONTROL_ACTUATION_OUTBOX_RETRY_SCHEDULED"}.issubset(actions)
    actions.clear()
    failed_repo = Repo(event(3), "failed")
    assert ActuationOutboxPublisher(failed_repo, Client(False)).publish_once() == [("failed", failed_repo.item.event_id)]
    assert {"CONTROL_ACTUATION_OUTBOX_PUBLISH_FAILED", "CONTROL_ACTUATION_OUTBOX_RETRY_EXHAUSTED"}.issubset(actions)
