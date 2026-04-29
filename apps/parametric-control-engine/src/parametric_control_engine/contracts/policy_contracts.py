"""Contracts for static policy selection in the MVP."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..models.control_models import TraceEntry
from .event_adapter_contracts import MonovariableControlBinding


@dataclass(frozen=True)
class PolicySelectionRequest:
    """Minimal request for resolving a control binding."""

    variable_id: str
    context: Dict[str, Any] = field(default_factory=dict)
    event_id: str = ""


@dataclass(frozen=True)
class StaticPolicyDefinition:
    """Static policy binding with optional context filters."""

    policy_id: str
    binding: MonovariableControlBinding
    required_context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    version: int = 1
    policy_type: str = "proportional"
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass(frozen=True)
class PolicySelectionResult:
    """Selected policy and trace data for auditability."""

    policy_id: str
    binding: MonovariableControlBinding
    selector_name: str
    selection_trace: List[TraceEntry]
    priority: int = 0
    version: int = 1
    policy_type: str = "proportional"
