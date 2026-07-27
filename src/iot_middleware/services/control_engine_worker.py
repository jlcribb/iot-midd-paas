"""
Control Engine Worker

Non-invasive runtime integration between telemetry events and the
parametric-control-engine.

Canonical flow:
Telemetry Event
→ ControlEvaluationRequest
→ Policy Selection
→ Evaluation
→ Recommendation
→ Publishable Envelope
→ Audit Envelope
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from iot_middleware.services.control_runtime_contract import (
    CONTROL_AUDIT_ACTION_EVALUATION_FAILED,
    CONTROL_AUDIT_PERSISTENCE_STATUS_FAILED,
    CONTROL_AUDIT_PERSISTENCE_STATUS_NOT_ATTEMPTED,
    CONTROL_AUDIT_PERSISTENCE_STATUS_PENDING,
    CONTROL_AUDIT_PERSISTENCE_STATUS_PERSISTED,
    CONTROL_AUDIT_ACTION_RECOMMENDATION_EMITTED,
    CONTROL_AUDIT_ACTION_SKIPPED_BY_FEATURE_FLAG,
    CONTROL_AUDIT_MESSAGE_TYPE,
    CONTROL_AUDIT_ROUTING_KEY,
    CONTROL_AUDIT_STATUS_ERROR,
    CONTROL_AUDIT_STATUS_PROCESSED,
    CONTROL_AUDIT_STATUS_SKIPPED,
    CONTROL_RECOMMENDATION_MESSAGE_TYPE,
    CONTROL_RECOMMENDATIONS_ROUTING_KEY,
    CONTROL_SKIP_REASON_FEATURE_FLAG_DISABLED,
    TELEMETRY_EVENTS_ROUTING_KEY,
)

logger = logging.getLogger("control_engine_worker")
logging.basicConfig(
    level=os.getenv("CONTROL_WORKER_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)


def _ensure_parametric_engine_path() -> None:
    """
    Allow running the worker from repo root without installing the engine package.
    Prefer proper package installation in production.
    """
    repo_root = os.getenv("REPO_ROOT", os.getcwd())
    engine_src = os.path.join(repo_root, "apps", "parametric-control-engine", "src")

    if os.path.isdir(engine_src) and engine_src not in sys.path:
        sys.path.insert(0, engine_src)


_ensure_parametric_engine_path()


try:
    from parametric_control_engine.adapters.event_adapter import (
        EventDrivenRecommendationAdapter,
    )
    from parametric_control_engine.adapters.recommendation_sink_adapter import (
        RecommendationSinkAdapter,
    )
    from parametric_control_engine.contracts.event_adapter_contracts import (
        MonovariableControlBinding,
        TelemetryStateEvent,
    )
    from parametric_control_engine.contracts.policy_contracts import (
        StaticPolicyDefinition,
    )
    from parametric_control_engine.models.control_models import (
        ControlParameters,
        ControlledVariableDefinition,
        SetpointReference,
    )
    from parametric_control_engine.policies.static_selector import StaticPolicySelector
    from parametric_control_engine.sources.in_memory_policy_source import (
        InMemoryPolicySource,
    )
    from parametric_control_engine.evaluators.threshold import ThresholdEvaluator
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "Could not import parametric-control-engine. "
        "Run with PYTHONPATH=apps/parametric-control-engine/src "
        "or install the package."
    ) from exc


TELEMETRY_QUEUE = os.getenv("CONTROL_WORKER_INPUT_QUEUE", TELEMETRY_EVENTS_ROUTING_KEY)
TELEMETRY_ROUTING_KEY = os.getenv(
    "CONTROL_WORKER_INPUT_ROUTING_KEY",
    TELEMETRY_QUEUE,
)
TELEMETRY_CONSUMER_QUEUE = os.getenv(
    "CONTROL_WORKER_CONSUMER_QUEUE",
    TELEMETRY_QUEUE,
)
RECOMMENDATION_QUEUE = os.getenv(
    "CONTROL_WORKER_RECOMMENDATION_QUEUE",
    CONTROL_RECOMMENDATIONS_ROUTING_KEY,
)
AUDIT_QUEUE = os.getenv("CONTROL_WORKER_AUDIT_QUEUE", CONTROL_AUDIT_ROUTING_KEY)
DEFAULT_SETPOINT = float(os.getenv("CONTROL_WORKER_SETPOINT", "70.0"))
DEFAULT_GAIN = float(os.getenv("CONTROL_WORKER_GAIN", "1.0"))
DEFAULT_DEADBAND = float(os.getenv("CONTROL_WORKER_DEADBAND", "0.0"))
DEFAULT_MIN_ACTION = float(os.getenv("CONTROL_WORKER_MIN_ACTION", "0.0"))
DEFAULT_MAX_ACTION = os.getenv("CONTROL_WORKER_MAX_ACTION")
PUBLISH_MODE = os.getenv("CONTROL_WORKER_PUBLISH_MODE", "rabbitmq").strip().lower()
POLL_INTERVAL_SECONDS = float(os.getenv("CONTROL_WORKER_POLL_INTERVAL_SECONDS", "1.0"))

sink_adapter = RecommendationSinkAdapter()
_rabbitmq_client = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _optional_float(raw: Optional[str]) -> Optional[float]:
    if raw is None or raw.strip() == "":
        return None
    return float(raw)


def _resolve_config_path() -> Optional[str]:
    explicit = os.getenv("CONTROL_WORKER_CONFIG_PATH") or os.getenv("IOT_MW_CONFIG_PATH")
    if explicit:
        return explicit

    repo_root = os.getenv("REPO_ROOT")
    if repo_root:
        candidate = os.path.join(repo_root, "config.yaml")
        if os.path.exists(candidate):
            return candidate

    return None


def _safe_to_dict(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    if hasattr(value, "__dict__"):
        return value.__dict__
    return value


def _build_correlation_id(input_event: Dict[str, Any]) -> str:
    event_id = str(input_event.get("event_id") or "unknown-event")
    variable = str(input_event.get("variable") or "unknown-variable")
    return f"control::{event_id}::{variable}"


def _build_audit_identity(input_event: Dict[str, Any]) -> Dict[str, str]:
    event_id = str(input_event.get("event_id") or "unknown-event")
    variable = str(input_event.get("variable") or "unknown-variable")
    return {
        "audit_id": f"audit::{event_id}::{variable}",
        "record_type": "control.runtime.audit",
        "partition_key": variable,
        "correlation_id": _build_correlation_id(input_event),
    }


def _build_delivery_metadata() -> Dict[str, Any]:
    return {
        "recommendation_publish": {
            "status": "not_requested",
            "transport": None,
            "routing_key": RECOMMENDATION_QUEUE,
        },
        "audit_publish": {
            "status": "pending",
            "transport": None,
            "routing_key": AUDIT_QUEUE,
        },
        "audit_persistence": _build_audit_persistence_metadata(
            status=CONTROL_AUDIT_PERSISTENCE_STATUS_NOT_ATTEMPTED,
            attempted=False,
        ),
    }


def _build_audit_persistence_metadata(
    *,
    status: str,
    attempted: bool,
    attempted_at: str | None = None,
    completed_at: str | None = None,
    row_id: int | None = None,
    rows_affected: int | None = None,
    error: str | None = None,
    action: str | None = None,
) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {
        "status": status,
        "attempted": attempted,
        "backend": "postgresql",
        "store": "iot_schema.auditoria",
        "table": "iot_schema.auditoria",
    }
    if attempted_at:
        metadata["attempted_at"] = attempted_at
    if completed_at:
        metadata["completed_at"] = completed_at
    if row_id is not None:
        metadata["row_id"] = row_id
    if rows_affected is not None:
        metadata["rows_affected"] = rows_affected
    if error:
        metadata["error"] = error
    if action:
        metadata["action"] = action
    return metadata


def _mark_audit_persistence_pending(audit_payload: Dict[str, Any]) -> None:
    delivery = audit_payload.setdefault("payload", {}).setdefault("delivery", _build_delivery_metadata())
    current = delivery.get("audit_persistence")
    attempted_at = None
    if isinstance(current, dict):
        attempted_at = current.get("attempted_at")
    delivery["audit_persistence"] = _build_audit_persistence_metadata(
        status=CONTROL_AUDIT_PERSISTENCE_STATUS_PENDING,
        attempted=True,
        attempted_at=attempted_at or utc_now_iso(),
    )


def _build_base_audit_envelope(
    *,
    input_event: Dict[str, Any],
    status: str,
) -> Dict[str, Any]:
    audit_identity = _build_audit_identity(input_event)
    payload = {
        "event_id": input_event.get("event_id"),
        "variable_id": input_event.get("variable"),
        "project_id": input_event.get("project_id"),
        "correlation_id": audit_identity["correlation_id"],
        "input_event": input_event,
        "policy_selection": None,
        "evaluation": None,
        "runtime_payload": None,
        "delivery": _build_delivery_metadata(),
    }

    return {
        **audit_identity,
        "message_type": CONTROL_AUDIT_MESSAGE_TYPE,
        "timestamp": utc_now_iso(),
        "status": status,
        "project_id": input_event.get("project_id"),
        "variable": input_event.get("variable"),
        "correlation_id": audit_identity["correlation_id"],
        "input_event": input_event,
        "recommendation": None,
        "publishable": None,
        "payload": payload,
    }


def _parse_observed_at(raw_timestamp: Any) -> datetime:
    if isinstance(raw_timestamp, datetime):
        return raw_timestamp.astimezone(timezone.utc)
    if isinstance(raw_timestamp, str):
        return datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
    raise ValueError("Telemetry event timestamp must be an ISO string or datetime")


def is_parametric_control_enabled(project_id: str) -> bool:
    """
    Backend guard.

    This is backed by project.parametric_control_enabled.
    Default is false for safety.

    CONTROL_WORKER_FORCE_ENABLED exists only for manual smoke runs.
    """
    if _env_bool("CONTROL_WORKER_FORCE_ENABLED", False):
        logger.warning(
            "CONTROL_WORKER_FORCE_ENABLED is active; bypassing feature flag for project_id=%s",
            project_id,
        )
        return True

    try:
        from iot_middleware.storage.db_handler import get_project_control_settings

        settings = get_project_control_settings(project_id)
        return bool(settings.get("parametric_control_enabled", False))
    except ImportError:
        logger.warning(
            "get_project_control_settings not available; "
            "parametric control disabled by default",
        )
        return False
    except Exception as exc:
        logger.exception(
            "Could not read control settings for project_id=%s: %s",
            project_id,
            exc,
        )
        return False


def validate_telemetry_event(event: Dict[str, Any]) -> None:
    required = ["project_id", "variable", "value", "timestamp"]
    missing = [key for key in required if key not in event]
    if missing:
        raise ValueError(f"Telemetry event missing required fields: {missing}")


def _build_runtime_event(event: Dict[str, Any]) -> TelemetryStateEvent:
    context = dict(event.get("context") or {})
    context.setdefault("project_id", str(event["project_id"]))

    return TelemetryStateEvent(
        event_id=str(event.get("event_id", f"evt-{uuid.uuid4()}")),
        variable_id=str(event["variable"]),
        value=float(event["value"]),
        source=str(event.get("source", "runtime.telemetry")),
        event_kind=str(event.get("event_kind", "telemetry.observed")),
        observed_at=_parse_observed_at(event["timestamp"]),
        quality=str(event.get("quality", "raw")),
        metadata=dict(event.get("metadata") or {}),
        context=context,
    )


def _build_policy_source(event: TelemetryStateEvent) -> InMemoryPolicySource:
    return _build_inmemory_policy_source(event)


def _build_inmemory_policy_source(event: TelemetryStateEvent) -> InMemoryPolicySource:
    variable = ControlledVariableDefinition(
        variable_id=event.variable_id,
        name=os.getenv(
            "CONTROL_WORKER_VARIABLE_NAME",
            event.variable_id.replace("_", " ").title(),
        ),
        unit=os.getenv("CONTROL_WORKER_VARIABLE_UNIT", "units"),
        actuator_name=os.getenv("CONTROL_WORKER_ACTUATOR_NAME", "control_output"),
        increase_action_label=os.getenv(
            "CONTROL_WORKER_INCREASE_LABEL",
            "increase",
        ),
        decrease_action_label=os.getenv(
            "CONTROL_WORKER_DECREASE_LABEL",
            "decrease",
        ),
        hold_action_label=os.getenv("CONTROL_WORKER_HOLD_LABEL", "hold"),
        description="Runtime-bound static control variable definition",
    )
    binding = MonovariableControlBinding(
        variable=variable,
        setpoint=SetpointReference(
            value=DEFAULT_SETPOINT,
            label=os.getenv("CONTROL_WORKER_SETPOINT_LABEL", "runtime-setpoint"),
            metadata={"source": "control-engine-worker"},
        ),
        parameters=ControlParameters(
            gain=DEFAULT_GAIN,
            deadband=DEFAULT_DEADBAND,
            min_action=DEFAULT_MIN_ACTION,
            max_action=_optional_float(DEFAULT_MAX_ACTION),
        ),
        recommendation_channel=RECOMMENDATION_QUEUE,
        context={"project_id": event.context.get("project_id")},
    )

    required_context: Dict[str, Any] = {}
    required_sector = os.getenv("CONTROL_WORKER_REQUIRED_SECTOR")
    if required_sector:
        required_context["sector"] = required_sector

    policy = StaticPolicyDefinition(
        policy_id=os.getenv(
            "CONTROL_WORKER_POLICY_ID",
            f"policy::{event.variable_id}",
        ),
        binding=binding,
        required_context=required_context,
        priority=int(os.getenv("CONTROL_WORKER_POLICY_PRIORITY", "0")),
        version=int(os.getenv("CONTROL_WORKER_POLICY_VERSION", "1")),
        policy_type="proportional",
        params={
            "setpoint_value": DEFAULT_SETPOINT,
            "gain": DEFAULT_GAIN,
            "deadband": DEFAULT_DEADBAND,
            "min_action": DEFAULT_MIN_ACTION,
            "max_action": _optional_float(DEFAULT_MAX_ACTION),
        },
        description="Static runtime policy resolved by control_engine_worker",
    )
    return InMemoryPolicySource([policy])


def _build_postgresql_policy_source():
    from iot_middleware.services.postgresql_policy_source import PostgreSQLPolicySource

    defaults = {
        "variable_name": os.getenv("CONTROL_WORKER_VARIABLE_NAME"),
        "variable_unit": os.getenv("CONTROL_WORKER_VARIABLE_UNIT", "units"),
        "actuator_name": os.getenv("CONTROL_WORKER_ACTUATOR_NAME", "control_output"),
        "increase_action_label": os.getenv("CONTROL_WORKER_INCREASE_LABEL", "increase"),
        "decrease_action_label": os.getenv("CONTROL_WORKER_DECREASE_LABEL", "decrease"),
        "hold_action_label": os.getenv("CONTROL_WORKER_HOLD_LABEL", "hold"),
        "variable_description": "Runtime-bound project control variable definition",
        "controller_direction": float(os.getenv("CONTROL_WORKER_CONTROLLER_DIRECTION", "1.0")),
        "setpoint_value": DEFAULT_SETPOINT,
        "setpoint_label": os.getenv("CONTROL_WORKER_SETPOINT_LABEL", "runtime-setpoint"),
    }
    return PostgreSQLPolicySource(
        recommendation_channel=RECOMMENDATION_QUEUE,
        defaults=defaults,
    )


def _allow_inmemory_policy_fallback() -> bool:
    return _env_bool("CONTROL_WORKER_ALLOW_INMEMORY_POLICY_FALLBACK", False)


def _resolve_policy_source(event: TelemetryStateEvent):
    policy_source = _build_postgresql_policy_source()
    selection = StaticPolicySelector(policy_source).resolve_event(event)
    return policy_source, selection


def _resolve_policy_selection(event: TelemetryStateEvent):
    try:
        return _resolve_policy_source(event)
    except Exception as exc:
        if not _allow_inmemory_policy_fallback():
            raise
        logger.warning(
            "PostgreSQL policy source unavailable for project_id=%s variable=%s: %s. Using in-memory fallback.",
            event.context.get("project_id"),
            event.variable_id,
            exc,
        )
        policy_source = _build_inmemory_policy_source(event)
        selection = StaticPolicySelector(policy_source).resolve_event(event)
        return policy_source, selection


def _build_policy_evaluator(selection: Any):
    if getattr(selection, "policy_type", "proportional") == "threshold":
        return ThresholdEvaluator()
    return None


def _build_failure_audit_envelope(
    *,
    input_event: Dict[str, Any],
    error: str,
) -> Dict[str, Any]:
    envelope = _build_base_audit_envelope(
        input_event=input_event,
        status=CONTROL_AUDIT_STATUS_ERROR,
    )
    envelope["error"] = error
    envelope["payload"]["error"] = error
    return envelope


def _build_skipped_audit_envelope(
    *,
    input_event: Dict[str, Any],
    reason: str,
) -> Dict[str, Any]:
    envelope = _build_base_audit_envelope(
        input_event=input_event,
        status=CONTROL_AUDIT_STATUS_SKIPPED,
    )
    envelope["skip_reason"] = reason
    envelope["payload"]["skip_reason"] = reason
    return envelope


def _load_rabbitmq_client():
    global _rabbitmq_client

    if _rabbitmq_client is not None:
        return _rabbitmq_client

    from pika import BasicProperties

    from iot_middleware.config import load_config
    from iot_middleware.messaging import create_rabbitmq_client

    config = load_config(_resolve_config_path())
    rabbitmq_config = _apply_rabbitmq_env_overrides(config.rabbitmq)
    client = create_rabbitmq_client(rabbitmq_config)

    if not client.connect():
        raise ConnectionError("Could not connect to RabbitMQ using runtime configuration")

    _rabbitmq_client = (client, BasicProperties)
    return _rabbitmq_client


def _apply_rabbitmq_env_overrides(rabbitmq_config: Any) -> Any:
    overrides: Dict[str, Any] = {}

    env_map = {
        "CONTROL_WORKER_RABBITMQ_HOST": ("host", str),
        "CONTROL_WORKER_RABBITMQ_PORT": ("port", int),
        "CONTROL_WORKER_RABBITMQ_USERNAME": ("username", str),
        "CONTROL_WORKER_RABBITMQ_PASSWORD": ("password", str),
        "CONTROL_WORKER_RABBITMQ_VHOST": ("virtual_host", str),
        "CONTROL_WORKER_RABBITMQ_EXCHANGE": ("exchange", str),
        "CONTROL_WORKER_RABBITMQ_HEARTBEAT": ("heartbeat", int),
        "CONTROL_WORKER_RABBITMQ_CONNECTION_ATTEMPTS": ("connection_attempts", int),
        "CONTROL_WORKER_RABBITMQ_RETRY_DELAY": ("retry_delay", int),
    }

    for env_name, (field_name, caster) in env_map.items():
        raw = os.getenv(env_name)
        if raw is None or raw == "":
            continue
        overrides[field_name] = caster(raw)

    if not overrides:
        return rabbitmq_config

    if hasattr(rabbitmq_config, "model_copy"):
        return rabbitmq_config.model_copy(update=overrides)
    if hasattr(rabbitmq_config, "copy"):
        return rabbitmq_config.copy(update=overrides)

    for key, value in overrides.items():
        setattr(rabbitmq_config, key, value)
    return rabbitmq_config


def _normalize_telemetry_message(raw_message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Soporta tanto payload plano como envelopes con `payload`.
    """
    if "project_id" in raw_message and "variable" in raw_message:
        return raw_message

    payload = raw_message.get("payload")
    if isinstance(payload, dict) and "project_id" in payload and "variable" in payload:
        return payload

    raise ValueError(
        "Telemetry message must be a raw event or an envelope with payload={project_id, variable, value, timestamp}"
    )


def publish_event(queue_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapter boundary.

    Default mode is stdout for deterministic local smoke runs.
    Set CONTROL_WORKER_PUBLISH_MODE=rabbitmq to use the existing RabbitMQ
    connection helper and publish raw JSON envelopes.

    TODO:
    formalize a canonical recommendation/audit routing contract before wiring a
    long-running consumer/publisher path as the default runtime mode.
    """
    if PUBLISH_MODE == "rabbitmq":
        try:
            client, _ = _load_rabbitmq_client()
            if not client.publish_json(
                routing_key=queue_name,
                payload=payload,
                queue_name=queue_name,
                durable_queue=True,
            ):
                raise ConnectionError(f"Failed to publish payload for routing key {queue_name}")
            logger.info("[PUBLISH_RABBITMQ] queue=%s", queue_name)
            return {
                "status": "published",
                "transport": "rabbitmq",
                "routing_key": queue_name,
            }
        except Exception as exc:
            logger.warning(
                "RabbitMQ publish unavailable for queue=%s: %s. Falling back to stdout.",
                queue_name,
                exc,
            )
            fallback_error = str(exc)
        else:  # pragma: no cover
            fallback_error = None
    else:
        fallback_error = None

    logger.info(
        "[PUBLISH_STDOUT] queue=%s payload=%s",
        queue_name,
        json.dumps(payload, ensure_ascii=False, default=str),
    )
    return {
        "status": "published_stdout" if PUBLISH_MODE == "stdout" else "fallback_stdout",
        "transport": "stdout",
        "routing_key": queue_name,
        "error": fallback_error,
    }


def _persist_audit_envelope(audit_payload: Dict[str, Any], *, action: str) -> Dict[str, Any]:
    """Persistencia best-effort del audit envelope en PostgreSQL."""
    try:
        from iot_middleware.storage.db_handler import persist_control_audit_record

        persistence_result = persist_control_audit_record(audit_payload, action=action)
        if isinstance(persistence_result, dict):
            return persistence_result
        if not persistence_result:
            logger.warning("Control audit persistence returned false action=%s", action)
            return _build_audit_persistence_metadata(
                status=CONTROL_AUDIT_PERSISTENCE_STATUS_FAILED,
                attempted=True,
                attempted_at=utc_now_iso(),
                completed_at=utc_now_iso(),
                rows_affected=0,
                error="persist_control_audit_record returned false",
                action=action,
            )
        return _build_audit_persistence_metadata(
            status=CONTROL_AUDIT_PERSISTENCE_STATUS_PERSISTED,
            attempted=True,
            attempted_at=utc_now_iso(),
            completed_at=utc_now_iso(),
            rows_affected=1,
            action=action,
        )
    except Exception as exc:
        logger.warning("Control audit persistence unavailable action=%s: %s", action, exc)
        return _build_audit_persistence_metadata(
            status=CONTROL_AUDIT_PERSISTENCE_STATUS_FAILED,
            attempted=True,
            attempted_at=utc_now_iso(),
            completed_at=utc_now_iso(),
            rows_affected=0,
            action=action,
            error=str(exc),
        )


def _enrich_processed_audit_envelope(
    *,
    audit_payload: Dict[str, Any],
    input_event: Dict[str, Any],
    selection: Any,
    publish_payload: Dict[str, Any],
) -> Dict[str, Any]:
    audit_payload.setdefault("message_type", CONTROL_AUDIT_MESSAGE_TYPE)
    audit_payload.setdefault("timestamp", utc_now_iso())
    audit_payload["status"] = CONTROL_AUDIT_STATUS_PROCESSED
    audit_payload["project_id"] = input_event.get("project_id")
    audit_payload["variable"] = input_event.get("variable")
    audit_payload["correlation_id"] = _build_correlation_id(input_event)
    audit_payload["input_event"] = input_event
    audit_payload["publishable"] = publish_payload

    payload = audit_payload.setdefault("payload", {})
    payload["project_id"] = input_event.get("project_id")
    payload["event_id"] = payload.get("event_id") or input_event.get("event_id")
    payload["variable_id"] = payload.get("variable_id") or input_event.get("variable")
    payload["correlation_id"] = audit_payload["correlation_id"]
    payload["policy_selection"] = {
        "policy_id": selection.policy_id,
        "selector_name": selection.selector_name,
        "priority": selection.priority,
        "version": selection.version,
        "policy_type": selection.policy_type,
        "selection_trace": [_safe_to_dict(entry) for entry in selection.selection_trace],
    }
    payload["input_event"] = input_event
    payload.setdefault("delivery", _build_delivery_metadata())
    return audit_payload


def handle_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    validate_telemetry_event(event)

    project_id = str(event["project_id"])
    if not is_parametric_control_enabled(project_id):
        audit_payload = _build_skipped_audit_envelope(
            input_event=event,
            reason=CONTROL_SKIP_REASON_FEATURE_FLAG_DISABLED,
        )
        _mark_audit_persistence_pending(audit_payload)
        audit_publish_result = publish_event(AUDIT_QUEUE, audit_payload)
        audit_payload["payload"]["delivery"]["audit_publish"] = audit_publish_result
        persistence_result = _persist_audit_envelope(
            audit_payload,
            action=CONTROL_AUDIT_ACTION_SKIPPED_BY_FEATURE_FLAG,
        )
        audit_payload["payload"]["delivery"]["audit_persistence"] = persistence_result
        logger.info(
            "Parametric control disabled; skipping event project_id=%s variable=%s",
            project_id,
            event.get("variable"),
        )
        return {
            "publish_envelope": None,
            "audit_envelope": audit_payload,
        }

    try:
        runtime_event = _build_runtime_event(event)
        _, selection = _resolve_policy_selection(runtime_event)

        recommendation = EventDrivenRecommendationAdapter(
            binding=selection.binding,
            evaluator=_build_policy_evaluator(selection),
        ).evaluate_event(runtime_event)
        sink_output = sink_adapter.build_sink_output(recommendation)

        publish_payload = _safe_to_dict(sink_output.publish_envelope)
        publish_payload.setdefault("payload", {})
        publish_payload["message_type"] = CONTROL_RECOMMENDATION_MESSAGE_TYPE
        publish_payload["payload"]["project_id"] = project_id
        publish_payload["payload"]["policy_id"] = selection.policy_id
        publish_payload["payload"]["policy_type"] = selection.policy_type
        publish_payload["payload"]["policy_version"] = selection.version
        publish_payload["payload"]["policy_priority"] = selection.priority

        audit_payload = _enrich_processed_audit_envelope(
            audit_payload=_safe_to_dict(sink_output.audit_envelope),
            input_event=event,
            selection=selection,
            publish_payload=publish_payload,
        )
        recommendation_publish_result = publish_event(RECOMMENDATION_QUEUE, publish_payload)
        audit_payload["payload"]["delivery"]["recommendation_publish"] = recommendation_publish_result
        _mark_audit_persistence_pending(audit_payload)
        audit_publish_result = publish_event(AUDIT_QUEUE, audit_payload)
        audit_payload["payload"]["delivery"]["audit_publish"] = audit_publish_result
        persistence_result = _persist_audit_envelope(
            audit_payload,
            action=CONTROL_AUDIT_ACTION_RECOMMENDATION_EMITTED,
        )
        audit_payload["payload"]["delivery"]["audit_persistence"] = persistence_result

        logger.info(
            "[CONTROL] project=%s variable=%s value=%s recommendation=%s",
            project_id,
            runtime_event.variable_id,
            runtime_event.value,
            json.dumps(publish_payload.get("payload", {}), ensure_ascii=False, default=str),
        )

        return {
            "publish_envelope": publish_payload,
            "audit_envelope": audit_payload,
        }

    except Exception as exc:
        audit_payload = _build_failure_audit_envelope(
            input_event=event,
            error=str(exc),
        )
        _mark_audit_persistence_pending(audit_payload)
        audit_publish_result = publish_event(AUDIT_QUEUE, audit_payload)
        audit_payload["payload"]["delivery"]["audit_publish"] = audit_publish_result
        persistence_result = _persist_audit_envelope(
            audit_payload,
            action=CONTROL_AUDIT_ACTION_EVALUATION_FAILED,
        )
        audit_payload["payload"]["delivery"]["audit_persistence"] = persistence_result

        logger.exception(
            "Control evaluation failed project_id=%s variable=%s",
            project_id,
            event.get("variable"),
        )
        return None


def run_once_from_json(raw_json: str) -> Optional[Dict[str, Any]]:
    event = json.loads(raw_json)
    return handle_event(event)


def consume_rabbitmq_events(
    *,
    max_messages: Optional[int] = None,
    idle_timeout_seconds: Optional[float] = None,
) -> int:
    """
    Consumer runtime for telemetry.events -> control engine -> RabbitMQ/stdout.

    Polling con `basic_get` evita introducir lógica de control fuera del worker y
    mantiene un smoke determinista de un solo mensaje.
    """
    client, _ = _load_rabbitmq_client()
    if not client.declare_topic_queue(
        queue_name=TELEMETRY_CONSUMER_QUEUE,
        routing_keys=[TELEMETRY_ROUTING_KEY],
        durable=True,
    ):
        raise ConnectionError(
            f"Could not declare/bind consumer queue {TELEMETRY_CONSUMER_QUEUE} -> {TELEMETRY_ROUTING_KEY}"
        )

    processed = 0
    idle_started_at = time.monotonic()

    while True:
        message = client.get_json_message(
            queue_name=TELEMETRY_CONSUMER_QUEUE,
            auto_ack=False,
        )
        if message is None:
            if idle_timeout_seconds is not None:
                idle_elapsed = time.monotonic() - idle_started_at
                if idle_elapsed >= idle_timeout_seconds:
                    return processed
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        idle_started_at = time.monotonic()
        delivery_tag = message.get("delivery_tag")
        raw_payload = message.get("payload") or {}

        try:
            event = _normalize_telemetry_message(raw_payload)
            handle_event(event)
        except Exception as exc:
            logger.exception("Failed to consume telemetry message from RabbitMQ")
            publish_event(
                AUDIT_QUEUE,
                _build_failure_audit_envelope(
                    input_event={"raw_message": raw_payload},
                    error=str(exc),
                ),
            )
        finally:
            if delivery_tag is not None:
                client.ack_message(delivery_tag)

        processed += 1
        if max_messages is not None and processed >= max_messages:
            return processed


def run() -> None:
    """
    Long-running consumer entrypoint.

    This remains intentionally non-invasive:
    - no ingestor changes;
    - no parallel control flow;
    - no control logic outside parametric-control-engine.
    """
    logger.info(
        "Control Engine Worker started input_queue=%s input_routing_key=%s recommendation=%s audit=%s publish_mode=%s",
        TELEMETRY_CONSUMER_QUEUE,
        TELEMETRY_ROUTING_KEY,
        RECOMMENDATION_QUEUE,
        AUDIT_QUEUE,
        PUBLISH_MODE,
    )
    processed = consume_rabbitmq_events()
    logger.info("Control Engine Worker stopped processed_messages=%s", processed)


if __name__ == "__main__":
    raw = os.getenv("CONTROL_WORKER_TEST_EVENT")
    max_messages = os.getenv("CONTROL_WORKER_MAX_MESSAGES")
    idle_timeout_seconds = os.getenv("CONTROL_WORKER_IDLE_TIMEOUT_SECONDS")

    if raw:
        run_once_from_json(raw)
    elif max_messages or idle_timeout_seconds:
        consume_rabbitmq_events(
            max_messages=int(max_messages) if max_messages else None,
            idle_timeout_seconds=float(idle_timeout_seconds) if idle_timeout_seconds else None,
        )
    else:
        run()
