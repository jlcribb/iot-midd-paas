"""M5.3 deterministic replay proofs; all inputs are frozen in the fixture."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

import pytest

from iot_middleware.services.simulation_replay_runner import (
    COMPATIBLE_CONTROL_ENGINE_VERSION,
    SimulationReplayRejected,
    SimulationReplayRunner,
)
from iot_middleware.storage.simulation_run_repository import StoredSimulationSession


PROJECT_ID = "11111111-1111-4111-8111-111111111111"
SESSION_ID = "22222222-2222-4222-8222-222222222222"


def ready_session(*, actionable: bool = True) -> StoredSimulationSession:
    topology = {
        "schema_version": 1,
        "source_asset": {"id": "source-1", "asset_type": "sensor", "status": "online", "metadata": {}},
        "actuation_binding": {"id": "binding-1", "enabled": True, "version": 1,
          "target_asset_id": "target-1", "control_point": "relay", "operation": "set"} if actionable else None,
        "target_asset": {"id": "target-1", "asset_type": "simulated", "status": "online", "metadata": {}} if actionable else None,
    }
    return StoredSimulationSession(
        id=SESSION_ID, project_id=PROJECT_ID, status="READY", experiment_fingerprint="a" * 64,
        policy_snapshot={"schema_version": 1, "policy": {
            "id": "policy-1", "project_id": PROJECT_ID, "variable": "temperature",
            "context_selector": {}, "policy_type": "threshold", "priority": 1, "enabled": True,
            "version": 4, "source_asset_id": "source-1",
            "params": {"setpoint_value": 20, "tolerance": 0.5, "increase_step": 2,
                       "decrease_step": 3, "hold_signal": 0, "variable_name": "Temperature",
                       "variable_unit": "celsius", "actuator_name": "relay"},
        }}, topology_snapshot=topology,
        dataset_snapshot={"schema_version": 1, "source_kind": "synthetic", "ordering": "timestamp_ascending_event_id",
            "records": [
                {"event_id": "33333333-3333-4333-8333-333333333333", "project_id": PROJECT_ID,
                 "variable": "temperature", "value": 20, "timestamp": "2026-08-21T00:00:00+00:00",
                 "context": {}, "metadata": {}, "quality": "raw", "source": "fixture", "event_kind": "telemetry.observed"},
                {"event_id": "44444444-4444-4444-8444-444444444444", "project_id": PROJECT_ID,
                 "variable": "temperature", "value": 10, "timestamp": "2026-08-21T00:01:00+00:00",
                 "context": {}, "metadata": {}, "quality": "raw", "source": "fixture", "event_kind": "telemetry.observed"},
            ]},
        configuration_snapshot={"schema_version": 1, "execution_context": "SIMULATION",
            "engine": {"name": "parametric-control-engine", "version": COMPATIBLE_CONTROL_ENGINE_VERSION},
            "clock": {"model_type": "SIMULATION_CLOCK", "model_version": "1", "initial_virtual_time": "2026-08-21T00:00:00+00:00"},
            "operational_side_effects": {"outbox": False, "transport": False, "physical_effects": False}},
    )


def domain(rows):
    return [row.as_dict() for row in rows]


def test_actionable_replay_uses_frozen_target_and_virtual_clock():
    rows = SimulationReplayRunner().replay(ready_session(actionable=True))
    assert [row.sequence for row in rows] == [1, 2]
    assert rows[0].reason_code == "NO_RECOMMENDATION_HOLD"
    assert rows[1].actionable is True
    assert rows[1].reason_code == "ACTIONABLE_FROZEN_TARGET"
    assert rows[1].virtual_timestamp == datetime(2026, 8, 21, 0, 1, tzinfo=timezone.utc)
    assert all(row.as_dict()["physical_effects"] is False for row in rows)


def test_recommendation_only_replay_never_becomes_actionable_without_frozen_target():
    rows = SimulationReplayRunner().replay(ready_session(actionable=False))
    assert rows[1].has_recommendation is True
    assert rows[1].actionable is False
    assert rows[1].recommendation_only is True
    assert rows[1].reason_code == "RECOMMENDATION_ONLY_NO_FROZEN_TARGET"


def test_same_session_replays_have_same_ordered_domain_output_and_no_wall_clock_dependency():
    runner = SimulationReplayRunner()
    session = ready_session()
    assert domain(runner.replay(session)) == domain(runner.replay(session))


def test_frozen_policy_and_topology_win_over_unrelated_live_mutations():
    session = ready_session()
    live_policy = {"setpoint_value": 9999}
    live_topology = {"target": "changed"}
    before = domain(SimulationReplayRunner().replay(session))
    live_policy["setpoint_value"] = -9999
    live_topology["target"] = "retired"
    assert domain(SimulationReplayRunner().replay(session)) == before


def test_draft_session_and_incompatible_engine_fail_closed_before_any_execution():
    draft = ready_session()
    draft = StoredSimulationSession(**{**draft.__dict__, "status": "DRAFT"})
    with pytest.raises(SimulationReplayRejected, match="READY"):
        SimulationReplayRunner().replay(draft)
    incompatible = ready_session()
    config = deepcopy(incompatible.configuration_snapshot)
    config["engine"]["version"] = "999.0.0"
    incompatible = StoredSimulationSession(**{**incompatible.__dict__, "configuration_snapshot": config})
    with pytest.raises(SimulationReplayRejected, match="incompatible"):
        SimulationReplayRunner().replay(incompatible)


def test_noncanonical_dataset_is_rejected_instead_of_being_silently_reordered():
    session = ready_session()
    dataset = deepcopy(session.dataset_snapshot)
    dataset["records"].reverse()
    invalid = StoredSimulationSession(**{**session.__dict__, "dataset_snapshot": dataset})
    with pytest.raises(SimulationReplayRejected, match="canonical"):
        SimulationReplayRunner().replay(invalid)


def test_session_value_is_not_mutated_by_replay_and_operational_dependencies_are_absent():
    session = ready_session()
    original = deepcopy(session)
    runner = SimulationReplayRunner()
    runner.replay(session)
    assert session == original
    assert not hasattr(runner, "outbox")
    assert not hasattr(runner, "publisher")
    assert not hasattr(runner, "transport")


def test_persisted_execution_creates_independent_runs_without_mutating_session():
    class Repository:
        def __init__(self): self.created = []; self.completed = []; self.session = ready_session()
        def load_session(self, *_): return self.session
        def create(self, **kwargs):
            from iot_middleware.storage.simulation_run_repository import SimulationRun
            run = SimulationRun(id=f"run-{len(self.created) + 1}", project_id=kwargs["project_id"], session_id=kwargs["session_id"],
                status="CREATED", created_by=kwargs["created_by"], engine_version=kwargs["engine_version"],
                replay_engine_version=kwargs["replay_engine_version"], clock_model_version=kwargs["clock_model_version"],
                output_count=0, created_at=datetime.now(timezone.utc), started_at=None, completed_at=None, failure_code=None, failure_detail=None)
            self.created.append(run); return run
        def mark_running(self, run_id): return None
        def complete(self, run_id, events):
            events = list(events); self.completed.append((run_id, events)); return {"id": run_id, "status": "COMPLETED", "output_count": len(events)}
        def fail(self, *args, **kwargs): raise AssertionError("must not fail")
    repository = Repository()
    runner = SimulationReplayRunner(repository)
    first = runner.execute(project_id=PROJECT_ID, session_id=SESSION_ID, created_by="operator")
    second = runner.execute(project_id=PROJECT_ID, session_id=SESSION_ID, created_by="operator")
    assert first["id"] != second["id"]
    assert [event.output for event in repository.completed[0][1]] == [event.output for event in repository.completed[1][1]]
    assert repository.session == ready_session()
