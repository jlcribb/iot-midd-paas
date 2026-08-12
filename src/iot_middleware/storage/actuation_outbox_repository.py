"""Transactional persistence and recovery operations for simulated dispatch outbox."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import text

from iot_middleware.storage.db_handler import _get_control_settings_connection_url, _get_control_settings_engine

DISPATCH_EVENT_TYPE = "control.actuation.simulated.dispatch"
DISPATCH_SCHEMA_VERSION = "1.0"
DISPATCH_ROUTING_KEY = "control.actuation.simulated.dispatch.v1"


@dataclass(frozen=True)
class OutboxEvent:
    id: str
    event_id: str
    command_id: str
    recommendation_id: str
    correlation_id: str
    project_id: str
    target_asset_id: str | None
    control_point: str | None
    binding_id: str | None
    binding_version: int | None
    payload: dict[str, Any]
    status: str
    attempt_count: int
    routing_key: str
    published_at: datetime | None
    available_at: datetime
    lease_until: datetime | None
    last_error: str | None
    created_at: datetime


def _map(row: Any) -> OutboxEvent:
    return OutboxEvent(
        id=str(row["id"]), event_id=str(row["event_id"]), command_id=str(row["command_id"]),
        recommendation_id=str(row["recommendation_id"]), correlation_id=str(row["correlation_id"]),
        project_id=str(row["project_id"]), target_asset_id=str(row["target_asset_id"]) if row["target_asset_id"] else None,
        control_point=row["control_point"], binding_id=str(row["binding_id"]) if row["binding_id"] else None,
        binding_version=int(row["binding_version"]) if row["binding_version"] is not None else None,
        payload=dict(row["payload"]), status=str(row["status"]), attempt_count=int(row["attempt_count"]),
        routing_key=str(row["routing_key"]), published_at=row["published_at"], available_at=row["available_at"],
        lease_until=row["lease_until"], last_error=row["last_error"], created_at=row["created_at"],
    )


class ActuationOutboxRepository:
    def __init__(self, engine=None) -> None:
        self._engine = engine or _get_control_settings_engine(_get_control_settings_connection_url())

    def insert_for_request(self, connection, request: Any) -> OutboxEvent:
        event_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"midd-iot:{request.command_id}:{DISPATCH_EVENT_TYPE}"))
        payload = {
            "message_type": DISPATCH_EVENT_TYPE, "schema_version": DISPATCH_SCHEMA_VERSION,
            "event_id": event_id, "simulated": True, "physical_effects": False,
            "payload": request.to_dict(),
        }
        row = connection.execute(text("""
            INSERT INTO public.control_actuation_outbox (
              event_id,event_type,schema_version,aggregate_type,command_id,recommendation_id,correlation_id,
              project_id,target_asset_id,control_point,binding_id,binding_version,routing_key,payload
            ) VALUES (
              CAST(:event_id AS uuid),:event_type,:schema_version,'actuation_delivery_intent',CAST(:command_id AS uuid),
              :recommendation_id,:correlation_id,CAST(:project_id AS uuid),CAST(:target_asset_id AS uuid),:control_point,
              CAST(:binding_id AS uuid),:binding_version,:routing_key,CAST(:payload AS jsonb)
            ) ON CONFLICT (command_id,event_type) DO NOTHING RETURNING *
        """), {
            "event_id": event_id, "event_type": DISPATCH_EVENT_TYPE, "schema_version": DISPATCH_SCHEMA_VERSION,
            "command_id": request.command_id, "recommendation_id": request.recommendation_id,
            "correlation_id": request.correlation_id, "project_id": request.project_id,
            "target_asset_id": request.target_asset_id, "control_point": request.control_point,
            "binding_id": request.actuation_binding_id, "binding_version": request.actuation_binding_version,
            "routing_key": DISPATCH_ROUTING_KEY, "payload": json.dumps(payload),
        }).mappings().first()
        if row is None:
            row = connection.execute(text("""
                SELECT * FROM public.control_actuation_outbox
                WHERE command_id=CAST(:command_id AS uuid) AND event_type=:event_type
            """), {"command_id": request.command_id, "event_type": DISPATCH_EVENT_TYPE}).mappings().one()
        return _map(row)

    def claim(self, *, limit: int = 20, lease_seconds: int = 30) -> list[OutboxEvent]:
        """Claim ready or expired-lease events; each claim is a persisted publish attempt."""
        with self._engine.begin() as connection:
            rows = connection.execute(text("""
                WITH picked AS (
                  SELECT id FROM public.control_actuation_outbox
                  WHERE (status='pending' AND available_at<=NOW())
                     OR (status='publishing' AND lease_until<=NOW())
                  ORDER BY available_at, created_at
                  FOR UPDATE SKIP LOCKED LIMIT :limit
                )
                UPDATE public.control_actuation_outbox outbox
                SET status='publishing', claimed_at=NOW(), lease_until=NOW()+CAST(:lease AS interval),
                    attempt_count=attempt_count+1
                FROM picked WHERE outbox.id=picked.id RETURNING outbox.*
            """), {"limit": limit, "lease": f"{lease_seconds} seconds"}).mappings().all()
        return [_map(row) for row in rows]

    def mark_published(self, event_id: str) -> None:
        with self._engine.begin() as connection:
            connection.execute(text("""
                UPDATE public.control_actuation_outbox
                SET status='published', published_at=NOW(), lease_until=NULL, last_error=NULL
                WHERE event_id=CAST(:event_id AS uuid) AND status='publishing'
            """), {"event_id": event_id})

    def retry_or_fail(self, event: OutboxEvent, error: Exception, *, max_attempts: int = 3, base_delay_seconds: float = 1.0) -> str:
        delay = min(30.0, max(0.0, base_delay_seconds) * (2 ** max(0, event.attempt_count - 1)))
        with self._engine.begin() as connection:
            row = connection.execute(text("""
                UPDATE public.control_actuation_outbox
                SET status=CASE WHEN attempt_count>=:max_attempts THEN 'failed' ELSE 'pending' END,
                    available_at=NOW()+CAST(:delay AS interval), lease_until=NULL,
                    last_error=:error
                WHERE event_id=CAST(:event_id AS uuid) AND status='publishing'
                RETURNING status
            """), {"event_id": event.event_id, "max_attempts": max_attempts,
                  "delay": f"{delay} seconds", "error": f"{type(error).__name__}:{error}"}).mappings().one()
        return str(row["status"])

    def get(self, event_id: str) -> OutboxEvent | None:
        with self._engine.connect() as connection:
            row = connection.execute(text("SELECT * FROM public.control_actuation_outbox WHERE event_id=CAST(:event_id AS uuid)"), {"event_id": event_id}).mappings().first()
        return _map(row) if row else None

    def metrics(self) -> dict[str, int | float | None]:
        with self._engine.connect() as connection:
            row = connection.execute(text("""
                SELECT count(*) FILTER (WHERE status='pending') AS pending_count,
                       count(*) FILTER (WHERE status='published') AS published_count,
                       count(*) FILTER (WHERE status='failed') AS failed_count,
                       COALESCE(sum(attempt_count), 0) AS publish_attempts,
                       COALESCE(sum(attempt_count) FILTER (WHERE last_error IS NOT NULL), 0) AS publish_failures,
                       EXTRACT(EPOCH FROM (NOW()-MIN(created_at) FILTER (WHERE status IN ('pending','publishing')))) AS oldest_pending_age_seconds
                FROM public.control_actuation_outbox
            """)).mappings().one()
        return {key: float(value) if key == "oldest_pending_age_seconds" and value is not None else int(value or 0) if key != "oldest_pending_age_seconds" else None for key, value in row.items()}
