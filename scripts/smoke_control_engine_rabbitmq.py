#!/usr/bin/env python3

"""
Smoke real de RabbitMQ para control_engine_worker.

Publica un evento de telemetría en una cola/routing key aislada, ejecuta el
worker en modo consume-one y verifica que aparezcan recommendation + audit en
RabbitMQ.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENGINE_SRC = os.path.join(REPO_ROOT, "apps", "parametric-control-engine", "src")
SRC_ROOT = os.path.join(REPO_ROOT, "src")

for path in [SRC_ROOT, ENGINE_SRC]:
    if path not in sys.path:
        sys.path.insert(0, path)


run_id = uuid.uuid4().hex
input_queue = f"telemetry.events.smoke.{run_id}"
recommendation_queue = f"control.recommendations.smoke.{run_id}"
audit_queue = f"control.audit.smoke.{run_id}"
smoke_project_id = os.getenv(
    "CONTROL_TEST_PROJECT_ID",
    "00000000-0000-0000-0000-000000000001",
)

os.environ.setdefault("REPO_ROOT", REPO_ROOT)
os.environ.setdefault("CONTROL_WORKER_FORCE_ENABLED", "false")
os.environ.setdefault("CONTROL_WORKER_PUBLISH_MODE", "rabbitmq")
os.environ.setdefault("CONTROL_WORKER_RABBITMQ_HOST", "localhost")
os.environ.setdefault("CONTROL_WORKER_RABBITMQ_PORT", "5672")
os.environ.setdefault("CONTROL_WORKER_RABBITMQ_USERNAME", "guest")
os.environ.setdefault("CONTROL_WORKER_RABBITMQ_PASSWORD", "guest")
os.environ.setdefault("CONTROL_WORKER_RABBITMQ_VHOST", "/")
os.environ.setdefault("CONTROL_WORKER_INPUT_QUEUE", input_queue)
os.environ.setdefault("CONTROL_WORKER_INPUT_ROUTING_KEY", input_queue)
os.environ.setdefault("CONTROL_WORKER_CONSUMER_QUEUE", input_queue)
os.environ.setdefault("CONTROL_WORKER_RECOMMENDATION_QUEUE", recommendation_queue)
os.environ.setdefault("CONTROL_WORKER_AUDIT_QUEUE", audit_queue)
os.environ.setdefault("CONTROL_WORKER_IDLE_TIMEOUT_SECONDS", "8")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "iot_middleware")
os.environ.setdefault("DB_USER", "iot_user")
os.environ.setdefault("DB_PASSWORD", "iot_password_2024")


from iot_middleware.services.control_engine_worker import (  # noqa: E402
    _load_rabbitmq_client,
    consume_rabbitmq_events,
)

from sqlalchemy import create_engine, text  # noqa: E402


def _project_engine():
    db_host = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "iot_middleware")
    db_user = os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "iot_user")
    db_password = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "iot_password_2024")
    return create_engine(
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}",
        pool_pre_ping=True,
    )


def ensure_project_flag(project_id: str, enabled: bool) -> None:
    engine = _project_engine()
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
                "project_id": project_id,
                "name": "control-engine-smoke-project",
                "description": "Proyecto temporal para smoke del control engine worker",
                "status": "draft",
                "enabled": enabled,
            },
        )


def ensure_project_policy(project_id: str, variable: str, context_selector: dict) -> None:
    engine = _project_engine()
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
                "project_id": project_id,
                "variable": variable,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO public.project_control_policies (
                    project_id,
                    variable,
                    context_selector,
                    policy_type,
                    params,
                    priority,
                    enabled,
                    version
                )
                VALUES (
                    CAST(:project_id AS uuid),
                    :variable,
                    CAST(:context_selector AS jsonb),
                    :policy_type,
                    CAST(:params AS jsonb),
                    :priority,
                    TRUE,
                    :version
                )
                """
            ),
            {
                "project_id": project_id,
                "variable": variable,
                "context_selector": json.dumps(context_selector),
                "policy_type": "proportional",
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
                "priority": 10,
                "version": 1,
            },
        )


def main() -> int:
    client, _ = _load_rabbitmq_client()
    for queue_name in [input_queue, recommendation_queue, audit_queue]:
        if not client.declare_topic_queue(
            queue_name=queue_name,
            routing_keys=[queue_name],
            durable=True,
            auto_delete=False,
        ):
            raise SystemExit(f"Could not declare smoke queue {queue_name}")

    def run_case(case_name: str, enabled: bool) -> dict:
        ensure_project_flag(smoke_project_id, enabled=enabled)
        ensure_project_policy(
            smoke_project_id,
            os.getenv("CONTROL_TEST_VARIABLE", "tank_level"),
            {"sector": os.getenv("CONTROL_TEST_SECTOR", "tank_A")},
        )
        client.purge_queue(input_queue)
        client.purge_queue(recommendation_queue)
        client.purge_queue(audit_queue)

        event = {
            "event_id": f"evt-smoke-{case_name}-{run_id}",
            "project_id": smoke_project_id,
            "variable": os.getenv("CONTROL_TEST_VARIABLE", "tank_level"),
            "value": float(os.getenv("CONTROL_TEST_VALUE", "72.5")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": {
                "sector": os.getenv("CONTROL_TEST_SECTOR", "tank_A"),
            },
        }

        if not client.publish_json(
            routing_key=input_queue,
            payload=event,
            queue_name=input_queue,
            durable_queue=True,
        ):
            raise SystemExit(f"Could not publish smoke telemetry event for case {case_name}")

        processed = consume_rabbitmq_events(max_messages=1, idle_timeout_seconds=8)
        if processed != 1:
            raise SystemExit(f"Expected worker to process 1 message in case {case_name}, got {processed}")

        recommendation_message = client.get_json_message(recommendation_queue, auto_ack=True)
        audit_message = client.get_json_message(audit_queue, auto_ack=True)
        if audit_message is None:
            raise SystemExit(f"Audit message not found in RabbitMQ smoke queue for case {case_name}")

        if enabled:
            if recommendation_message is None:
                raise SystemExit(f"Recommendation message not found for enabled case {case_name}")
            if audit_message["payload"].get("payload", {}).get("project_id") != smoke_project_id:
                raise SystemExit("Enabled audit message does not reference the expected project_id")
        else:
            if recommendation_message is not None:
                raise SystemExit(f"Disabled case {case_name} emitted an unexpected recommendation")
            if audit_message["payload"].get("status") != "skipped":
                raise SystemExit("Disabled case did not emit a skipped audit envelope")

        return {
            "case": case_name,
            "feature_flag_enabled": enabled,
            "input_event": event,
            "recommendation": recommendation_message["payload"] if recommendation_message else None,
            "audit": audit_message["payload"],
        }

    report = {
        "run_id": run_id,
        "queue_names": {
            "input": input_queue,
            "recommendation": recommendation_queue,
            "audit": audit_queue,
        },
        "cases": [
            run_case("disabled", enabled=False),
            run_case("enabled", enabled=True),
        ],
    }
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
