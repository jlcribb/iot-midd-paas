"""In-memory policy source used by the MVP and local demos."""

from __future__ import annotations

from dataclasses import asdict
from typing import Iterable, List

from ..contracts.policy_contracts import StaticPolicyDefinition
from ..contracts.policy_source_contracts import PolicySourceRequest, PolicySourceResult
from ..trace.trace_builder import ControlTraceBuilder


class InMemoryPolicySource:
    """Returns static policy definitions from an in-memory collection."""

    source_name = "in-memory-policy-source"
    version = "0.1.0"

    def __init__(self, policies: Iterable[StaticPolicyDefinition]) -> None:
        self._policies: List[StaticPolicyDefinition] = list(policies)

    def load_policies(self, request: PolicySourceRequest) -> PolicySourceResult:
        """Return candidate policies for the requested variable_id."""
        trace = ControlTraceBuilder(self.source_name, self.version)
        trace.add_step(
            "policy_source_request_received",
            {
                "request": asdict(request),
                "available_policy_count": len(self._policies),
            },
        )

        candidates = [
            policy
            for policy in self._policies
            if policy.binding.variable.variable_id == request.variable_id
        ]
        trace.add_step(
            "policy_candidates_loaded",
            {
                "candidate_policy_ids": [policy.policy_id for policy in candidates],
            },
        )

        return PolicySourceResult(
            source_name=self.source_name,
            policies=candidates,
            source_trace=trace.build(),
        )
