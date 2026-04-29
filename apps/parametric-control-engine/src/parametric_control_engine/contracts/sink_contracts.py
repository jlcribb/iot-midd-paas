"""Contracts for publishable and persistable recommendation outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from ..models.control_models import TraceEntry


@dataclass(frozen=True)
class PublishableRecommendationEnvelope:
    """Broker-friendly recommendation envelope without broker coupling."""

    envelope_id: str
    channel: str
    message_type: str
    message_key: str
    payload: Dict[str, Any]


@dataclass(frozen=True)
class RecommendationAuditEnvelope:
    """Persistence-friendly audit envelope without storage coupling."""

    audit_id: str
    record_type: str
    partition_key: str
    payload: Dict[str, Any]


@dataclass(frozen=True)
class RecommendationSinkOutput:
    """Final output of the sink adapter for runtime integration."""

    event_id: str
    variable_id: str
    publish_envelope: PublishableRecommendationEnvelope
    audit_envelope: RecommendationAuditEnvelope
    sink_trace: List[TraceEntry]
