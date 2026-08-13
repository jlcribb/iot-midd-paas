#!/usr/bin/env python3

"""
Smoke oficial de consolidación del flujo de control paramétrico.

El objetivo es distinguir con honestidad qué niveles quedaron realmente
validados:

- contract-level
- component-level
- broker-level
- database-level
- full E2E

Exit codes:
- 0: todo lo ejecutado quedó en PASS y no hubo SKIP/WARN
- 1: hubo al menos un FAIL
- 2: no hubo FAIL, pero sí SKIP/WARN
"""

from __future__ import annotations

import json
import os
import socket
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from threading import Event
from types import SimpleNamespace
from typing import Any, Dict, Iterator, List, Tuple
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

try:
    import paho.mqtt.client as mqtt
except Exception:  # pragma: no cover - import availability is part of smoke preflight
    mqtt = None


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(REPO_ROOT, "src")
ENGINE_SRC = os.path.join(REPO_ROOT, "apps", "parametric-control-engine", "src")

for path in [SRC_ROOT, ENGINE_SRC]:
    if path not in sys.path:
        sys.path.insert(0, path)


from iot_middleware.config import RabbitMQConfig  # noqa: E402
from iot_middleware.services import control_engine_worker as worker  # noqa: E402
from iot_middleware.services.control_runtime_contract import (  # noqa: E402
    CONTROL_AUDIT_ACTION_EVALUATION_FAILED,
    CONTROL_AUDIT_ACTION_RECOMMENDATION_EMITTED,
    CONTROL_AUDIT_ACTION_SKIPPED_BY_FEATURE_FLAG,
    CONTROL_AUDIT_ROUTING_KEY,
    CONTROL_AUDIT_STATUS_ERROR,
    CONTROL_AUDIT_STATUS_PROCESSED,
    CONTROL_AUDIT_STATUS_SKIPPED,
    CONTROL_RECOMMENDATIONS_ROUTING_KEY,
    TELEMETRY_EVENTS_ROUTING_KEY,
)
from iot_middleware.messaging import create_rabbitmq_client  # noqa: E402
from iot_middleware.services.ingestor import ControlTelemetryPublisher  # noqa: E402
from iot_middleware.storage import db_handler as runtime_db_handler  # noqa: E402


PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"
WARN = "WARN"

LEVELS = [
    "contract-level",
    "component-level",
    "broker-level",
    "database-level",
    "full E2E",
]

RUN_ID = uuid.uuid4().hex
# Every execution owns a complete fixture. No persisted project, policy or
# topology identifier is reused, which makes cleanup unambiguous.
TEST_PROJECT_ID = os.getenv("CONTROL_TEST_PROJECT_ID", str(uuid.uuid4()))
TEST_VARIABLE_ID = os.getenv("CONTROL_TEST_VARIABLE", "tank_level")
TEST_SECTOR = os.getenv("CONTROL_TEST_SECTOR", "tank_A")
TEST_SECTOR_ID = str(uuid.uuid4())
TEST_SOURCE_ASSET_ID = str(uuid.uuid4())
TEST_TARGET_ASSET_ID = str(uuid.uuid4())
TEST_POLICY_ID = str(uuid.uuid4())
TEST_BINDING_ID = str(uuid.uuid4())
TEST_EVENT_ID = f"evt-e2e-{RUN_ID}"
SMOKE_RECOMMENDATION_QUEUE = os.getenv("CONTROL_SMOKE_RECOMMENDATION_QUEUE", "")
SMOKE_AUDIT_QUEUE = os.getenv("CONTROL_SMOKE_AUDIT_QUEUE", "")
SMOKE_SIMULATED_QUEUE = os.getenv("CONTROL_SMOKE_SIMULATED_QUEUE", "")
DEFAULT_RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
DEFAULT_RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
DEFAULT_MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
DEFAULT_MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))


def configure_host_runtime_defaults() -> None:
    """
    Align host-side smoke execution with Docker Compose published ports.

    The canonical smoke command runs from the repo host, not from inside the
    Compose network. In that context, config.yaml points PostgreSQL to the
    service DNS name `postgresql`, which is only resolvable from containers.
    """
    if os.path.exists("/.dockerenv"):
        return

    host_defaults = {
        "DB_HOST": "localhost",
        "POSTGRES_HOST": "localhost",
        "DB_PORT": "5432",
        "POSTGRES_PORT": "5432",
        "DB_NAME": "iot_middleware",
        "POSTGRES_DB": "iot_middleware",
        "DB_USER": "iot_user",
        "POSTGRES_USER": "iot_user",
        "DB_PASSWORD": "iot_password_2024",
        "POSTGRES_PASSWORD": "iot_password_2024",
    }

    for env_name, env_value in host_defaults.items():
        os.environ.setdefault(env_name, env_value)

    runtime_db_handler._get_control_settings_connection_url.cache_clear()
    runtime_db_handler._get_control_settings_engine.cache_clear()
    runtime_db_handler._get_control_runtime_session_factory.cache_clear()


configure_host_runtime_defaults()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def scenario(status: str, name: str, detail: str, **data: Any) -> Dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "detail": detail,
        "data": data,
    }


def tcp_check(host: str, port: int, *, timeout: float = 1.5) -> Tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, f"{host}:{port} reachable"
    except OSError as exc:
        return False, f"{host}:{port} unavailable: {exc}"


def fetch_json(url: str) -> Dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json"})
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def build_postgres_engine():
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "iot_middleware")
    db_user = os.getenv("DB_USER", "iot_user")
    db_password = os.getenv("DB_PASSWORD", "iot_password_2024")
    return create_engine(
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}",
        pool_pre_ping=True,
    )


def can_connect_postgres() -> Tuple[bool, str]:
    try:
        engine = build_postgres_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "PostgreSQL reachable"
    except SQLAlchemyError as exc:
        return False, f"PostgreSQL unavailable: {exc}"


def build_rabbitmq_client():
    config = RabbitMQConfig(
        host=DEFAULT_RABBITMQ_HOST,
        port=DEFAULT_RABBITMQ_PORT,
        username=os.getenv("RABBITMQ_USERNAME", "guest"),
        password=os.getenv("RABBITMQ_PASSWORD", "guest"),
        virtual_host=os.getenv("RABBITMQ_VHOST", "/"),
        exchange=os.getenv("RABBITMQ_EXCHANGE", "iot_middleware"),
        queue_prefix="iot",
        heartbeat=600,
        connection_attempts=3,
        retry_delay=5,
        enable_monitoring=True,
    )
    client = create_rabbitmq_client(config)
    if not client.connect():
        raise ConnectionError("No se pudo conectar a RabbitMQ")
    return client


@contextmanager
def patched_worker_runtime(**overrides: Any) -> Iterator[None]:
    patches = [patch.object(worker, name, value) for name, value in overrides.items()]
    for item in patches:
        item.start()
    try:
        yield
    finally:
        while patches:
            patches.pop().stop()


def build_valid_event(*, event_id: str | None = None, value: float = 72.5) -> Dict[str, Any]:
    return {
        "event_id": event_id or f"evt-component-{uuid.uuid4().hex}",
        "project_id": TEST_PROJECT_ID,
        "variable": TEST_VARIABLE_ID,
        "value": value,
        "timestamp": now_iso(),
        "source": "runtime.ingestor",
        "event_kind": "telemetry.observed",
        "quality": "good",
        "metadata": {
            "topic": f"iot/{TEST_PROJECT_ID}/unit-smoke/device-smoke/{TEST_VARIABLE_ID}",
        },
        "context": {
            "sector": TEST_SECTOR,
            "unit_id": "unit-smoke",
            "device_id": "device-smoke",
            "asset_id": TEST_SOURCE_ASSET_ID,
            "location_id": "location-smoke",
        },
    }


def build_invalid_event() -> Dict[str, Any]:
    return {
        "project_id": TEST_PROJECT_ID,
        "variable": TEST_VARIABLE_ID,
        "value": 72.5,
    }


def build_test_rabbitmq_config() -> RabbitMQConfig:
    return RabbitMQConfig(
        host=DEFAULT_RABBITMQ_HOST,
        port=DEFAULT_RABBITMQ_PORT,
        username=os.getenv("RABBITMQ_USERNAME", "guest"),
        password=os.getenv("RABBITMQ_PASSWORD", "guest"),
        virtual_host=os.getenv("RABBITMQ_VHOST", "/"),
        exchange=os.getenv("RABBITMQ_EXCHANGE", "iot_middleware"),
        queue_prefix="iot",
        heartbeat=600,
        connection_attempts=3,
        retry_delay=5,
        enable_monitoring=True,
    )


def build_component_level_policy_selection(runtime_event: Any):
    source = worker._build_inmemory_policy_source(runtime_event)
    selection = worker.StaticPolicySelector(source).resolve_event(runtime_event)
    return source, selection


def ensure_project(engine, *, enabled: bool) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO public.projects (
                    id,
                    name,
                    description,
                    status,
                    metadata,
                    created_at,
                    updated_at,
                    parametric_control_enabled
                )
                VALUES (
                    CAST(:project_id AS uuid),
                    :name,
                    :description,
                    CAST(:status AS project_status_enum),
                    '{}'::jsonb,
                    now(),
                    now(),
                    :enabled
                )
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status,
                    updated_at = now(),
                    parametric_control_enabled = EXCLUDED.parametric_control_enabled
                """
            ),
            {
                "project_id": TEST_PROJECT_ID,
                "name": "control-engine-e2e-project",
                "description": "Proyecto de smoke end-to-end del control engine",
                "status": "active",
                "enabled": enabled,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO public.sectors (id, project_id, name)
                VALUES (CAST(:sector_id AS uuid), CAST(:project_id AS uuid), :name)
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"sector_id": TEST_SECTOR_ID, "project_id": TEST_PROJECT_ID, "name": f"smoke-{RUN_ID}"},
        )
        connection.execute(
            text(
                """
                INSERT INTO public.assets (id, project_id, sector_id, asset_type, subtype, name, status, metadata)
                VALUES
                  (CAST(:source_id AS uuid), CAST(:project_id AS uuid), CAST(:sector_id AS uuid),
                   CAST('sensor' AS asset_type_enum), 'smoke', 'source', 'active', '{}'::jsonb),
                  (CAST(:target_id AS uuid), CAST(:project_id AS uuid), CAST(:sector_id AS uuid),
                   CAST('actuator' AS asset_type_enum), 'smoke', 'target', 'active',
                   '{"control_capabilities":[{"key":"relay_1","operations":["set"]}]}'::jsonb)
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "source_id": TEST_SOURCE_ASSET_ID,
                "target_id": TEST_TARGET_ASSET_ID,
                "project_id": TEST_PROJECT_ID,
                "sector_id": TEST_SECTOR_ID,
            },
        )


def replace_policy(engine, *, enabled: bool) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DELETE FROM public.project_control_policies
                WHERE project_id = CAST(:project_id AS uuid)
                  AND variable = :variable
                """
            ),
            {
                "project_id": TEST_PROJECT_ID,
                "variable": TEST_VARIABLE_ID,
            },
        )
        if not enabled:
            return

        connection.execute(
            text(
                """
                INSERT INTO public.project_control_policies (
                    id,
                    project_id,
                    bound_asset_id,
                    variable,
                    context_selector,
                    policy_type,
                    params,
                    priority,
                    enabled,
                    version
                )
                VALUES (
                    CAST(:policy_id AS uuid),
                    CAST(:project_id AS uuid),
                    CAST(:source_asset_id AS uuid),
                    :variable,
                    CAST(:context_selector AS jsonb),
                    'proportional',
                    CAST(:params AS jsonb),
                    10,
                    TRUE,
                    1
                )
                """
            ),
            {
                "policy_id": TEST_POLICY_ID,
                "project_id": TEST_PROJECT_ID,
                "source_asset_id": TEST_SOURCE_ASSET_ID,
                "variable": TEST_VARIABLE_ID,
                "context_selector": json.dumps({"sector": TEST_SECTOR}),
                "params": json.dumps(
                    {
                        "variable_name": "Tank Level",
                        "variable_unit": "units",
                        "actuator_name": "control_output",
                        "setpoint_value": 70.0,
                        "gain": 1.0,
                        "deadband": 0.0,
                        "min_action": 0.0,
                    }
                ),
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO public.project_control_policy_actuation_bindings
                    (id, policy_id, project_id, source_asset_id, target_asset_id, control_point, operation, version)
                VALUES
                    (CAST(:binding_id AS uuid), CAST(:policy_id AS uuid), CAST(:project_id AS uuid),
                     CAST(:source_asset_id AS uuid), CAST(:target_asset_id AS uuid), 'relay_1', 'set', 1)
                """
            ),
            {
                "binding_id": TEST_BINDING_ID,
                "policy_id": TEST_POLICY_ID,
                "project_id": TEST_PROJECT_ID,
                "source_asset_id": TEST_SOURCE_ASSET_ID,
                "target_asset_id": TEST_TARGET_ASSET_ID,
            },
        )


def wait_for_audit_row(engine, *, event_id: str, timeout_seconds: float = 20.0) -> Dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    query = text(
        """
        SELECT
            id,
            ts,
            accion,
            entidad,
            cambios
        FROM iot_schema.auditoria
        WHERE entidad = 'control_engine_worker'
          AND (
            cambios->'payload'->>'event_id' = :event_id
            OR cambios->'payload'->'input_event'->>'event_id' = :event_id
            OR cambios->'input_event'->>'event_id' = :event_id
          )
        ORDER BY ts DESC
        LIMIT 1
        """
    )

    while time.monotonic() < deadline:
        with engine.connect() as connection:
            row = connection.execute(query, {"event_id": event_id}).mappings().first()
        if row:
            return {
                "id": row["id"],
                "ts": row["ts"].isoformat() if hasattr(row["ts"], "isoformat") else str(row["ts"]),
                "action": row["accion"],
                "entity": row["entidad"],
                "envelope": row["cambios"],
            }
        time.sleep(0.5)

    raise TimeoutError(f"No se persistió auditoría para event_id={event_id}")


def get_audit_delivery_metadata(envelope: Dict[str, Any]) -> Dict[str, Any]:
    payload = envelope.get("payload") if isinstance(envelope, dict) else {}
    payload = payload if isinstance(payload, dict) else {}
    delivery = payload.get("delivery") if isinstance(payload, dict) else {}
    delivery = delivery if isinstance(delivery, dict) else {}
    return {
        "recommendation_publish": delivery.get("recommendation_publish") or {},
        "audit_publish": delivery.get("audit_publish") or {},
        "audit_persistence": delivery.get("audit_persistence") or {},
    }


def evaluate_audit_consistency(audit_row: Dict[str, Any]) -> List[Dict[str, Any]]:
    delivery = get_audit_delivery_metadata(audit_row.get("envelope") or {})
    audit_publish = delivery["audit_publish"]
    audit_persistence = delivery["audit_persistence"]

    scenarios = [
        scenario(
            PASS if audit_publish.get("status") == "published" and audit_publish.get("transport") == "rabbitmq" else FAIL,
            "audit_publish",
            "La auditoría publicada declara transporte RabbitMQ real" if audit_publish.get("status") == "published" and audit_publish.get("transport") == "rabbitmq" else "La metadata de publicación de auditoría no refleja un publish RabbitMQ confirmado",
            audit_publish=audit_publish,
        ),
        scenario(
            PASS if audit_persistence.get("attempted") is True else FAIL,
            "audit_persistence_attempt",
            "La auditoría declara intento explícito de persistencia" if audit_persistence.get("attempted") is True else "La auditoría no declara intento explícito de persistencia",
            audit_persistence=audit_persistence,
        ),
        scenario(
            PASS if audit_row.get("id") is not None else FAIL,
            "audit_database_row",
            "La fila de auditoría fue encontrada en PostgreSQL" if audit_row.get("id") is not None else "No se encontró la fila de auditoría en PostgreSQL",
            audit_row_id=audit_row.get("id"),
        ),
    ]

    metadata_consistent = (
        audit_persistence.get("status") == "persisted"
        and audit_persistence.get("rows_affected") == 1
        and audit_persistence.get("row_id") == audit_row.get("id")
    )
    scenarios.append(
        scenario(
            PASS if metadata_consistent else FAIL,
            "audit_metadata_consistency",
            "La metadata persisted coincide con la fila observada" if metadata_consistent else "La metadata de persistencia no coincide con la fila observada",
            audit_persistence=audit_persistence,
            audit_row_id=audit_row.get("id"),
        )
    )
    return scenarios


def wait_for_simulated_delivery(engine, *, correlation_id: str, timeout_seconds: float = 30.0) -> Dict[str, Any]:
    """Verify the persisted result of the outbox → dispatch path without using legacy queues."""
    deadline = time.monotonic() + timeout_seconds
    query = text(
        """
        SELECT i.command_id, i.recommendation_id, i.correlation_id, i.policy_id,
               i.policy_version, i.source_asset_id, i.target_asset_id,
               i.actuation_binding_id, i.actuation_binding_version, i.status,
               i.simulated, o.event_id, o.status AS outbox_status, o.payload
        FROM public.control_actuation_delivery_intents i
        JOIN public.control_actuation_outbox o ON o.command_id = i.command_id
        WHERE i.project_id = CAST(:project_id AS uuid)
          AND i.correlation_id = :correlation_id
        ORDER BY i.created_at DESC
        LIMIT 1
        """
    )
    while time.monotonic() < deadline:
        with engine.connect() as connection:
            row = connection.execute(
                query,
                {"project_id": TEST_PROJECT_ID, "correlation_id": correlation_id},
            ).mappings().first()
        if row and row["status"] == "acknowledged" and row["outbox_status"] == "published":
            payload = dict(row["payload"] or {})
            if payload.get("simulated") is not True or payload.get("physical_effects") is not False:
                raise AssertionError("dispatch payload must remain simulated with physical_effects=false")
            return {key: (str(value) if key.endswith("_id") and value is not None else value) for key, value in row.items()}
        time.sleep(0.5)
    raise TimeoutError("No se alcanzó un intent acknowledged con outbox published")


def cleanup_fixture(engine) -> None:
    """Remove only rows identifiable by this execution's random project id."""
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DELETE FROM iot_schema.auditoria
                WHERE cambios->'payload'->>'project_id' = :project_id
                   OR cambios->>'project_id' = :project_id
                """
            ),
            {"project_id": TEST_PROJECT_ID},
        )
        connection.execute(
            text("DELETE FROM public.control_actuation_outbox WHERE project_id = CAST(:project_id AS uuid)"),
            {"project_id": TEST_PROJECT_ID},
        )
        connection.execute(
            text("DELETE FROM public.control_actuation_delivery_intents WHERE project_id = CAST(:project_id AS uuid)"),
            {"project_id": TEST_PROJECT_ID},
        )
        connection.execute(
            text("DELETE FROM public.projects WHERE id = CAST(:project_id AS uuid)"),
            {"project_id": TEST_PROJECT_ID},
        )


def publish_mqtt_message(event_id: str) -> Dict[str, Any]:
    if mqtt is None:
        raise RuntimeError("paho-mqtt no está disponible")

    payload = {
        "event_id": event_id,
        "value": float(os.getenv("CONTROL_TEST_VALUE", "72.5")),
        "timestamp": now_iso(),
        "sector": TEST_SECTOR,
        "location_id": "location-smoke",
        "asset_id": TEST_SOURCE_ASSET_ID,
    }
    topic = f"iot/{TEST_PROJECT_ID}/unit-smoke/device-smoke/{TEST_VARIABLE_ID}"

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv311)
    state = {
        "published": False,
        "connect_error": None,
        "publish_error": None,
    }
    connected_event = Event()
    published_event = Event()
    disconnected_event = Event()

    def on_connect(mqtt_client, _userdata, _connect_flags, reason_code, _properties):
        if reason_code != 0:
            state["connect_error"] = f"No se pudo conectar a MQTT rc={reason_code}"
            connected_event.set()
            mqtt_client.disconnect()
            return

        connected_event.set()
        result = mqtt_client.publish(topic, json.dumps(payload), qos=1)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            state["publish_error"] = f"Fallo publicando mensaje MQTT rc={result.rc}"
            published_event.set()
            mqtt_client.disconnect()

    def on_publish(mqtt_client, _userdata, _mid, _reason_codes, _properties):
        state["published"] = True
        published_event.set()
        mqtt_client.disconnect()

    def on_disconnect(_mqtt_client, _userdata, _disconnect_flags, _reason_code, _properties):
        disconnected_event.set()

    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    client.connect(DEFAULT_MQTT_HOST, DEFAULT_MQTT_PORT, 60)
    client.loop_start()

    try:
        if not connected_event.wait(timeout=10.0):
            raise TimeoutError(f"Timeout conectando a MQTT {DEFAULT_MQTT_HOST}:{DEFAULT_MQTT_PORT}")
        if state["connect_error"]:
            raise ConnectionError(state["connect_error"])
        if not published_event.wait(timeout=10.0):
            raise TimeoutError("Timeout publicando mensaje MQTT")
        if state["publish_error"]:
            raise RuntimeError(state["publish_error"])
        if not disconnected_event.wait(timeout=10.0):
            raise TimeoutError("Timeout esperando desconexión MQTT")
    finally:
        client.loop_stop()

    if not state["published"]:
        raise RuntimeError("El mensaje MQTT no se publicó correctamente")

    return {
        "topic": topic,
        "payload": payload,
    }


def run_contract_level() -> Dict[str, Any]:
    scenarios: List[Dict[str, Any]] = []

    publisher = ControlTelemetryPublisher(
        build_test_rabbitmq_config(),
        ingesta_config={"control_telemetry_enabled": True},
    )
    canonical_event = publisher.build_event(
        {
            "event_id": TEST_EVENT_ID,
            "project_id": TEST_PROJECT_ID,
            "sensor_type": TEST_VARIABLE_ID,
            "value": 72.5,
            "timestamp": now_iso(),
            "topic": f"iot/{TEST_PROJECT_ID}/unit-smoke/device-smoke/{TEST_VARIABLE_ID}",
            "unit_id": "unit-smoke",
            "device_id": "device-smoke",
            "sector": TEST_SECTOR,
            "quality": "good",
        }
    )

    try:
        if canonical_event is None:
            raise ValueError("ControlTelemetryPublisher no pudo construir el evento canónico")
        worker.validate_telemetry_event(canonical_event)
        normalized = worker._normalize_telemetry_message({"payload": canonical_event})
        if normalized["event_id"] != TEST_EVENT_ID:
            raise ValueError("El event_id normalizado no coincide")
        scenarios.append(
            scenario(
                PASS,
                "canonical_event_contract",
                "El evento canónico de telemetría es compatible entre ingestor y worker",
                canonical_event=canonical_event,
            )
        )
    except Exception as exc:
        scenarios.append(
            scenario(
                FAIL,
                "canonical_event_contract",
                f"Contrato de evento canónico inválido: {exc}",
            )
        )

    try:
        worker.handle_event(build_invalid_event())
        scenarios.append(
            scenario(
                FAIL,
                "invalid_event_rejected",
                "El worker aceptó un evento inválido/incompleto",
            )
        )
    except ValueError as exc:
        scenarios.append(
            scenario(
                PASS,
                "invalid_event_rejected",
                f"El worker rechaza eventos incompletos: {exc}",
            )
        )
    except Exception as exc:
        scenarios.append(
            scenario(
                FAIL,
                "invalid_event_rejected",
                f"El worker falló de forma inesperada ante evento inválido: {exc}",
            )
        )

    level_status = PASS if all(item["status"] == PASS for item in scenarios) else FAIL
    return {
        "level": "contract-level",
        "status": level_status,
        "scenarios": scenarios,
    }


def run_component_level() -> Dict[str, Any]:
    scenarios: List[Dict[str, Any]] = []

    def fake_publish(queue_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "mocked",
            "transport": "memory",
            "routing_key": queue_name,
            "message_type": payload.get("message_type"),
        }

    def fake_persist(_payload: Dict[str, Any], *, action: str) -> Dict[str, Any]:
        return {
            "status": "mocked",
            "store": "memory",
            "action": action,
        }

    disabled_event = build_valid_event(event_id=f"evt-component-disabled-{RUN_ID}")
    with patch.object(worker, "publish_event", side_effect=fake_publish), patch.object(
        worker,
        "_persist_audit_envelope",
        side_effect=fake_persist,
    ), patch.object(worker, "is_parametric_control_enabled", return_value=False):
        result = worker.handle_event(disabled_event)
        if result and result["audit_envelope"]["status"] == CONTROL_AUDIT_STATUS_SKIPPED:
            scenarios.append(
                scenario(
                    PASS,
                    "feature_flag_disabled",
                    "El worker no evalúa policy y audita skipped cuando el feature flag está deshabilitado",
                    audit_envelope=result["audit_envelope"],
                )
            )
        else:
            scenarios.append(
                scenario(
                    FAIL,
                    "feature_flag_disabled",
                    "El worker no emitió el comportamiento esperado para feature flag deshabilitado",
                )
            )

    no_policy_event = build_valid_event(event_id=f"evt-component-no-policy-{RUN_ID}")
    with patch.object(worker, "publish_event", side_effect=fake_publish), patch.object(
        worker,
        "_persist_audit_envelope",
        side_effect=fake_persist,
    ), patch.object(worker, "is_parametric_control_enabled", return_value=True), patch.object(
        worker,
        "_resolve_policy_selection",
        side_effect=ValueError("No static policy found for variable_id='tank_level'"),
    ):
        result = worker.handle_event(no_policy_event)
        if result is None:
            scenarios.append(
                scenario(
                    PASS,
                    "enabled_without_policy",
                    "El worker audita error coherente cuando no existe policy aplicable",
                )
            )
        else:
            scenarios.append(
                scenario(
                    FAIL,
                    "enabled_without_policy",
                    "El worker devolvió un resultado inesperado cuando faltó policy",
                    result=result,
                )
            )

    valid_event = build_valid_event(event_id=f"evt-component-valid-{RUN_ID}")
    with patch.object(worker, "publish_event", side_effect=fake_publish), patch.object(
        worker,
        "_persist_audit_envelope",
        side_effect=fake_persist,
    ), patch.object(worker, "is_parametric_control_enabled", return_value=True), patch.object(
        worker,
        "_resolve_policy_selection",
        side_effect=build_component_level_policy_selection,
    ):
        result = worker.handle_event(valid_event)
        if result and result["audit_envelope"]["status"] == CONTROL_AUDIT_STATUS_PROCESSED:
            scenarios.append(
                scenario(
                    PASS,
                    "enabled_with_valid_policy",
                    "El worker construye recommendation y audit usando el engine oficial",
                    publish_envelope=result["publish_envelope"],
                    audit_envelope=result["audit_envelope"],
                )
            )
        else:
            scenarios.append(
                scenario(
                    FAIL,
                    "enabled_with_valid_policy",
                    "El worker no produjo recommendation/audit válidos con una policy compatible",
                    result=result,
                )
            )

    level_status = PASS if all(item["status"] == PASS for item in scenarios) else FAIL
    return {
        "level": "component-level",
        "status": level_status,
        "scenarios": scenarios,
    }


def read_single_queue_payload(client, queue_name: str) -> Dict[str, Any] | None:
    message = client.get_json_message(queue_name, auto_ack=False)
    if message is None:
        return None
    delivery_tag = message.get("delivery_tag")
    if delivery_tag is not None:
        client.ack_message(delivery_tag)
    return message.get("payload") or {}


def run_broker_level() -> Dict[str, Any]:
    rabbit_ok, rabbit_detail = tcp_check(DEFAULT_RABBITMQ_HOST, DEFAULT_RABBITMQ_PORT)
    if not rabbit_ok:
        return {
            "level": "broker-level",
            "status": SKIP,
            "scenarios": [
                scenario(
                    SKIP,
                    "broker_preflight",
                    rabbit_detail,
                )
            ],
        }

    client = None
    scenarios: List[Dict[str, Any]] = []
    queue_suffix = uuid.uuid4().hex
    input_queue = f"{TELEMETRY_EVENTS_ROUTING_KEY}.smoke.{queue_suffix}"
    recommendation_queue = f"{CONTROL_RECOMMENDATIONS_ROUTING_KEY}.smoke.{queue_suffix}"
    audit_queue = f"{CONTROL_AUDIT_ROUTING_KEY}.smoke.{queue_suffix}"

    try:
        client = build_rabbitmq_client()
        for queue_name in [input_queue, recommendation_queue, audit_queue]:
            client.declare_topic_queue(
                queue_name=queue_name,
                routing_keys=[queue_name],
                durable=True,
                auto_delete=False,
            )
            client.purge_queue(queue_name)

        worker._rabbitmq_client = None
        os.environ.setdefault("CONTROL_WORKER_RABBITMQ_HOST", DEFAULT_RABBITMQ_HOST)
        os.environ.setdefault("CONTROL_WORKER_RABBITMQ_PORT", str(DEFAULT_RABBITMQ_PORT))
        os.environ.setdefault("CONTROL_WORKER_RABBITMQ_USERNAME", os.getenv("RABBITMQ_USERNAME", "guest"))
        os.environ.setdefault("CONTROL_WORKER_RABBITMQ_PASSWORD", os.getenv("RABBITMQ_PASSWORD", "guest"))
        os.environ.setdefault("CONTROL_WORKER_RABBITMQ_VHOST", os.getenv("RABBITMQ_VHOST", "/"))

        with patched_worker_runtime(
            PUBLISH_MODE="rabbitmq",
            TELEMETRY_QUEUE=input_queue,
            TELEMETRY_ROUTING_KEY=input_queue,
            TELEMETRY_CONSUMER_QUEUE=input_queue,
            RECOMMENDATION_QUEUE=recommendation_queue,
            AUDIT_QUEUE=audit_queue,
        ), patch.object(worker, "is_parametric_control_enabled", return_value=True), patch.object(
            worker,
            "_resolve_policy_selection",
            side_effect=build_component_level_policy_selection,
        ):
            valid_event = build_valid_event(event_id=f"evt-broker-valid-{RUN_ID}")
            published = client.publish_json(
                routing_key=input_queue,
                payload=valid_event,
                queue_name=input_queue,
                durable_queue=True,
            )
            processed = worker.consume_rabbitmq_events(max_messages=1, idle_timeout_seconds=5.0)
            recommendation_payload = read_single_queue_payload(client, recommendation_queue)
            audit_payload = read_single_queue_payload(client, audit_queue)

            if (
                published
                and processed == 1
                and recommendation_payload
                and audit_payload
                and audit_payload.get("status") == CONTROL_AUDIT_STATUS_PROCESSED
            ):
                scenarios.append(
                    scenario(
                        PASS,
                        "broker_valid_event",
                        "RabbitMQ transport verificado con queues aisladas para recommendation + audit",
                        input_queue=input_queue,
                        recommendation_queue=recommendation_queue,
                        audit_queue=audit_queue,
                        recommendation_payload=recommendation_payload,
                        audit_payload=audit_payload,
                    )
                )
            else:
                scenarios.append(
                    scenario(
                        FAIL,
                        "broker_valid_event",
                        "La ruta broker-level no produjo recommendation/audit válidos",
                        published=published,
                        processed=processed,
                        recommendation_payload=recommendation_payload,
                        audit_payload=audit_payload,
                    )
                )

        client.purge_queue(input_queue)
        client.purge_queue(recommendation_queue)
        client.purge_queue(audit_queue)

        with patched_worker_runtime(
            PUBLISH_MODE="rabbitmq",
            TELEMETRY_QUEUE=input_queue,
            TELEMETRY_ROUTING_KEY=input_queue,
            TELEMETRY_CONSUMER_QUEUE=input_queue,
            RECOMMENDATION_QUEUE=recommendation_queue,
            AUDIT_QUEUE=audit_queue,
        ):
            invalid_event = build_invalid_event()
            invalid_event["event_id"] = f"evt-broker-invalid-{RUN_ID}"
            published = client.publish_json(
                routing_key=input_queue,
                payload=invalid_event,
                queue_name=input_queue,
                durable_queue=True,
            )
            processed = worker.consume_rabbitmq_events(max_messages=1, idle_timeout_seconds=5.0)
            recommendation_payload = read_single_queue_payload(client, recommendation_queue)
            audit_payload = read_single_queue_payload(client, audit_queue)

            if (
                published
                and processed == 1
                and recommendation_payload is None
                and audit_payload
                and audit_payload.get("status") == CONTROL_AUDIT_STATUS_ERROR
            ):
                scenarios.append(
                    scenario(
                        PASS,
                        "broker_invalid_event",
                        "RabbitMQ transport conserva audit error y no emite recommendation para evento inválido",
                        audit_payload=audit_payload,
                    )
                )
            else:
                scenarios.append(
                    scenario(
                        FAIL,
                        "broker_invalid_event",
                        "Broker-level no reflejó el error esperado para un evento inválido",
                        published=published,
                        processed=processed,
                        recommendation_payload=recommendation_payload,
                        audit_payload=audit_payload,
                    )
                )

        level_status = PASS if all(item["status"] == PASS for item in scenarios) else FAIL
        return {
            "level": "broker-level",
            "status": level_status,
            "scenarios": scenarios,
        }
    except Exception as exc:
        return {
            "level": "broker-level",
            "status": FAIL,
            "scenarios": [
                scenario(
                    FAIL,
                    "broker_level_runtime",
                    f"Falló la validación broker-level: {exc}",
                )
            ],
        }
    finally:
        worker._rabbitmq_client = None
        if client is not None:
            try:
                client.disconnect()
            except Exception:
                pass


def run_database_level() -> Dict[str, Any]:
    postgres_ok, postgres_detail = can_connect_postgres()
    if not postgres_ok:
        return {
            "level": "database-level",
            "status": SKIP,
            "scenarios": [
                scenario(
                    SKIP,
                    "database_preflight",
                    postgres_detail,
                )
            ],
        }

    engine = build_postgres_engine()
    scenarios: List[Dict[str, Any]] = []

    def fake_publish(queue_name: str, _payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "mocked",
            "transport": "memory",
            "routing_key": queue_name,
        }

    cases = [
        {
            "name": "db_feature_flag_disabled",
            "enabled": False,
            "with_policy": False,
            "expected_action": CONTROL_AUDIT_ACTION_SKIPPED_BY_FEATURE_FLAG,
            "expected_status": CONTROL_AUDIT_STATUS_SKIPPED,
        },
        {
            "name": "db_enabled_without_policy",
            "enabled": True,
            "with_policy": False,
            "expected_action": CONTROL_AUDIT_ACTION_EVALUATION_FAILED,
            "expected_status": CONTROL_AUDIT_STATUS_ERROR,
        },
        {
            "name": "db_enabled_with_valid_policy",
            "enabled": True,
            "with_policy": True,
            "expected_action": CONTROL_AUDIT_ACTION_RECOMMENDATION_EMITTED,
            "expected_status": CONTROL_AUDIT_STATUS_PROCESSED,
        },
    ]

    for case in cases:
        event = build_valid_event(event_id=f"{case['name']}-{RUN_ID}")
        ensure_project(engine, enabled=case["enabled"])
        replace_policy(engine, enabled=case["with_policy"])

        with patch.object(worker, "publish_event", side_effect=fake_publish):
            result = worker.handle_event(event)

        try:
            audit_row = wait_for_audit_row(engine, event_id=event["event_id"])
            envelope = audit_row["envelope"] or {}
            delivery = get_audit_delivery_metadata(envelope)
            if (
                audit_row["action"] == case["expected_action"]
                and envelope.get("status") == case["expected_status"]
                and delivery["audit_persistence"].get("status") == "persisted"
                and delivery["audit_persistence"].get("row_id") == audit_row["id"]
            ):
                scenarios.append(
                    scenario(
                        PASS,
                        case["name"],
                        "Persistencia runtime verificada en iot_schema.auditoria",
                        action=audit_row["action"],
                        envelope=envelope,
                        delivery=delivery,
                        result=result,
                    )
                )
            else:
                scenarios.append(
                    scenario(
                        FAIL,
                        case["name"],
                        "La auditoría persistida no coincide con el estado esperado",
                        action=audit_row["action"],
                        envelope=envelope,
                        delivery=delivery,
                        result=result,
                    )
                )
        except Exception as exc:
            scenarios.append(
                scenario(
                    FAIL,
                    case["name"],
                    f"No se pudo verificar la persistencia de auditoría: {exc}",
                )
            )

    level_status = PASS if all(item["status"] == PASS for item in scenarios) else FAIL
    return {
        "level": "database-level",
        "status": level_status,
        "scenarios": scenarios,
    }


def run_full_e2e() -> Dict[str, Any]:
    rabbit_ok, rabbit_detail = tcp_check(DEFAULT_RABBITMQ_HOST, DEFAULT_RABBITMQ_PORT)
    mqtt_ok, mqtt_detail = tcp_check(DEFAULT_MQTT_HOST, DEFAULT_MQTT_PORT)
    postgres_ok, postgres_detail = can_connect_postgres()
    preflight_failures = [
        detail
        for ok, detail in [
            (rabbit_ok, rabbit_detail),
            (mqtt_ok, mqtt_detail),
            (postgres_ok, postgres_detail),
        ]
        if not ok
    ]
    isolated_queues = [SMOKE_RECOMMENDATION_QUEUE, SMOKE_AUDIT_QUEUE, SMOKE_SIMULATED_QUEUE]
    if not all(queue.startswith("control.") and ".smoke." in queue for queue in isolated_queues):
        preflight_failures.append("Las rutas de salida smoke deben declararse explícitamente y ser aisladas")
    if preflight_failures:
        return {
            "level": "full E2E",
            "status": SKIP,
            "scenarios": [
                scenario(
                    SKIP,
                    "full_e2e_preflight",
                    "No fue posible ejecutar el E2E completo con servicios reales",
                    reasons=preflight_failures,
                )
            ],
        }

    engine = build_postgres_engine()
    event_id = f"evt-full-e2e-{RUN_ID}"
    try:
        ensure_project(engine, enabled=True)
        replace_policy(engine, enabled=True)
        mqtt_result = publish_mqtt_message(event_id)
        audit_row = wait_for_audit_row(engine, event_id=event_id, timeout_seconds=30.0)
        correlation_id = f"control::{event_id}::{TEST_VARIABLE_ID}"
        delivery = wait_for_simulated_delivery(engine, correlation_id=correlation_id, timeout_seconds=30.0)
        consistency_scenarios = evaluate_audit_consistency(audit_row)
        level_status = PASS if all(item["status"] == PASS for item in consistency_scenarios) else FAIL
        return {
            "level": "full E2E",
            "status": level_status,
            "scenarios": [
                scenario(
                    PASS,
                    "mqtt_ingestor_worker_outbox_dispatch",
                    "Se verificó MQTT -> ingestor -> worker -> recommendation -> intent -> outbox -> dispatch simulated",
                    mqtt=mqtt_result,
                    audit_row=audit_row,
                    delivery=delivery,
                    isolated_queues=isolated_queues,
                )
            ] + consistency_scenarios,
        }
    except Exception as exc:
        return {
            "level": "full E2E",
            "status": FAIL,
            "scenarios": [
                scenario(
                    FAIL,
                    "mqtt_ingestor_worker_outbox_dispatch",
                    f"El flujo E2E real falló: {exc}",
                )
            ],
        }


def summarize_levels(level_results: List[Dict[str, Any]]) -> Tuple[str, int]:
    statuses = {result["level"]: result["status"] for result in level_results}
    if any(status == FAIL for status in statuses.values()):
        return FAIL, 1
    if any(status in {SKIP, WARN} for status in statuses.values()):
        return WARN, 2
    return PASS, 0


def print_human_summary(report: Dict[str, Any]) -> None:
    print("[SMOKE] Control parametric E2E consolidation")
    print(f"[SMOKE] run_id={report['run_id']}")
    print(f"[SMOKE] overall={report['overall_status']} exit_code={report['exit_code']}")
    for level_result in report["levels"]:
        print(f"[SMOKE] {level_result['level']}: {level_result['status']}")
        for item in level_result["scenarios"]:
            print(f"  - {item['status']} {item['name']}: {item['detail']}")


def main() -> int:
    try:
        level_results = [
            run_contract_level(),
            run_component_level(),
            run_broker_level(),
            run_database_level(),
            run_full_e2e(),
        ]
    finally:
        # The fixture is random and isolated, so cleanup cannot touch existing
        # projects, policies, outbox rows or audit history.
        try:
            cleanup_fixture(build_postgres_engine())
        except Exception as exc:
            print(f"[SMOKE] cleanup failed for fixture {TEST_PROJECT_ID}: {exc}", file=sys.stderr)
            raise
    overall_status, exit_code = summarize_levels(level_results)

    report = {
        "run_id": RUN_ID,
        "generated_at": now_iso(),
        "overall_status": overall_status,
        "exit_code": exit_code,
        "levels": level_results,
    }

    print_human_summary(report)
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
