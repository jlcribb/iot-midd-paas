"""PostgreSQL proof that replay persistence remains outside operational delivery."""

from __future__ import annotations

import json
import os
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from iot_middleware.services.simulation_replay_runner import SimulationReplayRunner
from iot_middleware.storage.db_handler import _get_control_settings_connection_url, _get_control_settings_engine
from iot_middleware.storage.simulation_run_repository import SimulationRunRepository


pytestmark = pytest.mark.skipif(os.getenv("RUN_SIMULATION_REPLAY_INTEGRATION") != "1", reason="requires local PostgreSQL")


@pytest.fixture
def stored_ready_session():
    engine = _get_control_settings_engine(_get_control_settings_connection_url())
    project_id, session_id = str(uuid.uuid4()), str(uuid.uuid4())
    records = [
        {"event_id": str(uuid.uuid4()), "project_id": project_id, "variable": "temperature", "value": 20,
         "timestamp": "2026-08-21T00:00:00+00:00", "context": {}, "metadata": {}, "quality": "raw", "source": "integration", "event_kind": "telemetry.observed"},
        {"event_id": str(uuid.uuid4()), "project_id": project_id, "variable": "temperature", "value": 10,
         "timestamp": "2026-08-21T00:01:00+00:00", "context": {}, "metadata": {}, "quality": "raw", "source": "integration", "event_kind": "telemetry.observed"},
    ]
    # UUID ordering may not follow generation ordering, so retain the M5.2 canonical rule.
    records.sort(key=lambda record: (record["timestamp"], record["event_id"]))
    policy = {"schema_version": 1, "policy": {"id": str(uuid.uuid4()), "project_id": project_id,
        "variable": "temperature", "context_selector": {}, "policy_type": "threshold", "priority": 1,
        "enabled": True, "version": 1, "source_asset_id": str(uuid.uuid4()),
        "params": {"setpoint_value": 20, "tolerance": 0.5, "increase_step": 2, "decrease_step": 2}}}
    topology = {"schema_version": 1, "source_asset": {"id": policy["policy"]["source_asset_id"], "asset_type": "sensor", "status": "online", "metadata": {}},
        "actuation_binding": None, "target_asset": None}
    dataset = {"schema_version": 1, "source_kind": "synthetic", "ordering": "timestamp_ascending_event_id", "records": records}
    configuration = {"schema_version": 1, "execution_context": "SIMULATION", "engine": {"name": "parametric-control-engine", "version": "0.1.0"},
        "clock": {"model_type": "SIMULATION_CLOCK", "model_version": "1", "initial_virtual_time": records[0]["timestamp"]},
        "operational_side_effects": {"outbox": False, "transport": False, "physical_effects": False}}
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO public.projects (id,name,status) VALUES (CAST(:id AS uuid),:name,'active')"), {"id": project_id, "name": f"m53-{project_id}"})
        connection.execute(text("""
            INSERT INTO public.control_simulation_sessions
              (id, project_id, execution_context, status, created_by, policy_snapshot, topology_snapshot,
               dataset_snapshot, configuration_snapshot, policy_snapshot_hash, topology_snapshot_hash,
               dataset_snapshot_hash, configuration_snapshot_hash, experiment_fingerprint, snapshot_schema_version, prepared_at)
            VALUES (CAST(:id AS uuid), CAST(:project_id AS uuid), 'SIMULATION', 'READY', 'integration',
                    CAST(:policy AS jsonb), CAST(:topology AS jsonb), CAST(:dataset AS jsonb), CAST(:configuration AS jsonb),
                    :policy_hash, :topology_hash, :dataset_hash, :configuration_hash, :fingerprint, 1, NOW())
        """), {"id": session_id, "project_id": project_id, "policy": json.dumps(policy), "topology": json.dumps(topology),
               "dataset": json.dumps(dataset), "configuration": json.dumps(configuration), "policy_hash": "a" * 64,
               "topology_hash": "b" * 64, "dataset_hash": "c" * 64, "configuration_hash": "d" * 64, "fingerprint": "e" * 64})
    try:
        yield engine, project_id, session_id
    finally:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM iot_schema.auditoria WHERE contexto->>'project_id'=:project_id AND entidad='control_simulation_runs'"), {"project_id": project_id})
            connection.execute(text("DELETE FROM public.control_simulation_results WHERE project_id=CAST(:project_id AS uuid)"), {"project_id": project_id})
            connection.execute(text("DELETE FROM public.control_simulation_run_events WHERE run_id IN (SELECT id FROM public.control_simulation_runs WHERE project_id=CAST(:project_id AS uuid))"), {"project_id": project_id})
            connection.execute(text("DELETE FROM public.control_simulation_runs WHERE project_id=CAST(:project_id AS uuid)"), {"project_id": project_id})
            connection.execute(text("DELETE FROM public.control_simulation_sessions WHERE id=CAST(:session_id AS uuid)"), {"session_id": session_id})
            connection.execute(text("DELETE FROM public.projects WHERE id=CAST(:project_id AS uuid)"), {"project_id": project_id})


def test_ready_session_runs_twice_with_isolated_outputs_and_no_operational_outbox(stored_ready_session):
    engine, project_id, session_id = stored_ready_session
    repository = SimulationRunRepository(engine)
    with engine.connect() as connection:
        before = connection.execute(text("SELECT count(*) FROM public.control_actuation_outbox WHERE project_id=CAST(:project_id AS uuid)"), {"project_id": project_id}).scalar_one()
    first = SimulationReplayRunner(repository).execute(project_id=project_id, session_id=session_id, created_by="integration")
    second = SimulationReplayRunner(repository).execute(project_id=project_id, session_id=session_id, created_by="integration")
    first_events, second_events = repository.events(first.id), repository.events(second.id)
    first_result, second_result = repository.get_result(project_id, session_id, first.id), repository.get_result(project_id, session_id, second.id)
    run_page, run_total = repository.list(project_id, session_id, limit=10, offset=0)
    assert first.status == second.status == "COMPLETED"
    assert first.id != second.id and first.output_count == second.output_count == 2
    assert run_total == 2 and {run.id for run, _ in run_page} == {first.id, second.id}
    assert {fingerprint for _, fingerprint in run_page} == {first_result.result_fingerprint}
    assert [event.output for event in first_events] == [event.output for event in second_events]
    assert first_result and second_result and first_result.result_fingerprint == second_result.result_fingerprint
    assert repository.materialize_result(project_id, session_id, first.id).id == first_result.id
    trace, total = repository.trace(project_id, session_id, first.id, limit=1, offset=1)
    assert total == 2 and trace[0]["sequence"] == 2 and trace[0]["recommendation_state"] == "RECOMMENDATION_ONLY"
    assert first_events[0].output["evaluation_outcome"] == "NO_RECOMMENDATION"
    assert first_events[1].output["recommendation_only"] is True
    with engine.connect() as connection:
        after = connection.execute(text("SELECT count(*) FROM public.control_actuation_outbox WHERE project_id=CAST(:project_id AS uuid)"), {"project_id": project_id}).scalar_one()
        status = connection.execute(text("SELECT status FROM public.control_simulation_sessions WHERE id=CAST(:session_id AS uuid)"), {"session_id": session_id}).scalar_one()
    assert before == after == 0
    assert status == "READY"
    with pytest.raises(DBAPIError, match="immutable"):
        with engine.begin() as connection:
            connection.execute(text("UPDATE public.control_simulation_results SET recommendation_count=99 WHERE id=CAST(:id AS uuid)"), {"id": first_result.id})
    assert repository.get_result(str(uuid.uuid4()), session_id, first.id) is None
    with pytest.raises(LookupError):
        repository.trace(str(uuid.uuid4()), session_id, first.id)
    failed = repository.create(project_id=project_id, session_id=session_id, created_by="integration", engine_version="0.1.0", replay_engine_version="1", clock_model_version="1")
    repository.fail(failed.id, code="TEST_FAILURE", detail="controlled")
    assert repository.get_result(project_id, session_id, failed.id) is None
    with pytest.raises(ValueError, match="COMPLETED"):
        repository.materialize_result(project_id, session_id, failed.id)
