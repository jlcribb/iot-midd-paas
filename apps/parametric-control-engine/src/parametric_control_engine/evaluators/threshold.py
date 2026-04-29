"""Simple threshold-based controller for experimental comparison."""

from __future__ import annotations

from dataclasses import asdict

from ..contracts.control_contracts import (
    ControlEvaluationRequest,
    ControlEvaluationResponse,
)
from ..models.control_models import (
    ActionKind,
    ActionRecommendation,
    ThresholdControlParameters,
)
from ..trace.trace_builder import ControlTraceBuilder


class ThresholdEvaluator:
    """Evaluates a process variable using fixed steps around a threshold band."""

    name = "threshold"
    version = "0.1.0"

    def evaluate(self, request: ControlEvaluationRequest) -> ControlEvaluationResponse:
        """Produce a fixed-step recommendation from a threshold band."""
        if not isinstance(request.parameters, ThresholdControlParameters):
            raise TypeError(
                "ThresholdEvaluator requires ThresholdControlParameters"
            )

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
        lower_band = request.setpoint.value - request.parameters.tolerance
        upper_band = request.setpoint.value + request.parameters.tolerance
        trace.add_step(
            "threshold_band_computed",
            {
                "setpoint_value": request.setpoint.value,
                "measurement_value": request.measurement.value,
                "error": error,
                "lower_band": lower_band,
                "upper_band": upper_band,
            },
        )

        raw_signal, decision_reason = self._select_signal(
            measurement_value=request.measurement.value,
            lower_band=lower_band,
            upper_band=upper_band,
            params=request.parameters,
        )
        applied_signal = raw_signal * request.variable.controller_direction
        trace.add_step(
            "threshold_decision_made",
            {
                "raw_signal": raw_signal,
                "controller_direction": request.variable.controller_direction,
                "applied_signal": applied_signal,
                "decision_reason": decision_reason,
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

    def _select_signal(
        self,
        *,
        measurement_value: float,
        lower_band: float,
        upper_band: float,
        params: ThresholdControlParameters,
    ) -> tuple[float, str]:
        if measurement_value < lower_band:
            return params.increase_step, "below_lower_band"
        if measurement_value > upper_band:
            return -params.decrease_step, "above_upper_band"
        return params.hold_signal, "inside_threshold_band"

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
