"""Deterministic adapter used only for safe simulated actuation delivery."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from parametric_control_engine.contracts.actuation_contracts import ActuationRequest, ActuationResult


class SimulatedActuationAdapter:
    """Adapter with zero network and zero physical side effects."""

    name = "simulated-actuation-adapter"
    version = "1.0"

    def validate_target(self, request: ActuationRequest) -> None:
        if not request.simulated or request.target_kind != "simulated":
            raise ValueError("Simulated adapter only accepts explicit simulated targets")
        if not request.target_reference.strip():
            raise ValueError("Simulated target reference is required")

    def dispatch(self, request: ActuationRequest, *, attempt: int = 1) -> ActuationResult:
        self.validate_target(request)
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
                "target_reference": request.target_reference,
                "operation": request.operation,
                "requested_value": request.requested_value,
                "physical_effects": False,
            },
        )

    def normalize_result(self, result: ActuationResult) -> dict[str, Any]:
        return result.to_dict()
