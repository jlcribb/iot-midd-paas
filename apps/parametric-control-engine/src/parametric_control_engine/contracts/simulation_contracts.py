"""Domain contracts for the M5 simulation-session foundation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..execution_context import ExecutionContextKind


class SimulationSessionStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class SimulationSession:
    id: str
    project_id: str
    created_by: str
    status: SimulationSessionStatus
    created_at: datetime
    execution_context: ExecutionContextKind = ExecutionContextKind.SIMULATION
    started_at: datetime | None = None
    completed_at: datetime | None = None
    snapshot_refs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.execution_context is not ExecutionContextKind.SIMULATION:
            raise ValueError("SimulationSession must use SIMULATION execution context")
