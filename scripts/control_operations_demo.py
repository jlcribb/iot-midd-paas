#!/usr/bin/env python3
"""Prepare, verify, and remove the isolated Control Operations demonstration.

This is deliberately a development-only fixture.  It does not create users,
credentials, tokens, or authentication fallbacks.  The only access grant it
creates is the least-privilege ``viewer`` membership for the supplied OAuth
email in its own marked project.

Run inside the canonical Docker Compose runtime so the script uses the same
PostgreSQL, RabbitMQ, control worker, outbox publisher, and simulated dispatch
contracts as the application.  See docs/operations/control_operations_demo.md.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from unittest.mock import patch

from sqlalchemy import create_engine, text


REPO_ROOT = Path(__file__).resolve().parents[1]
for source_path in (REPO_ROOT / "src", REPO_ROOT / "apps" / "parametric-control-engine" / "src"):
    source = str(source_path)
    if source not in sys.path:
        sys.path.insert(0, source)


DEMO_NAMESPACE = "midd-iot/control-operations-demo/v1"
DEMO_ACTOR_EMAIL = "jl.infodata@gmail.com"
DEMO_PROJECT_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{DEMO_NAMESPACE}/project"))
DEMO_SECTOR_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{DEMO_NAMESPACE}/sector"))
HEALTHY_SOURCE_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{DEMO_NAMESPACE}/asset/healthy-source"))
HEALTHY_TARGET_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{DEMO_NAMESPACE}/asset/healthy-target"))
RECOMMENDATION_SOURCE_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{DEMO_NAMESPACE}/asset/recommendation-source"))
INACTIVE_SOURCE_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{DEMO_NAMESPACE}/asset/inactive-source"))
HEALTHY_POLICY_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{DEMO_NAMESPACE}/policy/healthy"))
RECOMMENDATION_POLICY_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{DEMO_NAMESPACE}/policy/recommendation-only"))
INACTIVE_POLICY_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{DEMO_NAMESPACE}/policy/inactive"))
HEALTHY_BINDING_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{DEMO_NAMESPACE}/binding/healthy"))

HEALTHY_VARIABLE = "demo_tank_level"
RECOMMENDATION_VARIABLE = "demo_tank_pressure"
INACTIVE_VARIABLE = "demo_inactive_level"
ACK_CORRELATION_ID = "demo-control-ack-v1"
RECOMMENDATION_CORRELATION_ID = "demo-control-recommendation-only-v1"
ACK_EVENT_ID = "demo-control-event-ack-v1"
RECOMMENDATION_EVENT_ID = "demo-control-event-recommendation-only-v1"
DEMO_RECOMMENDATION_QUEUE = "control.recommendations.demo.v1"
DEMO_AUDIT_QUEUE = "control.audit.demo.v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def configure_runtime_defaults() -> None:
    """Use Compose service DNS in containers and published ports on the host."""
    # Compose injects DB_HOST=postgresql.  Do not infer a host runtime from
    # /.dockerenv: some `docker compose exec` environments do not expose it.
    if os.getenv("DB_HOST"):
        return
    defaults = {
        "DB_HOST": "localhost", "DB_PORT": "5432", "DB_NAME": "iot_middleware",
        "DB_USER": "iot_user", "DB_PASSWORD": "iot_password_2024",
        "POSTGRES_HOST": "localhost", "POSTGRES_PORT": "5432", "POSTGRES_DB": "iot_middleware",
        "POSTGRES_USER": "iot_user", "POSTGRES_PASSWORD": "iot_password_2024",
        "CONTROL_WORKER_RABBITMQ_HOST": "localhost", "CONTROL_WORKER_RABBITMQ_PORT": "5672",
    }
    for name, value in defaults.items():
        os.environ.setdefault(name, value)


configure_runtime_defaults()

from iot_middleware.services import control_engine_worker as worker  # noqa: E402
from iot_middleware.services.actuation_outbox_publisher import ActuationOutboxPublisher  # noqa: E402
from iot_middleware.services.simulated_actuation_consumer import SimulatedActuationConsumer  # noqa: E402
from iot_middleware.storage import db_handler as runtime_db_handler  # noqa: E402
from iot_middleware.storage.actuation_outbox_repository import ActuationOutboxRepository, _map as map_outbox  # noqa: E402


def engine():
    """Build a DB connection from the runtime environment; never read OAuth data."""
    return create_engine(
        "postgresql://{user}:{password}@{host}:{port}/{name}".format(
            host=os.environ["DB_HOST"], port=os.environ["DB_PORT"], name=os.environ["DB_NAME"],
            user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
        ),
        pool_pre_ping=True,
    )


def reset_runtime_db_cache() -> None:
    runtime_db_handler._get_control_settings_connection_url.cache_clear()
    runtime_db_handler._get_control_settings_engine.cache_clear()
    runtime_db_handler._get_control_runtime_session_factory.cache_clear()


@contextmanager
def patched_worker_runtime() -> Iterator[None]:
    """Publish only to demo-specific queues; never publish into telemetry legacy queues."""
    patches = [
        patch.object(worker, "PUBLISH_MODE", "rabbitmq"),
        patch.object(worker, "RECOMMENDATION_QUEUE", DEMO_RECOMMENDATION_QUEUE),
        patch.object(worker, "AUDIT_QUEUE", DEMO_AUDIT_QUEUE),
        patch.object(worker, "SIMULATED_ACTUATION_ENABLED", False),
    ]
    for item in patches:
        item.start()
    try:
        yield
    finally:
        while patches:
            patches.pop().stop()


def demo_metadata() -> str:
    return json.dumps({"demo_namespace": DEMO_NAMESPACE, "development_only": True, "not_production_seed": True})


def assert_owned_project(connection) -> bool:
    row = connection.execute(text("SELECT metadata FROM public.projects WHERE id = CAST(:id AS uuid)"), {"id": DEMO_PROJECT_ID}).mappings().first()
    if row is None:
        return False
    metadata = row["metadata"] or {}
    if metadata.get("demo_namespace") != DEMO_NAMESPACE or metadata.get("development_only") is not True:
        raise RuntimeError("Refusing to modify a project that is not the marked Control Operations demo fixture")
    return True


def purge_demo_queues() -> dict[str, str]:
    """Purge only the two queues this fixture declared; legacy queues are untouched."""
    client, _ = worker._load_rabbitmq_client()
    try:
        return {
            queue_name: "purged" if client.purge_queue(queue_name) else "not_present_or_unavailable"
            for queue_name in (DEMO_RECOMMENDATION_QUEUE, DEMO_AUDIT_QUEUE)
        }
    finally:
        client.disconnect()


def cleanup(connection_engine) -> dict[str, Any]:
    """Remove only rows and RabbitMQ messages attached to the known demo fixture."""
    with connection_engine.begin() as connection:
        if not assert_owned_project(connection):
            counts: dict[str, Any] = {"project": 0, "membership": 0, "audit": 0, "outbox": 0, "intent": 0}
        else:
            counts = {}
            for label, statement in (
                ("audit", "DELETE FROM iot_schema.auditoria WHERE cambios->'payload'->>'project_id' = :id OR cambios->>'project_id' = :id OR entidad_id::text = :id"),
                ("outbox", "DELETE FROM public.control_actuation_outbox WHERE project_id = CAST(:id AS uuid)"),
                ("intent", "DELETE FROM public.control_actuation_delivery_intents WHERE project_id = CAST(:id AS uuid)"),
                ("membership", "DELETE FROM public.project_control_memberships WHERE project_id = CAST(:id AS uuid)"),
                ("project", "DELETE FROM public.projects WHERE id = CAST(:id AS uuid)"),
            ):
                counts[label] = int(connection.execute(text(statement), {"id": DEMO_PROJECT_ID}).rowcount or 0)
    counts["demo_queues"] = purge_demo_queues()
    return counts


def prepare_configuration(connection_engine, actor_email: str) -> None:
    with connection_engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO public.projects (id, name, description, status, metadata, parametric_control_enabled)
            VALUES (CAST(:id AS uuid), :name, :description, CAST('active' AS project_status_enum), CAST(:metadata AS jsonb), TRUE)
        """), {"id": DEMO_PROJECT_ID, "name": "Control Operations Demo — DEVELOPMENT ONLY", "description": "Isolated M4.4 governed demonstration fixture; not a production seed.", "metadata": demo_metadata()})
        connection.execute(text("""
            INSERT INTO public.project_control_memberships (actor_email, project_id, role, enabled)
            VALUES (:actor_email, CAST(:project_id AS uuid), 'viewer', TRUE)
        """), {"actor_email": actor_email, "project_id": DEMO_PROJECT_ID})
        connection.execute(text("""
            INSERT INTO public.sectors (id, project_id, name, code, description, metadata)
            VALUES (CAST(:id AS uuid), CAST(:project_id AS uuid), 'Control demo sector', 'CONTROL_DEMO', 'Development-only control demonstration', CAST(:metadata AS jsonb))
        """), {"id": DEMO_SECTOR_ID, "project_id": DEMO_PROJECT_ID, "metadata": demo_metadata()})
        connection.execute(text("""
            INSERT INTO public.assets (id, project_id, sector_id, asset_type, subtype, name, status, metadata)
            VALUES
              (CAST(:healthy_source AS uuid), CAST(:project AS uuid), CAST(:sector AS uuid), CAST('sensor' AS asset_type_enum), 'demo-sensor', 'Healthy source sensor', CAST('active' AS asset_status_enum), '{}'::jsonb),
              (CAST(:target AS uuid), CAST(:project AS uuid), CAST(:sector AS uuid), CAST('actuator' AS asset_type_enum), 'demo-actuator', 'Healthy simulated actuator', CAST('active' AS asset_status_enum), '{"control_capabilities":[{"key":"relay_1","operations":["set"]}]}'::jsonb),
              (CAST(:recommendation_source AS uuid), CAST(:project AS uuid), CAST(:sector AS uuid), CAST('sensor' AS asset_type_enum), 'demo-sensor', 'Recommendation-only source sensor', CAST('active' AS asset_status_enum), '{}'::jsonb),
              (CAST(:inactive_source AS uuid), CAST(:project AS uuid), CAST(:sector AS uuid), CAST('sensor' AS asset_type_enum), 'demo-sensor', 'Inactive policy source sensor', CAST('active' AS asset_status_enum), '{}'::jsonb)
        """), {"healthy_source": HEALTHY_SOURCE_ID, "target": HEALTHY_TARGET_ID, "recommendation_source": RECOMMENDATION_SOURCE_ID, "inactive_source": INACTIVE_SOURCE_ID, "project": DEMO_PROJECT_ID, "sector": DEMO_SECTOR_ID})
        policy_params = json.dumps({"variable_name": "Demo variable", "variable_unit": "units", "actuator_name": "control_output", "setpoint_value": 70.0, "gain": 1.0, "deadband": 0.0, "min_action": 0.0})
        connection.execute(text("""
            INSERT INTO public.project_control_policies (id, project_id, bound_asset_id, variable, context_selector, policy_type, params, priority, enabled, version)
            VALUES
              (CAST(:healthy_id AS uuid), CAST(:project AS uuid), CAST(:healthy_source AS uuid), :healthy_variable, '{"sector":"CONTROL_DEMO"}'::jsonb, 'proportional', CAST(:params AS jsonb), 30, TRUE, 1),
              (CAST(:recommendation_id AS uuid), CAST(:project AS uuid), CAST(:recommendation_source AS uuid), :recommendation_variable, '{"sector":"CONTROL_DEMO"}'::jsonb, 'proportional', CAST(:params AS jsonb), 20, TRUE, 1),
              (CAST(:inactive_id AS uuid), CAST(:project AS uuid), CAST(:inactive_source AS uuid), :inactive_variable, '{"sector":"CONTROL_DEMO"}'::jsonb, 'proportional', CAST(:params AS jsonb), 10, FALSE, 1)
        """), {"healthy_id": HEALTHY_POLICY_ID, "recommendation_id": RECOMMENDATION_POLICY_ID, "inactive_id": INACTIVE_POLICY_ID, "project": DEMO_PROJECT_ID, "healthy_source": HEALTHY_SOURCE_ID, "recommendation_source": RECOMMENDATION_SOURCE_ID, "inactive_source": INACTIVE_SOURCE_ID, "healthy_variable": HEALTHY_VARIABLE, "recommendation_variable": RECOMMENDATION_VARIABLE, "inactive_variable": INACTIVE_VARIABLE, "params": policy_params})
        connection.execute(text("""
            INSERT INTO public.project_control_policy_actuation_bindings (id, policy_id, project_id, source_asset_id, target_asset_id, control_point, operation, enabled, version)
            VALUES (CAST(:id AS uuid), CAST(:policy AS uuid), CAST(:project AS uuid), CAST(:source AS uuid), CAST(:target AS uuid), 'relay_1', 'set', TRUE, 1)
        """), {"id": HEALTHY_BINDING_ID, "policy": HEALTHY_POLICY_ID, "project": DEMO_PROJECT_ID, "source": HEALTHY_SOURCE_ID, "target": HEALTHY_TARGET_ID})


def telemetry_event(*, event_id: str, correlation_id: str, variable: str, source_asset_id: str) -> dict[str, Any]:
    return {"event_id": event_id, "project_id": DEMO_PROJECT_ID, "variable": variable, "value": 72.5, "timestamp": now_iso(), "source": "control_operations_demo", "event_kind": "telemetry.observed", "quality": "good", "correlation_id": correlation_id, "metadata": {"demo_namespace": DEMO_NAMESPACE}, "context": {"sector": "CONTROL_DEMO", "unit_id": "demo-unit", "device_id": "demo-device", "asset_id": source_asset_id, "location_id": "demo-location"}}


class ScopedOutboxRepository:
    """Fixture adapter that lets the canonical publisher claim only its known event."""

    def __init__(self, connection_engine, event_id: str) -> None:
        self._engine = connection_engine
        self._event_id = event_id
        self._delegate = ActuationOutboxRepository(connection_engine)

    def claim(self, *, limit: int = 20, lease_seconds: int = 30):
        with self._engine.begin() as connection:
            row = connection.execute(text("""
                UPDATE public.control_actuation_outbox
                SET status='publishing', claimed_at=NOW(), lease_until=NOW()+CAST(:lease AS interval), attempt_count=attempt_count+1
                WHERE event_id=CAST(:event_id AS uuid) AND status='pending' AND available_at<=NOW()
                RETURNING *
            """), {"event_id": self._event_id, "lease": f"{lease_seconds} seconds"}).mappings().first()
        return [map_outbox(row)] if row else []

    def mark_published(self, event_id: str) -> None:
        self._delegate.mark_published(event_id)

    def retry_or_fail(self, event, error: Exception, *, max_attempts: int = 3, base_delay_seconds: float = 1.0) -> str:
        return self._delegate.retry_or_fail(event, error, max_attempts=max_attempts, base_delay_seconds=base_delay_seconds)


def wait_for_ack(connection_engine, command_id: str, timeout_seconds: float = 30.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        with connection_engine.connect() as connection:
            row = connection.execute(text("""
                SELECT i.id::text AS delivery_intent_id, i.command_id::text, i.recommendation_id, i.correlation_id, i.policy_id, i.status, o.event_id::text, o.status AS outbox_status
                FROM public.control_actuation_delivery_intents i
                JOIN public.control_actuation_outbox o ON o.command_id = i.command_id
                WHERE i.command_id = CAST(:command_id AS uuid)
            """), {"command_id": command_id}).mappings().first()
        if row and row["status"] == "acknowledged" and row["outbox_status"] == "published":
            return dict(row)
        time.sleep(0.5)
    raise TimeoutError("Demo dispatch did not reach acknowledged + outbox published")


def run_operational_scenarios(connection_engine) -> dict[str, Any]:
    reset_runtime_db_cache()
    with patched_worker_runtime():
        healthy = worker.handle_event(telemetry_event(event_id=ACK_EVENT_ID, correlation_id=ACK_CORRELATION_ID, variable=HEALTHY_VARIABLE, source_asset_id=HEALTHY_SOURCE_ID))
        recommendation_only = worker.handle_event(telemetry_event(event_id=RECOMMENDATION_EVENT_ID, correlation_id=RECOMMENDATION_CORRELATION_ID, variable=RECOMMENDATION_VARIABLE, source_asset_id=RECOMMENDATION_SOURCE_ID))
    if not healthy or not healthy.get("publish_envelope") or not recommendation_only or not recommendation_only.get("publish_envelope"):
        raise RuntimeError("The canonical control worker did not emit both demo recommendations")
    consumer = SimulatedActuationConsumer(dispatch_immediately=False)
    outcome = consumer.process(healthy["publish_envelope"])
    if outcome.status != "queued" or not outcome.command_id:
        raise RuntimeError(f"The canonical simulated actuation consumer did not queue the ACK demo: {outcome}")
    with connection_engine.connect() as connection:
        event_id = connection.execute(text("SELECT event_id::text FROM public.control_actuation_outbox WHERE command_id = CAST(:command_id AS uuid)"), {"command_id": outcome.command_id}).scalar_one()
    # Reuse the runtime's broker adapter.  The Compose runtime may carry host
    # overrides for its own published ports; this adapter is the established
    # source of truth for service-DNS resolution.
    client, _ = worker._load_rabbitmq_client()
    try:
        published = ActuationOutboxPublisher(repository=ScopedOutboxRepository(connection_engine, event_id), client=client).publish_once(limit=1)
    finally:
        client.disconnect()
    if published != [("published", event_id)]:
        raise RuntimeError(f"The scoped canonical outbox publish did not succeed: {published}")
    acknowledgement = wait_for_ack(connection_engine, outcome.command_id)
    return {"acknowledgement": acknowledgement, "healthy_recommendation_id": healthy["publish_envelope"]["payload"]["recommendation_id"], "recommendation_only_id": recommendation_only["publish_envelope"]["payload"]["recommendation_id"]}


def verify(connection_engine, actor_email: str) -> dict[str, Any]:
    with connection_engine.connect() as connection:
        project = connection.execute(text("SELECT id::text, parametric_control_enabled, metadata FROM public.projects WHERE id=CAST(:id AS uuid)"), {"id": DEMO_PROJECT_ID}).mappings().one_or_none()
        membership = connection.execute(text("SELECT role, enabled FROM public.project_control_memberships WHERE actor_email=:actor AND project_id=CAST(:id AS uuid)"), {"actor": actor_email, "id": DEMO_PROJECT_ID}).mappings().one_or_none()
        unrelated_memberships = connection.execute(text("SELECT COUNT(*) FROM public.project_control_memberships WHERE actor_email=:actor AND project_id<>CAST(:id AS uuid) AND enabled=TRUE"), {"actor": actor_email, "id": DEMO_PROJECT_ID}).scalar_one()
        policy_rows = connection.execute(text("SELECT variable, enabled FROM public.project_control_policies WHERE project_id=CAST(:id AS uuid) ORDER BY variable"), {"id": DEMO_PROJECT_ID}).mappings().all()
        audit_rows = connection.execute(text("SELECT cambios FROM iot_schema.auditoria WHERE entidad='control_engine_worker' AND accion='CONTROL_RECOMMENDATION_EMITTED' AND (cambios->'payload'->>'project_id'=:id OR cambios->>'project_id'=:id)"), {"id": DEMO_PROJECT_ID}).mappings().all()
        delivery = connection.execute(text("SELECT i.id::text AS delivery_intent_id, i.command_id::text, i.recommendation_id, i.correlation_id, i.policy_id, i.status, o.event_id::text, o.status AS outbox_status FROM public.control_actuation_delivery_intents i JOIN public.control_actuation_outbox o ON o.command_id=i.command_id WHERE i.project_id=CAST(:id AS uuid)"), {"id": DEMO_PROJECT_ID}).mappings().all()
    if not project or project["metadata"].get("demo_namespace") != DEMO_NAMESPACE or project["parametric_control_enabled"] is not True:
        raise RuntimeError("Demo project is missing, unmarked, or has parametric control disabled")
    if not membership or membership["role"] != "viewer" or membership["enabled"] is not True or unrelated_memberships != 0:
        raise RuntimeError("Demo OAuth actor scope is not the required exclusive viewer membership")
    states = {row["variable"]: bool(row["enabled"]) for row in policy_rows}
    expected_states = {HEALTHY_VARIABLE: True, RECOMMENDATION_VARIABLE: True, INACTIVE_VARIABLE: False}
    if states != expected_states:
        raise RuntimeError(f"Unexpected demo policy states: {states}")
    recommendation_ids = {str((row["cambios"] or {}).get("publishable", {}).get("payload", {}).get("recommendation_id")) for row in audit_rows}
    if len(recommendation_ids - {"None"}) < 2:
        raise RuntimeError("Expected two persisted canonical recommendation audit envelopes")
    ack = next((dict(row) for row in delivery if row["correlation_id"] == ACK_CORRELATION_ID and row["status"] == "acknowledged" and row["outbox_status"] == "published"), None)
    if ack is None or ack["policy_id"] != HEALTHY_POLICY_ID:
        raise RuntimeError("Expected a fully traced acknowledged simulated delivery")
    if any(row["status"] == "dead_lettered" for row in delivery):
        raise RuntimeError("The demo must not introduce a DEAD_LETTERED delivery")
    return {"project_id": DEMO_PROJECT_ID, "actor_email": actor_email, "role": "viewer", "unrelated_active_memberships": int(unrelated_memberships), "recommendation_count": len(recommendation_ids - {"None"}), "acknowledgement": ack, "attention": "empty; no safe failure/retry is fabricated for this governed demo"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Controlled M4.4 Control Operations demo harness")
    parser.add_argument("command", choices=("prepare", "verify", "cleanup"))
    parser.add_argument("--actor-email", default=DEMO_ACTOR_EMAIL)
    args = parser.parse_args()
    actor_email = args.actor_email.strip().lower()
    if actor_email != DEMO_ACTOR_EMAIL:
        raise SystemExit("This controlled harness is restricted to the authorized M4.4 demo OAuth identity")
    connection_engine = engine()
    if args.command == "cleanup":
        print(json.dumps({"command": "cleanup", "removed": cleanup(connection_engine)}, sort_keys=True))
        return 0
    if args.command == "prepare":
        cleanup(connection_engine)
        prepare_configuration(connection_engine, actor_email)
        trace = run_operational_scenarios(connection_engine)
        print(json.dumps({"command": "prepare", "project_id": DEMO_PROJECT_ID, "trace": trace}, default=str, sort_keys=True))
        return 0
    print(json.dumps({"command": "verify", "result": verify(connection_engine, actor_email)}, default=str, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
