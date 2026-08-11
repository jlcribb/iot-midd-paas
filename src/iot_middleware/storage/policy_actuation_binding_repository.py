"""Read-only runtime lookup for governed policy actuation bindings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import text

from iot_middleware.storage.db_handler import _get_control_settings_connection_url, _get_control_settings_engine


ELIGIBLE_TARGET_TYPES = frozenset({"actuator", "relay_module", "programmable_node"})


@dataclass(frozen=True)
class PolicyActuationBinding:
    id: str
    policy_id: str
    project_id: str
    source_asset_id: str
    target_asset_id: str
    control_point: str
    operation: str
    version: int
    target_asset_type: str
    target_metadata: dict[str, Any]


class PolicyActuationBindingRepository:
    def __init__(self, engine=None) -> None:
        self._engine = engine or _get_control_settings_engine(_get_control_settings_connection_url())

    def get_active(self, policy_id: str) -> Optional[PolicyActuationBinding]:
        query = text(
            """
            SELECT b.id, b.policy_id, b.project_id, b.source_asset_id, b.target_asset_id,
                   b.control_point, b.operation, b.version, target.asset_type AS target_asset_type,
                   target.metadata AS target_metadata
            FROM public.project_control_policy_actuation_bindings b
            JOIN public.assets target
              ON target.id = b.target_asset_id AND target.project_id = b.project_id
            WHERE b.policy_id = CAST(:policy_id AS uuid) AND b.enabled = TRUE
            """
        )
        with self._engine.connect() as connection:
            row = connection.execute(query, {"policy_id": policy_id}).mappings().first()
        if not row:
            return None
        return PolicyActuationBinding(
            id=str(row["id"]), policy_id=str(row["policy_id"]), project_id=str(row["project_id"]),
            source_asset_id=str(row["source_asset_id"]), target_asset_id=str(row["target_asset_id"]),
            control_point=str(row["control_point"]), operation=str(row["operation"]),
            version=int(row["version"]), target_asset_type=str(row["target_asset_type"]),
            target_metadata=dict(row["target_metadata"] or {}),
        )

    @staticmethod
    def supports(binding: PolicyActuationBinding) -> bool:
        if binding.target_asset_type not in ELIGIBLE_TARGET_TYPES:
            return False
        capabilities = binding.target_metadata.get("control_capabilities")
        if not isinstance(capabilities, list):
            return False
        return any(
            isinstance(item, dict)
            and item.get("key") == binding.control_point
            and binding.operation in item.get("operations", [])
            for item in capabilities
        )
