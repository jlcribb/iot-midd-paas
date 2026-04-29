"""First minimal parametric evaluator based on proportional control."""

from __future__ import annotations

from dataclasses import asdict
from typing import Tuple

from ..contracts.control_contracts import (
    ControlEvaluationRequest,
    ControlEvaluationResponse,
)
from ..models.control_models import ActionKind, ActionRecommendation
from ..trace.trace_builder import ControlTraceBuilder


class ProportionalEvaluator:
    """Evaluates a single process variable using a proportional control policy."""

    name = "proportional"
    version = "0.1.0"

    def evaluate(self, request: ControlEvaluationRequest) -> ControlEvaluationResponse:
        """Produce a deterministic action recommendation with full trace data."""
        trace = ControlTraceBuilder(self.name, self.version)
        trace.add_step(
            "input_received",
            {
                "variable": asdict(request.variable),
                "measurement": asdict(request.measurement),
                "setpoint": asdict(request.setpoint),
                "parameters": asdict(request.parameters),
                "context": request.context,
            },
        )

        error = request.setpoint.value - request.measurement.value
        trace.add_step(
            "error_computed",
            {
                "setpoint_value": request.setpoint.value,
                "measurement_value": request.measurement.value,
                "error": error,
            },
        )

        raw_signal = request.parameters.gain * error
        direction_adjusted_signal = raw_signal * request.variable.controller_direction
        trace.add_step(
            "raw_signal_computed",
            {
                "gain": request.parameters.gain,
                "raw_signal": raw_signal,
                "controller_direction": request.variable.controller_direction,
                "direction_adjusted_signal": direction_adjusted_signal,
            },
        )

        applied_signal, constraint_reason = self._apply_constraints(
            signal=direction_adjusted_signal,
            deadband=request.parameters.deadband,
            min_action=request.parameters.min_action,
            max_action=request.parameters.max_action,
        )
        trace.add_step(
            "constraints_applied",
            {
                "deadband": request.parameters.deadband,
                "min_action": request.parameters.min_action,
                "max_action": request.parameters.max_action,
                "constraint_reason": constraint_reason,
                "applied_signal": applied_signal,
            },
        )

        recommendation = self._build_recommendation(request, error, applied_signal)
        trace.add_step(
            "recommendation_built",
            {
                "kind": recommendation.kind.value,
                "action_label": recommendation.action_label,
                "command_value": recommendation.command_value,
                "summary": recommendation.summary,
            },
        )

        return ControlEvaluationResponse(
            variable_id=request.variable.variable_id,
            evaluator_name=self.name,
            error=error,
            raw_control_signal=raw_signal,
            applied_control_signal=applied_signal,
            recommendation=recommendation,
            trace=trace.build(),
        )

    def _apply_constraints(
        self,
        *,
        signal: float,
        deadband: float,
        min_action: float,
        max_action: float | None,
    ) -> Tuple[float, str]:
        abs_signal = abs(signal)

        if abs_signal <= deadband:
            return 0.0, "deadband_hold"

        constrained_signal = signal
        reasons = []

        if abs_signal < min_action:
            constrained_signal = min_action if signal > 0 else -min_action
            reasons.append("min_action_floor")

        if max_action is not None and abs(constrained_signal) > max_action:
            constrained_signal = max_action if constrained_signal > 0 else -max_action
            reasons.append("max_action_clamp")

        if not reasons:
            reasons.append("none")

        return constrained_signal, ",".join(reasons)

    def _build_recommendation(
        self,
        request: ControlEvaluationRequest,
        error: float,
        applied_signal: float,
    ) -> ActionRecommendation:
        variable = request.variable

        if applied_signal > 0:
            kind = ActionKind.INCREASE
            action_label = variable.increase_action_label
        elif applied_signal < 0:
            kind = ActionKind.DECREASE
            action_label = variable.decrease_action_label
        else:
            kind = ActionKind.HOLD
            action_label = variable.hold_action_label

        summary = (
            f"{action_label} {variable.actuator_name} "
            f"for {variable.name}: error={error:.3f} {variable.unit}, "
            f"command={applied_signal:.3f}"
        )

        return ActionRecommendation(
            kind=kind,
            actuator_name=variable.actuator_name,
            action_label=action_label,
            command_value=applied_signal,
            summary=summary,
            metadata={
                "variable_name": variable.name,
                "unit": variable.unit,
                "controller_direction": variable.controller_direction,
            },
        )
