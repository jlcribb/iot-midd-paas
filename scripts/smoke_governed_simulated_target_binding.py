#!/usr/bin/env python3
"""Safe local E2E smoke for governed simulated target bindings.

Creates a disposable project, source, target, policy and binding; verifies one
simulated acknowledgement and one recommendation-only decision, then removes
only its own data. No broker, MQTT, hardware, or outbox is used.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from iot_middleware.services.simulated_actuation_consumer import SimulatedActuationConsumer
from iot_middleware.storage.db_handler import _get_control_settings_connection_url, _get_control_settings_engine
from iot_middleware.storage.actuation_outbox_repository import ActuationOutboxRepository


def main() -> None:
    project_id, sector_id, source_id, target_id, policy_id, binding_id = (str(uuid.uuid4()) for _ in range(6))
    engine = _get_control_settings_engine(_get_control_settings_connection_url())
    now = datetime.now(timezone.utc)
    envelope = {
        "message_type": "control.recommendation", "schema_version": "1.0",
        "payload": {
            "recommendation_id": f"recommendation::{uuid.uuid4()}", "correlation_id": str(uuid.uuid4()),
            "project_id": project_id, "policy_id": policy_id, "policy_version": 1,
            "event_id": "prompt060-smoke", "variable_id": "tank_level", "action_label": "set",
            "command_value": 1.0, "source_asset_id": source_id, "created_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=5)).isoformat(),
            "actuation_binding": {"binding_id": binding_id, "target_asset_id": target_id, "control_point": "relay_1", "operation": "set", "version": 1},
        },
    }
    try:
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO projects (id, name, status) VALUES (CAST(:id AS uuid), :name, 'active')"), {"id": project_id, "name": f"prompt060-smoke-{project_id}"})
            connection.execute(text("INSERT INTO sectors (id, project_id, name) VALUES (CAST(:id AS uuid), CAST(:project_id AS uuid), 'smoke')"), {"id": sector_id, "project_id": project_id})
            for asset_id, asset_type, metadata in (
                (source_id, "sensor", {}),
                (target_id, "actuator", {"control_capabilities": [{"key": "relay_1", "operations": ["set", "toggle"]}]}),
            ):
                connection.execute(text("""INSERT INTO assets (id, project_id, sector_id, asset_type, subtype, name, status, metadata)
                    VALUES (CAST(:id AS uuid), CAST(:project_id AS uuid), CAST(:sector_id AS uuid), CAST(:asset_type AS asset_type_enum), 'smoke', :name, 'active', CAST(:metadata AS jsonb))"""), {"id": asset_id, "project_id": project_id, "sector_id": sector_id, "asset_type": asset_type, "name": asset_type, "metadata": json.dumps(metadata)})
            connection.execute(text("""INSERT INTO project_control_policies (id, project_id, bound_asset_id, variable, policy_type, params)
                VALUES (CAST(:id AS uuid), CAST(:project_id AS uuid), CAST(:source AS uuid), 'tank_level', 'threshold', CAST(:params AS jsonb))"""), {"id": policy_id, "project_id": project_id, "source": source_id, "params": json.dumps({})})
            connection.execute(text("""INSERT INTO project_control_policy_actuation_bindings
                (id, policy_id, project_id, source_asset_id, target_asset_id, control_point, operation, version)
                VALUES (CAST(:id AS uuid), CAST(:policy AS uuid), CAST(:project AS uuid), CAST(:source AS uuid), CAST(:target AS uuid), 'relay_1', 'set', 1)"""), {"id": binding_id, "policy": policy_id, "project": project_id, "source": source_id, "target": target_id})

        consumer = SimulatedActuationConsumer(dispatch_immediately=False)
        queued = consumer.process(envelope)
        assert queued.status == "queued"
        for _ in range(20):
            if consumer.repository.get_by_command_id(queued.command_id).status == "acknowledged":
                break
            time.sleep(0.25)
        assert consumer.repository.get_by_command_id(queued.command_id).status == "acknowledged"
        outbox = ActuationOutboxRepository(engine)
        with engine.connect() as connection:
            event_row = connection.execute(text("SELECT event_id FROM control_actuation_outbox WHERE command_id=CAST(:id AS uuid)"), {"id": queued.command_id}).mappings().one()
        event = outbox.get(str(event_row["event_id"]))
        assert event.status == "published" and event.payload["physical_effects"] is False
        from iot_middleware.services.control_engine_worker import _load_rabbitmq_client
        client, _ = _load_rabbitmq_client()
        assert client.publish_json(routing_key=event.routing_key, payload=event.payload)
        time.sleep(1)
        duplicate_intent = consumer.repository.get_by_command_id(queued.command_id)
        assert duplicate_intent.status == "acknowledged" and duplicate_intent.retry_count == 1
        unbound = {**envelope, "payload": {**envelope["payload"], "recommendation_id": f"recommendation::{uuid.uuid4()}"}}
        unbound["payload"].pop("actuation_binding")
        assert consumer.process(unbound).status == "recommendation_only"
        print("PASS outbox published and duplicate dispatch preserved one acknowledged command; unbound recommendation stayed recommendation-only")
    finally:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM control_actuation_delivery_intents WHERE project_id = CAST(:id AS uuid)"), {"id": project_id})
            connection.execute(text("DELETE FROM projects WHERE id = CAST(:id AS uuid)"), {"id": project_id})


if __name__ == "__main__":
    main()
