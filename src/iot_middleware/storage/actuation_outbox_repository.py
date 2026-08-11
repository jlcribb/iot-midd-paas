"""Transactional outbox persistence for simulated dispatch; never publishes to a broker."""
from __future__ import annotations
import json, uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy import text
from iot_middleware.storage.db_handler import _get_control_settings_connection_url, _get_control_settings_engine

DISPATCH_EVENT_TYPE = "control.actuation.simulated.dispatch"
DISPATCH_SCHEMA_VERSION = "1.0"
DISPATCH_ROUTING_KEY = "control.actuation.simulated.dispatch.v1"

@dataclass(frozen=True)
class OutboxEvent:
    id: str; event_id: str; command_id: str; payload: dict[str, Any]; status: str; attempt_count: int
    routing_key: str; published_at: datetime | None; available_at: datetime; last_error: str | None

def _map(row: Any) -> OutboxEvent:
    return OutboxEvent(str(row['id']), str(row['event_id']), str(row['command_id']), dict(row['payload']), str(row['status']), int(row['attempt_count']), str(row['routing_key']), row['published_at'], row['available_at'], row['last_error'])

class ActuationOutboxRepository:
    def __init__(self, engine=None): self._engine = engine or _get_control_settings_engine(_get_control_settings_connection_url())

    def insert_for_request(self, connection, request: Any) -> OutboxEvent:
        event_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"midd-iot:{request.command_id}:{DISPATCH_EVENT_TYPE}"))
        payload = {"message_type": DISPATCH_EVENT_TYPE, "schema_version": DISPATCH_SCHEMA_VERSION, "event_id": event_id, "simulated": True, "physical_effects": False, "payload": request.to_dict()}
        row = connection.execute(text("""INSERT INTO control_actuation_outbox
          (event_id,event_type,schema_version,aggregate_type,command_id,recommendation_id,correlation_id,project_id,target_asset_id,control_point,binding_id,binding_version,routing_key,payload)
          VALUES (CAST(:event_id AS uuid),:event_type,:schema_version,'actuation_delivery_intent',CAST(:command_id AS uuid),:recommendation_id,:correlation_id,CAST(:project_id AS uuid),CAST(:target_asset_id AS uuid),:control_point,CAST(:binding_id AS uuid),:binding_version,:routing_key,CAST(:payload AS jsonb))
          ON CONFLICT (command_id,event_type) DO NOTHING RETURNING *"""), {"event_id":event_id,"event_type":DISPATCH_EVENT_TYPE,"schema_version":DISPATCH_SCHEMA_VERSION,"command_id":request.command_id,"recommendation_id":request.recommendation_id,"correlation_id":request.correlation_id,"project_id":request.project_id,"target_asset_id":request.target_asset_id,"control_point":request.control_point,"binding_id":request.actuation_binding_id,"binding_version":request.actuation_binding_version,"routing_key":DISPATCH_ROUTING_KEY,"payload":json.dumps(payload)}).mappings().first()
        if not row: row = connection.execute(text("SELECT * FROM control_actuation_outbox WHERE command_id=CAST(:command_id AS uuid) AND event_type=:event_type"), {"command_id":request.command_id,"event_type":DISPATCH_EVENT_TYPE}).mappings().one()
        return _map(row)

    def claim(self, limit=20, lease_seconds=30) -> list[OutboxEvent]:
        with self._engine.begin() as c:
            rows=c.execute(text("""WITH picked AS (SELECT id FROM control_actuation_outbox WHERE (status='pending' AND available_at<=now()) OR (status='publishing' AND lease_until<=now()) ORDER BY available_at FOR UPDATE SKIP LOCKED LIMIT :limit)
            UPDATE control_actuation_outbox o SET status='publishing',claimed_at=now(),lease_until=now()+CAST(:lease AS interval) FROM picked WHERE o.id=picked.id RETURNING o.*"""), {"limit":limit,"lease":f"{lease_seconds} seconds"}).mappings().all()
        return [_map(x) for x in rows]
    def mark_published(self, event_id: str) -> None:
        with self._engine.begin() as c: c.execute(text("UPDATE control_actuation_outbox SET status='published', published_at=now(), lease_until=NULL, last_error=NULL WHERE event_id=CAST(:id AS uuid)"), {"id":event_id})
    def retry_or_fail(self,event_id:str,error:Exception,max_attempts=3,base_delay=1)->None:
        with self._engine.begin() as c:
            c.execute(text("""UPDATE control_actuation_outbox SET attempt_count=attempt_count+1, status=CASE WHEN attempt_count+1>=:max THEN 'failed' ELSE 'pending' END, available_at=now()+CAST(:delay AS interval), lease_until=NULL,last_error=:error WHERE event_id=CAST(:id AS uuid)"""), {"id":event_id,"max":max_attempts,"delay":f"{base_delay} seconds","error":f"{type(error).__name__}:{error}"})
    def counts(self)->dict[str,int]:
        with self._engine.connect() as c: return {str(x['status']):int(x['count']) for x in c.execute(text("SELECT status,count(*) FROM control_actuation_outbox GROUP BY status")).mappings()}
