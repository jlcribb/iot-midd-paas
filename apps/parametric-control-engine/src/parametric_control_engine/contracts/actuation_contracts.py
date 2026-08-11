"""Versioned contracts for governed, simulated actuation delivery.

These contracts deliberately describe delivery after a recommendation has been
validated.  They do not model, authorize, or perform physical actuation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Dict, Optional


CONTROL_RECOMMENDATION_SCHEMA_VERSION = "1.0"
ACTUATION_REQUEST_SCHEMA_VERSION = "1.0"
ACTUATION_RESULT_SCHEMA_VERSION = "1.0"
SIMULATED_GOVERNANCE_MODE = "simulated"
SIMULATED_TARGET_KIND = "simulated"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def stable_recommendation_id(
    *,
    project_id: str,
    event_id: str,
    variable_id: str,
    policy_id: str,
    policy_version: int | str,
    source_asset_id: Optional[str],
) -> str:
    """Return a deterministic identity for one evaluated recommendation."""
    source = source_asset_id or "unbound"
    material = "|".join(
        [str(project_id), str(event_id), str(variable_id), str(policy_id), str(policy_version), source]
    )
    return f"recommendation::{sha256(material.encode('utf-8')).hexdigest()[:32]}"


def stable_idempotency_key(
    *,
    project_id: str,
    recommendation_id: str,
    target_kind: str,
    target_reference: str,
    operation: str,
    policy_version: int | str,
) -> str:
    material = "|".join(
        [
            str(project_id),
            str(recommendation_id),
            str(target_kind),
            str(target_reference),
            str(operation),
            str(policy_version),
        ]
    )
    return f"actuation::{sha256(material.encode('utf-8')).hexdigest()[:48]}"


@dataclass(frozen=True)
class ActuationRequest:
    schema_version: str
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
    variable_id: str
    operation: str
    requested_value: float
    created_at: str
    expires_at: str
    governance_mode: str
    idempotency_key: str
    simulated: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActuationResult:
    schema_version: str
    command_id: str
    recommendation_id: str
    correlation_id: str
    project_id: str
    status: str
    attempt: int
    adapter: str
    started_at: str
    finished_at: str
    simulated: bool
    result: Dict[str, Any]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def expires_at_from(created_at: datetime, ttl_seconds: int) -> str:
    return (created_at + timedelta(seconds=max(1, ttl_seconds))).isoformat()
