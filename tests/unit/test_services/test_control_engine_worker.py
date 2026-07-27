from copy import deepcopy
from unittest.mock import MagicMock
from types import SimpleNamespace

from iot_middleware.services import control_engine_worker as worker


class DummyClient:
    def __init__(self):
        self.publish_json = MagicMock(return_value=True)
        self.declare_topic_queue = MagicMock(return_value=True)
        self.get_json_message = MagicMock()
        self.ack_message = MagicMock(return_value=True)


def test_publish_event_uses_rabbitmq_when_enabled(monkeypatch):
    dummy_client = DummyClient()

    monkeypatch.setattr(worker, "PUBLISH_MODE", "rabbitmq")
    monkeypatch.setattr(worker, "_load_rabbitmq_client", lambda: (dummy_client, object()))

    payload = {"message_type": "control.recommendation", "payload": {"value": 42}}
    worker.publish_event("control.recommendations", payload)

    dummy_client.publish_json.assert_called_once_with(
        routing_key="control.recommendations",
        payload=payload,
        queue_name="control.recommendations",
        durable_queue=True,
    )


def test_allow_inmemory_policy_fallback_requires_explicit_flag(monkeypatch):
    monkeypatch.setattr(worker, "PUBLISH_MODE", "stdout")
    monkeypatch.delenv("CONTROL_WORKER_ALLOW_INMEMORY_POLICY_FALLBACK", raising=False)

    assert worker._allow_inmemory_policy_fallback() is False

    monkeypatch.setenv("CONTROL_WORKER_ALLOW_INMEMORY_POLICY_FALLBACK", "true")
    assert worker._allow_inmemory_policy_fallback() is True


def test_consume_rabbitmq_events_processes_and_acks(monkeypatch):
    dummy_client = DummyClient()
    dummy_client.get_json_message.side_effect = [
        {
            "delivery_tag": 123,
            "payload": {
                "project_id": "00000000-0000-0000-0000-000000000001",
                "variable": "tank_level",
                "value": 72.5,
                "timestamp": "2026-01-01T00:00:00+00:00",
                "context": {"sector": "tank_A"},
            },
        }
    ]

    handled = []

    monkeypatch.setattr(worker, "_load_rabbitmq_client", lambda: (dummy_client, object()))
    monkeypatch.setattr(worker, "handle_event", lambda event: handled.append(event) or {"ok": True})

    processed = worker.consume_rabbitmq_events(max_messages=1, idle_timeout_seconds=0.1)

    assert processed == 1
    assert handled == [
        {
            "project_id": "00000000-0000-0000-0000-000000000001",
            "variable": "tank_level",
            "value": 72.5,
            "timestamp": "2026-01-01T00:00:00+00:00",
            "context": {"sector": "tank_A"},
        }
    ]
    dummy_client.declare_topic_queue.assert_called_once()
    dummy_client.ack_message.assert_called_once_with(123)


def test_normalize_telemetry_message_accepts_payload_envelope():
    wrapped = {
        "payload": {
            "project_id": "00000000-0000-0000-0000-000000000001",
            "variable": "tank_level",
            "value": 72.5,
            "timestamp": "2026-01-01T00:00:00+00:00",
        }
    }

    normalized = worker._normalize_telemetry_message(wrapped)

    assert normalized["project_id"] == "00000000-0000-0000-0000-000000000001"
    assert normalized["variable"] == "tank_level"


def test_build_base_audit_envelope_starts_with_not_attempted_persistence():
    envelope = worker._build_base_audit_envelope(
        input_event={
            "event_id": "evt-1",
            "project_id": "00000000-0000-0000-0000-000000000001",
            "variable": "tank_level",
            "value": 72.5,
            "timestamp": "2026-01-01T00:00:00+00:00",
        },
        status="skipped",
    )

    assert envelope["payload"]["delivery"]["audit_persistence"]["status"] == "not_attempted"
    assert envelope["payload"]["delivery"]["audit_persistence"]["attempted"] is False


def test_handle_event_disabled_emits_only_audit(monkeypatch):
    published = []
    persisted = []

    monkeypatch.setattr(worker, "is_parametric_control_enabled", lambda project_id: False)
    monkeypatch.setattr(
        worker,
        "publish_event",
        lambda queue, payload: published.append((queue, payload)) or {
            "status": "mocked",
            "transport": "memory",
            "routing_key": queue,
        },
    )
    monkeypatch.setattr(
        worker,
        "_persist_audit_envelope",
        lambda payload, action: persisted.append((action, payload)) or {
            "status": "mocked",
            "store": "memory",
            "action": action,
        },
    )

    event = {
        "project_id": "00000000-0000-0000-0000-000000000001",
        "variable": "tank_level",
        "value": 72.5,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "context": {"sector": "tank_A"},
    }

    result = worker.handle_event(event)

    assert result["publish_envelope"] is None
    assert result["audit_envelope"]["status"] == "skipped"
    assert result["audit_envelope"]["skip_reason"] == "feature_flag_disabled"
    assert published == [(worker.AUDIT_QUEUE, result["audit_envelope"])]
    assert persisted == [("CONTROL_SKIPPED_BY_FEATURE_FLAG", result["audit_envelope"])]


def test_handle_event_enabled_emits_recommendation_and_audit(monkeypatch):
    published = []
    persisted = []

    runtime_event = SimpleNamespace(
        variable_id="tank_level",
        value=72.5,
    )
    selection = SimpleNamespace(
        binding=object(),
        policy_id="policy::tank_level",
        selector_name="static-policy-selector",
        priority=10,
        version=2,
        policy_type="proportional",
        selection_trace=[],
    )
    sink_output = SimpleNamespace(
        publish_envelope={
            "message_type": "control.recommendation",
            "payload": {
                "event_id": "evt-1",
                "variable_id": "tank_level",
            },
        },
        audit_envelope={
            "message_type": "control.audit",
            "payload": {
                "event_id": "evt-1",
                "variable_id": "tank_level",
            },
        },
    )

    monkeypatch.setattr(worker, "is_parametric_control_enabled", lambda project_id: True)
    monkeypatch.setattr(worker, "_build_runtime_event", lambda event: runtime_event)
    monkeypatch.setattr(worker, "_resolve_policy_selection", lambda event: (object(), selection))
    monkeypatch.setattr(
        worker,
        "EventDrivenRecommendationAdapter",
        lambda binding, evaluator=None: SimpleNamespace(evaluate_event=lambda event: object()),
    )
    monkeypatch.setattr(worker, "sink_adapter", SimpleNamespace(build_sink_output=lambda recommendation: sink_output))
    monkeypatch.setattr(
        worker,
        "publish_event",
        lambda queue, payload: published.append((queue, payload)) or {
            "status": "mocked",
            "transport": "memory",
            "routing_key": queue,
        },
    )
    monkeypatch.setattr(
        worker,
        "_persist_audit_envelope",
        lambda payload, action: persisted.append((action, payload)) or {
            "status": "mocked",
            "store": "memory",
            "action": action,
        },
    )

    event = {
        "project_id": "00000000-0000-0000-0000-000000000001",
        "variable": "tank_level",
        "value": 72.5,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "context": {"sector": "tank_A"},
    }

    result = worker.handle_event(event)

    assert result["publish_envelope"]["payload"]["project_id"] == "00000000-0000-0000-0000-000000000001"
    assert result["audit_envelope"]["status"] == "processed"
    assert result["audit_envelope"]["message_type"] == "control.audit"
    assert result["audit_envelope"]["correlation_id"] == "control::unknown-event::tank_level"
    assert result["audit_envelope"]["payload"]["project_id"] == "00000000-0000-0000-0000-000000000001"
    assert result["publish_envelope"]["payload"]["policy_type"] == "proportional"
    assert result["publish_envelope"]["payload"]["policy_version"] == 2
    assert result["publish_envelope"]["payload"]["policy_priority"] == 10
    assert result["audit_envelope"]["payload"]["delivery"]["recommendation_publish"]["routing_key"] == worker.RECOMMENDATION_QUEUE
    assert published == [
        (worker.RECOMMENDATION_QUEUE, result["publish_envelope"]),
        (worker.AUDIT_QUEUE, result["audit_envelope"]),
    ]
    assert persisted == [("CONTROL_RECOMMENDATION_EMITTED", result["audit_envelope"])]


def test_handle_event_publishes_audit_with_pending_persistence_before_final_result(monkeypatch):
    published = []

    runtime_event = SimpleNamespace(
        variable_id="tank_level",
        value=72.5,
    )
    selection = SimpleNamespace(
        binding=object(),
        policy_id="policy::tank_level",
        selector_name="static-policy-selector",
        priority=10,
        version=2,
        policy_type="proportional",
        selection_trace=[],
    )
    sink_output = SimpleNamespace(
        publish_envelope={
            "message_type": "control.recommendation",
            "payload": {
                "event_id": "evt-1",
                "variable_id": "tank_level",
            },
        },
        audit_envelope={
            "message_type": "control.audit",
            "payload": {
                "event_id": "evt-1",
                "variable_id": "tank_level",
            },
        },
    )

    def capture_publish(queue, payload):
        published.append((queue, deepcopy(payload)))
        return {
            "status": "mocked",
            "transport": "memory",
            "routing_key": queue,
        }

    monkeypatch.setattr(worker, "is_parametric_control_enabled", lambda project_id: True)
    monkeypatch.setattr(worker, "_build_runtime_event", lambda event: runtime_event)
    monkeypatch.setattr(worker, "_resolve_policy_selection", lambda event: (object(), selection))
    monkeypatch.setattr(
        worker,
        "EventDrivenRecommendationAdapter",
        lambda binding, evaluator=None: SimpleNamespace(evaluate_event=lambda event: object()),
    )
    monkeypatch.setattr(worker, "sink_adapter", SimpleNamespace(build_sink_output=lambda recommendation: sink_output))
    monkeypatch.setattr(worker, "publish_event", capture_publish)
    monkeypatch.setattr(
        worker,
        "_persist_audit_envelope",
        lambda payload, action: {
            "status": "persisted",
            "attempted": True,
            "backend": "postgresql",
            "store": "iot_schema.auditoria",
            "table": "iot_schema.auditoria",
            "action": action,
            "attempted_at": "2026-01-01T00:00:01+00:00",
            "completed_at": "2026-01-01T00:00:02+00:00",
            "row_id": 99,
            "rows_affected": 1,
        },
    )

    result = worker.handle_event(
        {
            "project_id": "00000000-0000-0000-0000-000000000001",
            "variable": "tank_level",
            "value": 72.5,
            "timestamp": "2026-01-01T00:00:00+00:00",
            "context": {"sector": "tank_A"},
        }
    )

    published_audit = next(payload for queue, payload in published if queue == worker.AUDIT_QUEUE)
    assert published_audit["payload"]["delivery"]["audit_persistence"]["status"] == "pending_best_effort"
    assert published_audit["payload"]["delivery"]["audit_persistence"]["attempted"] is True
    assert result["audit_envelope"]["payload"]["delivery"]["audit_persistence"]["status"] == "persisted"
    assert result["audit_envelope"]["payload"]["delivery"]["audit_persistence"]["row_id"] == 99


def test_handle_event_no_policy_found_emits_failure_audit(monkeypatch):
    published = []
    persisted = []

    monkeypatch.setattr(worker, "is_parametric_control_enabled", lambda project_id: True)
    monkeypatch.setattr(
        worker,
        "_resolve_policy_selection",
        lambda event: (_ for _ in ()).throw(ValueError("No static policy found for variable_id='tank_level'")),
    )
    monkeypatch.setattr(
        worker,
        "publish_event",
        lambda queue, payload: published.append((queue, payload)) or {
            "status": "mocked",
            "transport": "memory",
            "routing_key": queue,
        },
    )
    monkeypatch.setattr(
        worker,
        "_persist_audit_envelope",
        lambda payload, action: persisted.append((action, payload)) or {
            "status": "mocked",
            "store": "memory",
            "action": action,
        },
    )

    event = {
        "project_id": "00000000-0000-0000-0000-000000000001",
        "variable": "tank_level",
        "value": 72.5,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "context": {"sector": "tank_A"},
    }

    result = worker.handle_event(event)

    assert result is None
    assert len(published) == 1
    assert published[0][0] == worker.AUDIT_QUEUE
    assert published[0][1]["status"] == "error"
    assert "No static policy found" in published[0][1]["error"]
    assert persisted == [("CONTROL_EVALUATION_FAILED", published[0][1])]


def test_persist_audit_envelope_returns_failed_metadata_on_exception(monkeypatch):
    from iot_middleware.storage import db_handler

    monkeypatch.setattr(
        db_handler,
        "persist_control_audit_record",
        lambda audit_payload, action: (_ for _ in ()).throw(RuntimeError("db unavailable")),
    )

    result = worker._persist_audit_envelope(
        {
            "payload": {
                "delivery": {
                    "audit_persistence": {
                        "status": "pending_best_effort",
                        "attempted": True,
                        "attempted_at": "2026-01-01T00:00:00+00:00",
                    }
                }
            }
        },
        action="CONTROL_RECOMMENDATION_EMITTED",
    )

    assert result["status"] == "failed"
    assert result["attempted"] is True
    assert result["rows_affected"] == 0
    assert "db unavailable" in result["error"]
