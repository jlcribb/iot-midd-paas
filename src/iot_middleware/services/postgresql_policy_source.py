"""PostgreSQL-backed control policy source for control_engine_worker."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict, List, Tuple

from parametric_control_engine.contracts.event_adapter_contracts import (
    MonovariableControlBinding,
)
from parametric_control_engine.contracts.policy_contracts import StaticPolicyDefinition
from parametric_control_engine.contracts.policy_source_contracts import (
    PolicySourceRequest,
    PolicySourceResult,
)
from parametric_control_engine.models.control_models import (
    ControlParameters,
    ControlledVariableDefinition,
    SetpointReference,
    ThresholdControlParameters,
)
from parametric_control_engine.trace.trace_builder import ControlTraceBuilder

from iot_middleware.storage.db_handler import list_project_control_policies


class PostgreSQLPolicySource:
    """Load project-scoped policy candidates from public.project_control_policies."""

    source_name = "postgresql-policy-source"
    version = "0.1.0"

    def __init__(
        self,
        *,
        recommendation_channel: str,
        defaults: Dict[str, Any] | None = None,
    ) -> None:
        self._recommendation_channel = recommendation_channel
        self._defaults = defaults or {}

    def load_policies(self, request: PolicySourceRequest) -> PolicySourceResult:
        trace = ControlTraceBuilder(self.source_name, self.version)
        trace.add_step(
            "policy_source_request_received",
            {
                "request": asdict(request),
            },
        )

        project_id = str(request.context.get("project_id") or "").strip()
        if not project_id:
            trace.add_step(
                "policy_candidates_loaded",
                {
                    "reason": "missing_project_id",
                    "candidate_policy_ids": [],
                },
            )
            return PolicySourceResult(
                source_name=self.source_name,
                policies=[],
                source_trace=trace.build(),
            )

        rows = list_project_control_policies(project_id, request.variable_id)
        trace.add_step(
            "project_policy_rows_loaded",
            {
                "project_id": project_id,
                "variable_id": request.variable_id,
                "row_count": len(rows),
            },
        )

        policies: List[StaticPolicyDefinition] = []
        seen_signatures: set[Tuple[str, str, str, int]] = set()
        skipped_rows: List[Dict[str, Any]] = []

        for row in rows:
            signature = self._policy_signature(row)
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)

            try:
                policies.append(self._build_policy_definition(row))
            except Exception as exc:
                skipped_rows.append(
                    {
                        "policy_id": row.get("id"),
                        "error": str(exc),
                    }
                )

        if skipped_rows:
            trace.add_step(
                "invalid_policy_rows_skipped",
                {
                    "rows": skipped_rows,
                },
            )

        trace.add_step(
            "policy_candidates_loaded",
            {
                "candidate_policy_ids": [policy.policy_id for policy in policies],
            },
        )

        return PolicySourceResult(
            source_name=self.source_name,
            policies=policies,
            source_trace=trace.build(),
        )

    @staticmethod
    def _policy_signature(row: Dict[str, Any]) -> Tuple[str, str, str, str, int]:
        context_selector = row.get("context_selector") or {}
        return (
            str(row.get("project_id") or ""),
            str(row.get("variable") or ""),
            json.dumps(context_selector, sort_keys=True),
            str(row.get("policy_type") or "proportional"),
            int(row.get("priority") or 0),
        )

    def _build_policy_definition(self, row: Dict[str, Any]) -> StaticPolicyDefinition:
        params = dict(row.get("params") or {})
        context_selector = dict(row.get("context_selector") or {})
        policy_type = str(row.get("policy_type") or "proportional").strip().lower()

        return StaticPolicyDefinition(
            policy_id=str(row["id"]),
            binding=MonovariableControlBinding(
                variable=self._build_variable_definition(row, params),
                setpoint=self._build_setpoint_reference(params),
                parameters=self._build_parameter_set(policy_type, params),
                recommendation_channel=str(
                    params.get("recommendation_channel")
                    or self._recommendation_channel
                ),
                context={"project_id": str(row["project_id"])},
            ),
            required_context=context_selector,
            priority=int(row.get("priority") or 0),
            version=int(row.get("version") or 1),
            policy_type=policy_type,
            params=params,
            description=str(params.get("description") or ""),
        )

    def _build_variable_definition(
        self,
        row: Dict[str, Any],
        params: Dict[str, Any],
    ) -> ControlledVariableDefinition:
        variable_id = str(row["variable"])
        return ControlledVariableDefinition(
            variable_id=variable_id,
            name=str(
                params.get("variable_name")
                or self._defaults.get("variable_name")
                or variable_id.replace("_", " ").title()
            ),
            unit=str(
                params.get("variable_unit")
                or self._defaults.get("variable_unit")
                or "units"
            ),
            actuator_name=str(
                params.get("actuator_name")
                or self._defaults.get("actuator_name")
                or "control_output"
            ),
            increase_action_label=str(
                params.get("increase_action_label")
                or self._defaults.get("increase_action_label")
                or "increase"
            ),
            decrease_action_label=str(
                params.get("decrease_action_label")
                or self._defaults.get("decrease_action_label")
                or "decrease"
            ),
            hold_action_label=str(
                params.get("hold_action_label")
                or self._defaults.get("hold_action_label")
                or "hold"
            ),
            controller_direction=float(
                params.get("controller_direction")
                or self._defaults.get("controller_direction")
                or 1.0
            ),
            description=str(
                params.get("variable_description")
                or self._defaults.get("variable_description")
                or "Runtime-bound project control variable definition"
            ),
        )

    def _build_setpoint_reference(self, params: Dict[str, Any]) -> SetpointReference:
        metadata = params.get("setpoint_metadata")
        if not isinstance(metadata, dict):
            metadata = {"source": "project-control-policies"}

        return SetpointReference(
            value=float(
                params.get("setpoint_value")
                or self._defaults.get("setpoint_value")
                or 70.0
            ),
            label=str(
                params.get("setpoint_label")
                or self._defaults.get("setpoint_label")
                or "project-policy-setpoint"
            ),
            metadata=metadata,
        )

    def _build_parameter_set(self, policy_type: str, params: Dict[str, Any]) -> Any:
        if policy_type == "threshold":
            return ThresholdControlParameters(
                tolerance=float(params.get("tolerance", 0.5)),
                increase_step=float(params.get("increase_step", 1.0)),
                decrease_step=float(params.get("decrease_step", 1.0)),
                hold_signal=float(params.get("hold_signal", 0.0)),
            )

        if policy_type != "proportional":
            raise ValueError(f"Unsupported policy_type={policy_type!r}")

        max_action = params.get("max_action")
        return ControlParameters(
            gain=float(params.get("gain", 1.0)),
            deadband=float(params.get("deadband", 0.0)),
            min_action=float(params.get("min_action", 0.0)),
            max_action=float(max_action) if max_action is not None else None,
        )
