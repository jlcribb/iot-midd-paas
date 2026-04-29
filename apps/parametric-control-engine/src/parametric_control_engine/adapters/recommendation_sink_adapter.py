"""Adapters that render recommendation outputs for future runtime sinks."""

from __future__ import annotations

from dataclasses import asdict

from ..contracts.event_adapter_contracts import EventDrivenRecommendation
from ..contracts.sink_contracts import (
    PublishableRecommendationEnvelope,
    RecommendationAuditEnvelope,
    RecommendationSinkOutput,
)
from ..trace.trace_builder import ControlTraceBuilder


class RecommendationSinkAdapter:
    """Converts evaluated recommendations into publish/persist envelopes."""

    name = "recommendation-sink-adapter"
    version = "0.1.0"

    def build_publishable_envelope(
        self,
        recommendation: EventDrivenRecommendation,
    ) -> PublishableRecommendationEnvelope:
        """Build a runtime envelope suitable for a future broker or message bus."""
        return PublishableRecommendationEnvelope(
            envelope_id=f"publish::{recommendation.event_id}::{recommendation.variable_id}",
            channel=recommendation.recommendation_channel,
            message_type="control.recommendation",
            message_key=f"{recommendation.variable_id}:{recommendation.event_id}",
            payload={
                **recommendation.runtime_payload,
                "evaluator_name": recommendation.evaluation.evaluator_name,
                "evaluated_at": recommendation.evaluation.evaluated_at.isoformat(),
            },
        )

    def build_persistable_audit_envelope(
        self,
        recommendation: EventDrivenRecommendation,
    ) -> RecommendationAuditEnvelope:
        """Build an audit-friendly envelope for future persistence layers."""
        return RecommendationAuditEnvelope(
            audit_id=f"audit::{recommendation.event_id}::{recommendation.variable_id}",
            record_type="control.recommendation.audit",
            partition_key=recommendation.variable_id,
            payload={
                "event_id": recommendation.event_id,
                "variable_id": recommendation.variable_id,
                "recommendation_channel": recommendation.recommendation_channel,
                "evaluation": asdict(recommendation.evaluation),
                "adapter_trace": [asdict(entry) for entry in recommendation.adapter_trace],
                "runtime_payload": recommendation.runtime_payload,
            },
        )

    def build_sink_output(
        self,
        recommendation: EventDrivenRecommendation,
    ) -> RecommendationSinkOutput:
        """Build both publish and persistence envelopes with sink traceability."""
        trace = ControlTraceBuilder(self.name, self.version)
        trace.add_step(
            "recommendation_received",
            {
                "event_id": recommendation.event_id,
                "variable_id": recommendation.variable_id,
                "recommendation_channel": recommendation.recommendation_channel,
            },
        )

        publish_envelope = self.build_publishable_envelope(recommendation)
        trace.add_step(
            "publishable_envelope_built",
            {
                "envelope_id": publish_envelope.envelope_id,
                "channel": publish_envelope.channel,
                "message_type": publish_envelope.message_type,
            },
        )

        audit_envelope = self.build_persistable_audit_envelope(recommendation)
        trace.add_step(
            "audit_envelope_built",
            {
                "audit_id": audit_envelope.audit_id,
                "record_type": audit_envelope.record_type,
                "partition_key": audit_envelope.partition_key,
            },
        )

        return RecommendationSinkOutput(
            event_id=recommendation.event_id,
            variable_id=recommendation.variable_id,
            publish_envelope=publish_envelope,
            audit_envelope=audit_envelope,
            sink_trace=trace.build(),
        )
