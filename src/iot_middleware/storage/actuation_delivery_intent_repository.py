"""Persistence boundary for simulated actuation delivery intents.

This module contains storage operations only. Governance and dispatch decisions
remain in the simulated actuation service.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Optional

from sqlalchemy import text

from iot_middleware.storage.db_handler import (
    _get_control_settings_connection_url,
    _get_control_settings_engine,
)


DELIVERY_STATUSES = frozenset(
    {
        "received",
        "validated",
        "ready_to_dispatch",
        "dispatched",
        "retry_pending",
        "acknowledged",
        "rejected",
        "expired",
        "failed_final",
    }
)

VALID_TRANSITIONS = {
    "received": {"validated", "rejected", "expired"},
    "validated": {"ready_to_dispatch", "rejected", "expired"},
    "ready_to_dispatch": {"dispatched", "expired", "failed_final"},
    "dispatched": {"acknowledged", "retry_pending", "failed_final"},
    "retry_pending": {"dispatched", "failed_final", "expired"},
    "acknowledged": set(),
    "rejected": set(),
    "expired": set(),
    "failed_final": set(),
}


class InvalidDeliveryTransition(ValueError):
    pass


@dataclass(frozen=True)
class DeliveryIntent:
    id: str
    command_id: str
    recommendation_id: str
    correlation_id: str
    project_id: str
    policy_id: str
    policy_version: int
    source_asset_id: Optional[str]
    target_asset_id: Optional[str]
    target_kind: str
    target_reference: str
    control_point: Optional[str]
    actuation_binding_id: Optional[str]
    actuation_binding_version: Optional[int]
    variable_id: str
    operation: str
    requested_value: float
    idempotency_key: str
    governance_mode: str
    status: str
    retry_count: int
    last_attempt_at: Optional[datetime]
    next_retry_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    last_error: Optional[str]
    simulated: bool


def _map_row(row: Any) -> DeliveryIntent:
    return DeliveryIntent(
        id=str(row["id"]),
        command_id=str(row["command_id"]),
        recommendation_id=str(row["recommendation_id"]),
        correlation_id=str(row["correlation_id"]),
        project_id=str(row["project_id"]),
        policy_id=str(row["policy_id"]),
        policy_version=int(row["policy_version"]),
        source_asset_id=str(row["source_asset_id"]) if row["source_asset_id"] else None,
        target_asset_id=str(row["target_asset_id"]) if row["target_asset_id"] else None,
        target_kind=str(row["target_kind"]),
        target_reference=str(row["target_reference"]),
        control_point=str(row["control_point"]) if row["control_point"] else None,
        actuation_binding_id=str(row["actuation_binding_id"]) if row["actuation_binding_id"] else None,
        actuation_binding_version=int(row["actuation_binding_version"]) if row["actuation_binding_version"] else None,
        variable_id=str(row["variable_id"]),
        operation=str(row["operation"]),
        requested_value=float(row["requested_value"]),
        idempotency_key=str(row["idempotency_key"]),
        governance_mode=str(row["governance_mode"]),
        status=str(row["status"]),
        retry_count=int(row["retry_count"]),
        last_attempt_at=row["last_attempt_at"],
        next_retry_at=row["next_retry_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        expires_at=row["expires_at"],
        last_error=row["last_error"],
        simulated=bool(row["simulated"]),
    )


class ActuationDeliveryIntentRepository:
    """PostgreSQL-backed create-or-get and state transition operations."""

    def __init__(self, engine=None) -> None:
        self._engine = engine or _get_control_settings_engine(_get_control_settings_connection_url())

    def create_or_get(self, request: Any) -> tuple[DeliveryIntent, bool]:
        values = {
            "id": str(uuid.uuid4()),
            "command_id": request.command_id,
            "recommendation_id": request.recommendation_id,
            "correlation_id": request.correlation_id,
            "project_id": request.project_id,
            "policy_id": request.policy_id,
            "policy_version": request.policy_version,
            "source_asset_id": request.source_asset_id,
            "target_asset_id": request.target_asset_id,
            "target_kind": request.target_kind,
            "target_reference": request.target_reference,
            "control_point": request.control_point,
            "actuation_binding_id": request.actuation_binding_id,
            "actuation_binding_version": request.actuation_binding_version,
            "variable_id": request.variable_id,
            "operation": request.operation,
            "requested_value": request.requested_value,
            "idempotency_key": request.idempotency_key,
            "governance_mode": request.governance_mode,
            "expires_at": request.expires_at,
            "simulated": request.simulated,
        }
        insert = text(
            """
            INSERT INTO public.control_actuation_delivery_intents (
                id, command_id, recommendation_id, correlation_id, project_id,
                policy_id, policy_version, source_asset_id, target_asset_id,
                target_kind, target_reference, control_point, actuation_binding_id,
                actuation_binding_version, variable_id, operation,
                requested_value, idempotency_key, governance_mode, expires_at, simulated
            ) VALUES (
                CAST(:id AS uuid), CAST(:command_id AS uuid), :recommendation_id,
                :correlation_id, CAST(:project_id AS uuid), :policy_id, :policy_version,
                CAST(:source_asset_id AS uuid), CAST(:target_asset_id AS uuid),
                :target_kind, :target_reference, :control_point, CAST(:actuation_binding_id AS uuid),
                :actuation_binding_version, :variable_id, :operation,
                :requested_value, :idempotency_key, :governance_mode,
                CAST(:expires_at AS timestamptz), :simulated
            )
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING *
            """
        )
        existing = text(
            "SELECT * FROM public.control_actuation_delivery_intents WHERE idempotency_key = :idempotency_key"
        )
        with self._engine.begin() as connection:
            row = connection.execute(insert, values).mappings().first()
            if row:
                return _map_row(row), True
            row = connection.execute(existing, {"idempotency_key": request.idempotency_key}).mappings().one()
            return _map_row(row), False

    def transition(
        self,
        *,
        command_id: str,
        from_statuses: Iterable[str],
        to_status: str,
        last_error: Optional[str] = None,
        increment_retry_count: bool = False,
        next_retry_at: Optional[datetime] = None,
        record_attempt: bool = False,
    ) -> DeliveryIntent:
        allowed = set(from_statuses)
        if to_status not in DELIVERY_STATUSES or not allowed:
            raise InvalidDeliveryTransition("Unknown delivery status or empty transition source")
        if any(to_status not in VALID_TRANSITIONS.get(status, set()) for status in allowed):
            raise InvalidDeliveryTransition(f"Invalid transition {allowed} -> {to_status}")

        query = text(
            """
            UPDATE public.control_actuation_delivery_intents
            SET status = :to_status,
                last_error = :last_error,
                retry_count = retry_count + CASE WHEN :increment_retry_count THEN 1 ELSE 0 END,
                last_attempt_at = CASE WHEN :record_attempt THEN NOW() ELSE last_attempt_at END,
                next_retry_at = :next_retry_at,
                updated_at = NOW()
            WHERE command_id = CAST(:command_id AS uuid)
              AND status = ANY(CAST(:from_statuses AS text[]))
            RETURNING *
            """
        )
        with self._engine.begin() as connection:
            row = connection.execute(
                query,
                {
                    "command_id": command_id,
                    "from_statuses": list(allowed),
                    "to_status": to_status,
                    "last_error": last_error,
                    "increment_retry_count": increment_retry_count,
                    "next_retry_at": next_retry_at,
                    "record_attempt": record_attempt,
                },
            ).mappings().first()
        if not row:
            raise InvalidDeliveryTransition(f"No intent can transition to {to_status}")
        return _map_row(row)

    def prepare_dispatch_with_outbox(self, request: Any):
        """Atomically move a fresh intent to ready_to_dispatch and persist its event."""
        from iot_middleware.storage.actuation_outbox_repository import ActuationOutboxRepository
        with self._engine.begin() as connection:
            validated = connection.execute(text("""UPDATE public.control_actuation_delivery_intents
                SET status='validated', updated_at=NOW() WHERE command_id=CAST(:command_id AS uuid) AND status='received' RETURNING *"""), {"command_id": request.command_id}).mappings().first()
            if not validated:
                raise InvalidDeliveryTransition("Intent cannot be prepared for dispatch")
            ready = connection.execute(text("""UPDATE public.control_actuation_delivery_intents
                SET status='ready_to_dispatch', updated_at=NOW() WHERE command_id=CAST(:command_id AS uuid) AND status='validated' RETURNING *"""), {"command_id": request.command_id}).mappings().one()
            event = ActuationOutboxRepository(self._engine).insert_for_request(connection, request)
        return _map_row(ready), event

    def get_due_retries(self, *, now: Optional[datetime] = None, limit: int = 20) -> list[DeliveryIntent]:
        """Return retryable intents due for one bounded, idempotent retry claim."""
        query = text(
            """
            SELECT *
            FROM public.control_actuation_delivery_intents
            WHERE status = 'retry_pending'
              AND next_retry_at IS NOT NULL
              AND next_retry_at <= COALESCE(CAST(:now AS timestamptz), NOW())
            ORDER BY next_retry_at ASC, created_at ASC
            LIMIT :limit
            """
        )
        with self._engine.connect() as connection:
            rows = connection.execute(query, {"now": now, "limit": limit}).mappings().all()
        return [_map_row(row) for row in rows]

    def get_by_command_id(self, command_id: str) -> Optional[DeliveryIntent]:
        query = text(
            "SELECT * FROM public.control_actuation_delivery_intents WHERE command_id = CAST(:command_id AS uuid)"
        )
        with self._engine.connect() as connection:
            row = connection.execute(query, {"command_id": command_id}).mappings().first()
        return _map_row(row) if row else None
