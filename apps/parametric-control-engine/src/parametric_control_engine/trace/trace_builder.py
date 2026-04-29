"""Small helper to assemble evaluation traces in a consistent way."""

from __future__ import annotations

from typing import Any, Dict, List

from ..models.control_models import TraceEntry


class ControlTraceBuilder:
    """Collects trace entries without coupling evaluators to trace storage details."""

    def __init__(self, evaluator_name: str, evaluator_version: str) -> None:
        self._entries: List[TraceEntry] = [
            TraceEntry(
                step="trace_initialized",
                data={
                    "evaluator_name": evaluator_name,
                    "evaluator_version": evaluator_version,
                },
            )
        ]

    def add_step(self, step: str, data: Dict[str, Any]) -> None:
        self._entries.append(TraceEntry(step=step, data=data))

    def build(self) -> List[TraceEntry]:
        return list(self._entries)
