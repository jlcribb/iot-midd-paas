"""Explicit execution boundaries for shared control semantics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol


class ExecutionContextKind(str, Enum):
    LIVE = "LIVE"
    SIMULATION = "SIMULATION"


class OperationalSideEffectForbidden(PermissionError):
    """Raised when a non-live context attempts an operational side effect."""


class Clock(Protocol):
    def now(self) -> datetime: ...


@dataclass(frozen=True)
class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


@dataclass(frozen=True)
class SimulationClock:
    """Immutable virtual clock used by deterministic simulation replay.

    ``advance_to`` deliberately returns a new instance.  Separate runs therefore
    cannot share mutable clock state, while callers can still model the virtual
    timestamp of each canonical input event.
    """

    current: datetime

    def now(self) -> datetime:
        return self.current

    def advance_to(self, current: datetime) -> "SimulationClock":
        if current.tzinfo is None:
            raise ValueError("SimulationClock requires timezone-aware virtual time")
        return SimulationClock(current.astimezone(timezone.utc))


@dataclass(frozen=True)
class SideEffectPolicy:
    physical_effects_allowed: bool
    operational_outbox_allowed: bool
    operational_transport_allowed: bool


@dataclass(frozen=True)
class ExecutionContext:
    kind: ExecutionContextKind
    clock: Clock
    persistence_namespace: str
    event_namespace: str
    correlation_namespace: str
    observability_namespace: str
    topology_source: str
    policy_source: str
    side_effects: SideEffectPolicy
    simulation_session_id: str | None = None

    def require_operational_outbox(self) -> None:
        if not self.side_effects.operational_outbox_allowed:
            raise OperationalSideEffectForbidden(f"{self.kind.value} cannot access the operational outbox")

    def require_operational_transport(self) -> None:
        if not self.side_effects.operational_transport_allowed:
            raise OperationalSideEffectForbidden(f"{self.kind.value} cannot access operational transport")

    def require_physical_effects(self) -> None:
        if not self.side_effects.physical_effects_allowed:
            raise OperationalSideEffectForbidden(f"{self.kind.value} cannot enable physical effects")


LIVE_EXECUTION_CONTEXT = ExecutionContext(
    kind=ExecutionContextKind.LIVE,
    clock=SystemClock(),
    persistence_namespace="operational",
    event_namespace="control",
    correlation_namespace="control",
    observability_namespace="control",
    topology_source="live",
    policy_source="active",
    side_effects=SideEffectPolicy(False, True, True),
)


def simulation_execution_context(*, session_id: str, clock: Clock | None = None) -> ExecutionContext:
    """Return a session-qualified context with no operational side effects."""
    if not session_id.strip():
        raise ValueError("simulation session_id is required")
    return ExecutionContext(
        kind=ExecutionContextKind.SIMULATION,
        clock=clock or SimulationClock(datetime.now(timezone.utc)),
        persistence_namespace=f"simulation:{session_id}",
        event_namespace="simulation",
        correlation_namespace=f"simulation:{session_id}",
        observability_namespace="simulation",
        topology_source="snapshot_slot",
        policy_source="snapshot_slot",
        side_effects=SideEffectPolicy(False, False, False),
        simulation_session_id=session_id,
    )
