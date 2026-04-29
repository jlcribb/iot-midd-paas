"""Static policy selector for monovariable control bindings."""

from __future__ import annotations

from dataclasses import asdict
from typing import List

from ..contracts.event_adapter_contracts import TelemetryStateEvent
from ..contracts.policy_contracts import (
    PolicySelectionRequest,
    PolicySelectionResult,
)
from ..contracts.policy_source_contracts import PolicySource, PolicySourceRequest
from ..trace.trace_builder import ControlTraceBuilder


class StaticPolicySelector:
    """Resolves a binding using variable_id plus optional exact context filters."""

    name = "static-policy-selector"
    version = "0.1.0"

    def __init__(self, policy_source: PolicySource) -> None:
        self._policy_source = policy_source

    def resolve(self, request: PolicySelectionRequest) -> PolicySelectionResult:
        """Select the most specific static policy for the incoming request."""
        trace = ControlTraceBuilder(self.name, self.version)
        source_result = self._policy_source.load_policies(
            PolicySourceRequest(
                variable_id=request.variable_id,
                context=request.context,
                event_id=request.event_id,
            )
        )
        trace.add_step(
            "selection_request_received",
            {
                "request": asdict(request),
                "policy_source_name": source_result.source_name,
                "candidate_count": len(source_result.policies),
                "policy_source_trace_steps": [
                    entry.step for entry in source_result.source_trace
                ],
            },
        )

        matching_candidates = []
        for policy in source_result.policies:
            if policy.binding.variable.variable_id != request.variable_id:
                continue
            if not self._matches_context(policy.required_context, request.context):
                continue
            matching_candidates.append(policy)

        trace.add_step(
            "candidates_filtered",
            {
                "matching_policy_ids": [policy.policy_id for policy in matching_candidates],
            },
        )

        if not matching_candidates:
            raise ValueError(
                f"No static policy found for variable_id={request.variable_id!r}"
            )

        selected = max(
            matching_candidates,
            key=lambda policy: (
                len(policy.required_context),
                policy.priority,
                policy.version,
            ),
        )
        trace.add_step(
            "policy_selected",
            {
                "policy_id": selected.policy_id,
                "required_context": selected.required_context,
                "priority": selected.priority,
                "version": selected.version,
                "policy_type": selected.policy_type,
                "binding_channel": selected.binding.recommendation_channel,
            },
        )

        return PolicySelectionResult(
            policy_id=selected.policy_id,
            binding=selected.binding,
            selector_name=self.name,
            priority=selected.priority,
            version=selected.version,
            policy_type=selected.policy_type,
            selection_trace=trace.build(),
        )

    def resolve_event(self, event: TelemetryStateEvent) -> PolicySelectionResult:
        """Resolve a static policy directly from a telemetry/state event."""
        return self.resolve(
            PolicySelectionRequest(
                variable_id=event.variable_id,
                context=event.context,
                event_id=event.event_id,
            )
        )

    @staticmethod
    def _matches_context(required_context: dict, actual_context: dict) -> bool:
        return all(actual_context.get(key) == value for key, value in required_context.items())
