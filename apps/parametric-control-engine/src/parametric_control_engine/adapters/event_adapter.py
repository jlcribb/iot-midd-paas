"""Minimal event-to-recommendation adapter for the control engine MVP."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

from ..contracts.control_contracts import ControlEvaluationRequest
from ..contracts.event_adapter_contracts import (
    EventDrivenRecommendation,
    MonovariableControlBinding,
    TelemetryStateEvent,
)
from ..evaluators.proportional import ProportionalEvaluator
from ..evaluators.threshold import ThresholdEvaluator
from ..models.control_models import MeasurementState
from ..trace.trace_builder import ControlTraceBuilder


class EventDrivenRecommendationAdapter:
    """Transforms telemetry/state events into control evaluations."""

    name = "event-driven-recommendation-adapter"
    version = "0.1.0"

    def __init__(
        self,
        binding: MonovariableControlBinding,
        evaluator: ProportionalEvaluator | ThresholdEvaluator | None = None,
    ) -> None:
        self._binding = binding
        self._evaluator = evaluator or ProportionalEvaluator()

    def to_evaluation_request(
        self,
        event: TelemetryStateEvent,
    ) -> tuple[ControlEvaluationRequest, list]:
        """Convert an external telemetry event into the engine input contract."""
        trace = ControlTraceBuilder(self.name, self.version)
        trace.add_step(
            "event_received",
            {
                "event": asdict(event),
                "binding_variable_id": self._binding.variable.variable_id,
            },
        )

        if event.variable_id != self._binding.variable.variable_id:
            raise ValueError(
                "Event variable_id does not match the control binding variable_id"
            )

        measurement = MeasurementState(
            value=event.value,
            observed_at=event.observed_at,
            quality=event.quality,
            source=event.source,
            metadata=event.metadata,
        )
        trace.add_step(
            "measurement_mapped",
            {
                "measurement": asdict(measurement),
            },
        )

        context: Dict[str, Any] = dict(self._binding.context)
        context.update(event.context)
        context["event_id"] = event.event_id
        context["event_kind"] = event.event_kind

        request = ControlEvaluationRequest(
            variable=self._binding.variable,
            measurement=measurement,
            setpoint=self._binding.setpoint,
            parameters=self._binding.parameters,
            context=context,
        )
        trace.add_step(
            "control_request_built",
            {
                "request": asdict(request),
            },
        )
        return request, trace.build()

    def evaluate_event(self, event: TelemetryStateEvent) -> EventDrivenRecommendation:
        """Evaluate one telemetry/state event and build a runtime-oriented envelope."""
        request, adapter_trace = self.to_evaluation_request(event)
        evaluation = self._evaluator.evaluate(request)

        runtime_payload = {
            "event_id": event.event_id,
            "variable_id": evaluation.variable_id,
            "recommendation_kind": evaluation.recommendation.kind.value,
            "action_label": evaluation.recommendation.action_label,
            "actuator_name": evaluation.recommendation.actuator_name,
            "command_value": evaluation.recommendation.command_value,
            "summary": evaluation.recommendation.summary,
            "setpoint_value": request.setpoint.value,
            "measurement_value": request.measurement.value,
            "error": evaluation.error,
            "trace_steps": [entry.step for entry in evaluation.trace],
            "binding_channel": self._binding.recommendation_channel,
        }

        return EventDrivenRecommendation(
            event_id=event.event_id,
            variable_id=evaluation.variable_id,
            recommendation_channel=self._binding.recommendation_channel,
            evaluation=evaluation,
            adapter_trace=adapter_trace,
            runtime_payload=runtime_payload,
        )
