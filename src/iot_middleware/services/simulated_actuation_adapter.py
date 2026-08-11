"""Deterministic adapter used only for safe simulated actuation delivery."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from parametric_control_engine.contracts.actuation_contracts import ActuationRequest, ActuationResult


class SimulatedTransientFailure(TimeoutError):
    """Deterministic test-only failure that is safe to retry."""


class SimulatedPermanentFailure(ValueError):
    """Deterministic test-only failure that must not be retried."""


class SimulatedActuationAdapter:
    """Adapter with zero network and zero physical side effects."""

    name = "simulated-actuation-adapter"
    version = "1.0"

    def __init__(self, *, test_failure_plan: tuple[str, ...] = ()) -> None:
        # Injected only by tests/fixtures; runtime configuration never enables it.
        self._test_failure_plan = tuple(test_failure_plan)

    def validate_target(self, request: ActuationRequest) -> None:
        if not request.simulated or request.target_kind != "simulated":
            raise ValueError("Simulated adapter only accepts explicit simulated targets")
        if not request.target_asset_id or not request.control_point or not request.actuation_binding_id:
            raise ValueError("Simulated adapter requires a governed target asset binding")
        if not request.target_reference.startswith(f"asset:{request.target_asset_id}:"):
            raise ValueError("Simulated target reference does not match target asset")

    def dispatch(self, request: ActuationRequest, *, attempt: int = 1) -> ActuationResult:
        self.validate_target(request)
        failure = self._test_failure_plan[attempt - 1] if attempt <= len(self._test_failure_plan) else None
        if failure == "transient":
            raise SimulatedTransientFailure("deterministic simulated transient failure")
        if failure == "permanent":
            raise SimulatedPermanentFailure("deterministic simulated permanent failure")
        started_at = datetime.now(timezone.utc).isoformat()
        finished_at = datetime.now(timezone.utc).isoformat()
        return ActuationResult(
            schema_version="1.0",
            command_id=request.command_id,
            recommendation_id=request.recommendation_id,
            correlation_id=request.correlation_id,
            project_id=request.project_id,
            status="acknowledged",
            attempt=attempt,
            adapter=f"{self.name}@{self.version}",
            started_at=started_at,
            finished_at=finished_at,
            simulated=True,
            result={
                "target_kind": "simulated",
                "target_asset_id": request.target_asset_id,
                "target_reference": request.target_reference,
                "control_point": request.control_point,
                "actuation_binding_id": request.actuation_binding_id,
                "actuation_binding_version": request.actuation_binding_version,
                "operation": request.operation,
                "requested_value": request.requested_value,
                "physical_effects": False,
            },
        )

    def normalize_result(self, result: ActuationResult) -> dict[str, Any]:
        return result.to_dict()
