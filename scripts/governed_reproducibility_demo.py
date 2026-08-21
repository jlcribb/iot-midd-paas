#!/usr/bin/env python3
"""Controlled M5.6 fixture for the authenticated reproducibility demo.

The script creates only a marked development project and a temporary,
project-scoped operator membership for the already configured OAuth identity.
Simulation sessions and runs are intentionally created from the Workbench, not
by this harness.  Cleanup refuses unmarked projects and never touches legacy
RabbitMQ queues or unscoped data.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text


REPO_ROOT = Path(__file__).resolve().parents[1]
for source_path in (REPO_ROOT / "src", REPO_ROOT / "apps" / "parametric-control-engine" / "src"):
    if str(source_path) not in sys.path:
        sys.path.insert(0, str(source_path))

NAMESPACE = "midd-iot/m5-6-governed-reproducibility-demo/v1"
ACTOR_EMAIL = "jl.infodata@gmail.com"
PROJECT_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{NAMESPACE}/project"))
SECTOR_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{NAMESPACE}/sector"))
PRIMARY_SOURCE_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{NAMESPACE}/asset/primary-source"))
PRIMARY_TARGET_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{NAMESPACE}/asset/primary-target"))
RECOMMENDATION_SOURCE_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{NAMESPACE}/asset/recommendation-source"))
PRIMARY_POLICY_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{NAMESPACE}/policy/primary"))
RECOMMENDATION_POLICY_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{NAMESPACE}/policy/recommendation-only"))
PRIMARY_BINDING_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{NAMESPACE}/binding/primary"))
PRIMARY_VARIABLE = "m56_demo_level"
RECOMMENDATION_VARIABLE = "m56_demo_recommendation_only"
FROZEN_SETPOINT = 22.0
MUTATED_LIVE_SETPOINT = 100.0


def configure_defaults() -> None:
    if os.getenv("DB_HOST"):
        return
    for key, value in {
        "DB_HOST": "localhost", "DB_PORT": "5432", "DB_NAME": "iot_middleware",
        "DB_USER": "iot_user", "DB_PASSWORD": "iot_password_2024",
    }.items():
        os.environ.setdefault(key, value)


configure_defaults()


def engine():
    return create_engine(
        "postgresql://{user}:{password}@{host}:{port}/{name}".format(
            host=os.environ["DB_HOST"], port=os.environ["DB_PORT"], name=os.environ["DB_NAME"],
            user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
        ),
        pool_pre_ping=True,
    )


def metadata() -> str:
    return json.dumps({"demo_namespace": NAMESPACE, "development_only": True, "purpose": "M5.6 governed reproducibility demonstration"})


def threshold_params(setpoint: float) -> str:
    return json.dumps({
        "setpoint_value": setpoint, "setpoint_label": "M5.6 frozen threshold",
        "tolerance": 3.0, "increase_step": 1.0, "decrease_step": 1.0, "hold_signal": 0.0,
        "variable_name": "M5.6 demo level", "variable_unit": "units", "actuator_name": "demo relay",
        "increase_action_label": "increase", "decrease_action_label": "decrease", "hold_action_label": "hold",
    })


def assert_owned(connection) -> bool:
    row = connection.execute(text("SELECT metadata FROM public.projects WHERE id=CAST(:id AS uuid)"), {"id": PROJECT_ID}).mappings().one_or_none()
    if row is None:
        return False
    project_metadata = row["metadata"] or {}
    if project_metadata.get("demo_namespace") != NAMESPACE or project_metadata.get("development_only") is not True:
        raise RuntimeError("refusing to modify an unmarked M5.6 project")
    return True


def cleanup(db_engine) -> dict[str, int]:
    """Delete only rows bound to the exactly marked fixture project."""
    with db_engine.begin() as connection:
        if not assert_owned(connection):
            return {key: 0 for key in ("project", "membership", "sessions", "runs", "results", "run_events", "policies", "bindings", "assets", "sectors", "audit")}
        statements = (
            ("audit", "DELETE FROM iot_schema.auditoria WHERE contexto->>'project_id'=:id AND entidad IN ('control_simulation_sessions', 'control_simulation_runs')"),
            ("results", "DELETE FROM public.control_simulation_results WHERE project_id=CAST(:id AS uuid)"),
            ("run_events", "DELETE FROM public.control_simulation_run_events WHERE run_id IN (SELECT id FROM public.control_simulation_runs WHERE project_id=CAST(:id AS uuid))"),
            ("runs", "DELETE FROM public.control_simulation_runs WHERE project_id=CAST(:id AS uuid)"),
            ("sessions", "DELETE FROM public.control_simulation_sessions WHERE project_id=CAST(:id AS uuid)"),
            ("bindings", "DELETE FROM public.project_control_policy_actuation_bindings WHERE project_id=CAST(:id AS uuid)"),
            ("policies", "DELETE FROM public.project_control_policies WHERE project_id=CAST(:id AS uuid)"),
            ("assets", "DELETE FROM public.assets WHERE project_id=CAST(:id AS uuid)"),
            ("sectors", "DELETE FROM public.sectors WHERE project_id=CAST(:id AS uuid)"),
            ("membership", "DELETE FROM public.project_control_memberships WHERE project_id=CAST(:id AS uuid)"),
            ("project", "DELETE FROM public.projects WHERE id=CAST(:id AS uuid)"),
        )
        return {label: int(connection.execute(text(sql), {"id": PROJECT_ID}).rowcount or 0) for label, sql in statements}


def prepare(db_engine, actor_email: str) -> dict[str, str]:
    cleanup(db_engine)
    with db_engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO public.projects (id, name, description, status, metadata, parametric_control_enabled)
            VALUES (CAST(:id AS uuid), :name, :description, CAST('active' AS project_status_enum), CAST(:metadata AS jsonb), TRUE)
        """), {"id": PROJECT_ID, "name": "M5.6 Governed Reproducibility Demo — DEVELOPMENT ONLY", "description": "Temporary, cleanup-safe M5.6 fixture; never a production seed.", "metadata": metadata()})
        connection.execute(text("""
            INSERT INTO public.project_control_memberships (actor_email, project_id, role, enabled)
            VALUES (:email, CAST(:project_id AS uuid), 'operator', TRUE)
        """), {"email": actor_email, "project_id": PROJECT_ID})
        connection.execute(text("""
            INSERT INTO public.sectors (id, project_id, name, code, description, metadata)
            VALUES (CAST(:id AS uuid), CAST(:project_id AS uuid), 'M5.6 demo sector', 'M56_DEMO', 'Temporary simulation-only fixture', CAST(:metadata AS jsonb))
        """), {"id": SECTOR_ID, "project_id": PROJECT_ID, "metadata": metadata()})
        connection.execute(text("""
            INSERT INTO public.assets (id, project_id, sector_id, asset_type, subtype, name, status, metadata)
            VALUES
              (CAST(:primary_source AS uuid), CAST(:project AS uuid), CAST(:sector AS uuid), CAST('sensor' AS asset_type_enum), 'm56-sensor', 'M5.6 source asset', CAST('active' AS asset_status_enum), CAST(:metadata AS jsonb)),
              (CAST(:primary_target AS uuid), CAST(:project AS uuid), CAST(:sector AS uuid), CAST('actuator' AS asset_type_enum), 'm56-actuator', 'M5.6 simulated target', CAST('active' AS asset_status_enum), CAST(:target_metadata AS jsonb)),
              (CAST(:recommendation_source AS uuid), CAST(:project AS uuid), CAST(:sector AS uuid), CAST('sensor' AS asset_type_enum), 'm56-sensor', 'M5.6 recommendation-only source', CAST('active' AS asset_status_enum), CAST(:metadata AS jsonb))
        """), {"primary_source": PRIMARY_SOURCE_ID, "primary_target": PRIMARY_TARGET_ID, "recommendation_source": RECOMMENDATION_SOURCE_ID, "project": PROJECT_ID, "sector": SECTOR_ID, "metadata": metadata(), "target_metadata": json.dumps({"demo_namespace": NAMESPACE, "control_capabilities": [{"key": "relay_1", "operations": ["set"]}]})})
        connection.execute(text("""
            INSERT INTO public.project_control_policies (id, project_id, bound_asset_id, variable, context_selector, policy_type, params, priority, enabled, version)
            VALUES
              (CAST(:primary_id AS uuid), CAST(:project AS uuid), CAST(:primary_source AS uuid), :primary_variable, '{}'::jsonb, 'threshold', CAST(:params AS jsonb), 20, TRUE, 1),
              (CAST(:recommendation_id AS uuid), CAST(:project AS uuid), CAST(:recommendation_source AS uuid), :recommendation_variable, '{}'::jsonb, 'threshold', CAST(:params AS jsonb), 10, TRUE, 1)
        """), {"primary_id": PRIMARY_POLICY_ID, "recommendation_id": RECOMMENDATION_POLICY_ID, "project": PROJECT_ID, "primary_source": PRIMARY_SOURCE_ID, "recommendation_source": RECOMMENDATION_SOURCE_ID, "primary_variable": PRIMARY_VARIABLE, "recommendation_variable": RECOMMENDATION_VARIABLE, "params": threshold_params(FROZEN_SETPOINT)})
        connection.execute(text("""
            INSERT INTO public.project_control_policy_actuation_bindings (id, policy_id, project_id, source_asset_id, target_asset_id, control_point, operation, enabled, version)
            VALUES (CAST(:id AS uuid), CAST(:policy AS uuid), CAST(:project AS uuid), CAST(:source AS uuid), CAST(:target AS uuid), 'relay_1', 'set', TRUE, 1)
        """), {"id": PRIMARY_BINDING_ID, "policy": PRIMARY_POLICY_ID, "project": PROJECT_ID, "source": PRIMARY_SOURCE_ID, "target": PRIMARY_TARGET_ID})
    return fixture_ids(actor_email)


def mutate_live(db_engine, setpoint: float) -> dict[str, Any]:
    with db_engine.begin() as connection:
        if not assert_owned(connection):
            raise RuntimeError("M5.6 fixture is not prepared")
        row = connection.execute(text("""
            UPDATE public.project_control_policies
            SET params=CAST(:params AS jsonb), version=version+1
            WHERE id=CAST(:id AS uuid) AND project_id=CAST(:project AS uuid)
            RETURNING version
        """), {"params": threshold_params(setpoint), "id": PRIMARY_POLICY_ID, "project": PROJECT_ID}).mappings().one()
    return {"policy_id": PRIMARY_POLICY_ID, "live_setpoint": setpoint, "version": int(row["version"])}


def fixture_ids(actor_email: str) -> dict[str, str]:
    return {"actor_email": actor_email, "project_id": PROJECT_ID, "primary_policy_id": PRIMARY_POLICY_ID,
            "recommendation_policy_id": RECOMMENDATION_POLICY_ID, "primary_variable": PRIMARY_VARIABLE,
            "recommendation_variable": RECOMMENDATION_VARIABLE, "frozen_setpoint": str(FROZEN_SETPOINT),
            "mutated_live_setpoint": str(MUTATED_LIVE_SETPOINT)}


def evidence(db_engine) -> dict[str, Any]:
    with db_engine.connect() as connection:
        if not assert_owned(connection):
            raise RuntimeError("M5.6 fixture is not prepared")
        membership = connection.execute(text("""SELECT role, enabled FROM public.project_control_memberships
            WHERE actor_email=:email AND project_id=CAST(:project AS uuid)"""), {"email": ACTOR_EMAIL, "project": PROJECT_ID}).mappings().one_or_none()
        sessions = connection.execute(text("""
            SELECT id::text AS session_id, policy_snapshot->'policy'->>'id' AS policy_id, experiment_fingerprint,
                   policy_snapshot_hash, topology_snapshot_hash, dataset_snapshot_hash, configuration_snapshot_hash,
                   configuration_snapshot->'engine'->>'version' AS engine_version,
                   configuration_snapshot->'clock'->>'model_version' AS clock_model_version, prepared_at
            FROM public.control_simulation_sessions WHERE project_id=CAST(:project AS uuid) ORDER BY created_at
        """), {"project": PROJECT_ID}).mappings().all()
        run_rows = connection.execute(text("""
            SELECT r.id::text AS run_id, r.session_id::text, r.status, r.output_count, r.created_at, r.completed_at,
                   result.result_fingerprint, result.processed_events, result.evaluation_count, result.recommendation_count,
                   result.actionable_recommendation_count, result.recommendation_only_count, result.failed_domain_event_count
            FROM public.control_simulation_runs r LEFT JOIN public.control_simulation_results result ON result.run_id=r.id
            WHERE r.project_id=CAST(:project AS uuid) ORDER BY r.created_at, r.id
        """), {"project": PROJECT_ID}).mappings().all()
        traces = connection.execute(text("""
            SELECT events.run_id::text, events.sequence, events.output
            FROM public.control_simulation_run_events events
            JOIN public.control_simulation_runs runs ON runs.id=events.run_id
            WHERE runs.project_id=CAST(:project AS uuid) ORDER BY events.run_id, events.sequence
        """), {"project": PROJECT_ID}).mappings().all()
        outbox = connection.execute(text("SELECT count(*) FROM public.control_actuation_outbox WHERE project_id=CAST(:project AS uuid)"), {"project": PROJECT_ID}).scalar_one()
        intents = connection.execute(text("SELECT count(*) FROM public.control_actuation_delivery_intents WHERE project_id=CAST(:project AS uuid)"), {"project": PROJECT_ID}).scalar_one()
    return {"fixture": fixture_ids(ACTOR_EMAIL), "membership": dict(membership) if membership else None,
            "sessions": [dict(row) for row in sessions], "runs": [dict(row) for row in run_rows],
            "traces": [{"run_id": row["run_id"], "sequence": int(row["sequence"]), "output": dict(row["output"])} for row in traces],
            "operational_outbox_count": int(outbox), "operational_delivery_intent_count": int(intents)}


def main() -> int:
    parser = argparse.ArgumentParser(description="M5.6 governed reproducibility fixture")
    parser.add_argument("command", choices=("prepare", "mutate-live", "restore-live", "evidence", "cleanup"))
    parser.add_argument("--actor-email", default=ACTOR_EMAIL)
    args = parser.parse_args()
    actor_email = args.actor_email.strip().lower()
    if actor_email != ACTOR_EMAIL:
        raise SystemExit("fixture is restricted to the configured M5.6 OAuth demo identity")
    db_engine = engine()
    if args.command == "prepare":
        output: dict[str, Any] = {"command": args.command, "fixture": prepare(db_engine, actor_email)}
    elif args.command == "mutate-live":
        output = {"command": args.command, "mutation": mutate_live(db_engine, MUTATED_LIVE_SETPOINT)}
    elif args.command == "restore-live":
        output = {"command": args.command, "mutation": mutate_live(db_engine, FROZEN_SETPOINT)}
    elif args.command == "evidence":
        output = {"command": args.command, "evidence": evidence(db_engine)}
    else:
        output = {"command": args.command, "removed": cleanup(db_engine)}
    print(json.dumps(output, default=str, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
