from datetime import datetime, timezone

import pytest

from parametric_control_engine.contracts.simulation_contracts import SimulationSession, SimulationSessionStatus
from parametric_control_engine.execution_context import (
    ExecutionContextKind,
    OperationalSideEffectForbidden,
    SimulationClock,
    simulation_execution_context,
)


def test_simulation_context_is_explicit_and_session_scoped():
    clock = SimulationClock(datetime(2026, 8, 21, tzinfo=timezone.utc))
    context = simulation_execution_context(session_id="session-1", clock=clock)

    assert context.kind is ExecutionContextKind.SIMULATION
    assert context.persistence_namespace == "simulation:session-1"
    assert context.correlation_namespace == "simulation:session-1"
    assert context.clock.now() == clock.current
    assert context.side_effects.physical_effects_allowed is False


def test_simulation_context_fails_closed_for_every_operational_side_effect():
    context = simulation_execution_context(session_id="session-1")

    with pytest.raises(OperationalSideEffectForbidden):
        context.require_operational_outbox()
    with pytest.raises(OperationalSideEffectForbidden):
        context.require_operational_transport()
    with pytest.raises(OperationalSideEffectForbidden):
        context.require_physical_effects()


def test_simulation_session_cannot_be_constructed_as_live():
    with pytest.raises(ValueError, match="SIMULATION"):
        SimulationSession(
            id="session-1", project_id="project-1", created_by="actor-1",
            status=SimulationSessionStatus.DRAFT, created_at=datetime.now(timezone.utc),
            execution_context=ExecutionContextKind.LIVE,
        )
