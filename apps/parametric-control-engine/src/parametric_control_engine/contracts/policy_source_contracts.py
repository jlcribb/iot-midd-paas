"""Contracts for abstract policy sources in the MVP."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Protocol, runtime_checkable

from ..models.control_models import TraceEntry
from .policy_contracts import StaticPolicyDefinition


@dataclass(frozen=True)
class PolicySourceRequest:
    """Minimal request sent to a policy source."""

    variable_id: str
    context: Dict[str, object] = field(default_factory=dict)
    event_id: str = ""


@dataclass(frozen=True)
class PolicySourceResult:
    """Candidate policies returned by a policy source."""

    source_name: str
    policies: List[StaticPolicyDefinition]
    source_trace: List[TraceEntry]


@runtime_checkable
class PolicySource(Protocol):
    """Abstract provider of candidate policies for the selector."""

    source_name: str

    def load_policies(self, request: PolicySourceRequest) -> PolicySourceResult:
        """Load candidate policies for the incoming request."""
