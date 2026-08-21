"""Persistence boundary for deterministic, simulation-only replay runs.

The repository intentionally has no dependency on delivery intents, the
operational outbox, publishers, or transports.  A run refers to a READY session
and stores only its own ordered domain output.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

from sqlalchemy import text

from iot_middleware.storage.db_handler import (
    _get_control_settings_connection_url,
    _get_control_settings_engine,
)
from iot_middleware.services.simulation_result_model import SimulationResultEvidence, canonical_result_evidence


@dataclass(frozen=True)
class StoredSimulationSession:
    id: str
    project_id: str
    status: str
    experiment_fingerprint: str | None
    policy_snapshot: dict[str, Any] | None
    topology_snapshot: dict[str, Any] | None
    dataset_snapshot: dict[str, Any] | None
    configuration_snapshot: dict[str, Any] | None


@dataclass(frozen=True)
class SimulationRun:
    id: str
    project_id: str
    session_id: str
    status: str
    created_by: str
    engine_version: str
    replay_engine_version: str
    clock_model_version: str
    output_count: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    failure_code: str | None
    failure_detail: str | None


@dataclass(frozen=True)
class SimulationRunEvent:
    run_id: str
    sequence: int
    event_id: str
    virtual_timestamp: datetime
    output: dict[str, Any]


@dataclass(frozen=True)
class SimulationResult:
    id: str
    project_id: str
    session_id: str
    run_id: str
    experiment_fingerprint: str
    result_fingerprint: str
    processed_events: int
    evaluation_count: int
    recommendation_count: int
    actionable_recommendation_count: int
    recommendation_only_count: int
    failed_domain_event_count: int
    first_virtual_timestamp: datetime | None
    last_virtual_timestamp: datetime | None
    canonical_result_schema_version: int
    created_at: datetime


def _as_dict(value: Any) -> dict[str, Any] | None:
    return dict(value) if isinstance(value, dict) else None


def _map_session(row: Any) -> StoredSimulationSession:
    return StoredSimulationSession(
        id=str(row["id"]), project_id=str(row["project_id"]), status=str(row["status"]),
        experiment_fingerprint=row["experiment_fingerprint"],
        policy_snapshot=_as_dict(row["policy_snapshot"]),
        topology_snapshot=_as_dict(row["topology_snapshot"]),
        dataset_snapshot=_as_dict(row["dataset_snapshot"]),
        configuration_snapshot=_as_dict(row["configuration_snapshot"]),
    )


def _map_run(row: Any) -> SimulationRun:
    return SimulationRun(
        id=str(row["id"]), project_id=str(row["project_id"]), session_id=str(row["session_id"]),
        status=str(row["status"]), created_by=str(row["created_by"]),
        engine_version=str(row["engine_version"]), replay_engine_version=str(row["replay_engine_version"]),
        clock_model_version=str(row["clock_model_version"]), output_count=int(row["output_count"]),
        created_at=row["created_at"], started_at=row["started_at"], completed_at=row["completed_at"],
        failure_code=row["failure_code"], failure_detail=row["failure_detail"],
    )


def _map_result(row: Any) -> SimulationResult:
    return SimulationResult(
        id=str(row["id"]), project_id=str(row["project_id"]), session_id=str(row["session_id"]), run_id=str(row["run_id"]),
        experiment_fingerprint=str(row["experiment_fingerprint"]), result_fingerprint=str(row["result_fingerprint"]),
        processed_events=int(row["processed_events"]), evaluation_count=int(row["evaluation_count"]),
        recommendation_count=int(row["recommendation_count"]), actionable_recommendation_count=int(row["actionable_recommendation_count"]),
        recommendation_only_count=int(row["recommendation_only_count"]), failed_domain_event_count=int(row["failed_domain_event_count"]),
        first_virtual_timestamp=row["first_virtual_timestamp"], last_virtual_timestamp=row["last_virtual_timestamp"],
        canonical_result_schema_version=int(row["canonical_result_schema_version"]), created_at=row["created_at"],
    )


class SimulationRunRepository:
    """PostgreSQL repository for simulation runs and their ordered outputs."""

    def __init__(self, engine=None) -> None:
        self._engine = engine or _get_control_settings_engine(_get_control_settings_connection_url())

    def load_session(self, project_id: str, session_id: str) -> StoredSimulationSession | None:
        with self._engine.connect() as connection:
            row = connection.execute(text("""
                SELECT id, project_id, status, experiment_fingerprint, policy_snapshot,
                       topology_snapshot, dataset_snapshot, configuration_snapshot
                FROM public.control_simulation_sessions
                WHERE project_id=CAST(:project_id AS uuid) AND id=CAST(:session_id AS uuid)
            """), {"project_id": project_id, "session_id": session_id}).mappings().first()
        return _map_session(row) if row else None

    def create(self, *, project_id: str, session_id: str, created_by: str,
               engine_version: str, replay_engine_version: str,
               clock_model_version: str) -> SimulationRun:
        run_id = str(uuid.uuid4())
        with self._engine.begin() as connection:
            row = connection.execute(text("""
                INSERT INTO public.control_simulation_runs
                  (id, project_id, session_id, status, created_by, engine_version,
                   replay_engine_version, clock_model_version, physical_effects_allowed)
                VALUES (CAST(:id AS uuid), CAST(:project_id AS uuid), CAST(:session_id AS uuid),
                        'CREATED', :created_by, :engine_version, :replay_engine_version,
                        :clock_model_version, FALSE)
                RETURNING *
            """), {"id": run_id, "project_id": project_id, "session_id": session_id,
                   "created_by": created_by, "engine_version": engine_version,
                   "replay_engine_version": replay_engine_version,
                   "clock_model_version": clock_model_version}).mappings().one()
        return _map_run(row)

    def mark_running(self, run_id: str) -> SimulationRun:
        return self._transition(run_id, "RUNNING")

    def complete(self, run_id: str, events: Iterable[SimulationRunEvent]) -> SimulationRun:
        materialized = list(events)
        with self._engine.begin() as connection:
            for event in materialized:
                connection.execute(text("""
                    INSERT INTO public.control_simulation_run_events
                      (run_id, sequence, event_id, virtual_timestamp, output)
                    VALUES (CAST(:run_id AS uuid), :sequence, CAST(:event_id AS uuid),
                            :virtual_timestamp, CAST(:output AS jsonb))
                """), {"run_id": run_id, "sequence": event.sequence, "event_id": event.event_id,
                       "virtual_timestamp": event.virtual_timestamp,
                       "output": json.dumps(event.output, sort_keys=True)})
            completed = connection.execute(text("""
                UPDATE public.control_simulation_runs
                SET status='COMPLETED', completed_at=NOW(), output_count=:output_count
                WHERE id=CAST(:run_id AS uuid) AND status='RUNNING'
                RETURNING *
            """), {"run_id": run_id, "output_count": len(materialized)}).mappings().one()
            row = connection.execute(text("""
                SELECT r.*, s.experiment_fingerprint FROM public.control_simulation_runs r
                JOIN public.control_simulation_sessions s ON s.id=r.session_id AND s.project_id=r.project_id
                WHERE r.id=CAST(:run_id AS uuid)
            """), {"run_id": str(completed["id"])}).mappings().one()
            self._materialize_result_in_transaction(connection, row, materialized)
            self._audit(connection, row, "SIMULATION_RUN_COMPLETED", {"output_count": len(materialized)})
        return _map_run(row)

    def fail(self, run_id: str, *, code: str, detail: str) -> SimulationRun:
        with self._engine.begin() as connection:
            row = connection.execute(text("""
                UPDATE public.control_simulation_runs
                SET status='FAILED', started_at=COALESCE(started_at, NOW()), completed_at=NOW(), failure_code=:code, failure_detail=:detail
                WHERE id=CAST(:run_id AS uuid) AND status IN ('CREATED', 'RUNNING')
                RETURNING *
            """), {"run_id": run_id, "code": code, "detail": detail[:500]}).mappings().one()
            self._audit(connection, row, "SIMULATION_RUN_FAILED", {"failure_code": code})
        return _map_run(row)

    def get(self, project_id: str, session_id: str, run_id: str) -> SimulationRun | None:
        with self._engine.connect() as connection:
            row = connection.execute(text("""
                SELECT * FROM public.control_simulation_runs
                WHERE id=CAST(:run_id AS uuid) AND project_id=CAST(:project_id AS uuid)
                  AND session_id=CAST(:session_id AS uuid)
            """), {"run_id": run_id, "project_id": project_id, "session_id": session_id}).mappings().first()
        return _map_run(row) if row else None

    def events(self, run_id: str) -> list[SimulationRunEvent]:
        with self._engine.connect() as connection:
            rows = connection.execute(text("""
                SELECT run_id, sequence, event_id, virtual_timestamp, output
                FROM public.control_simulation_run_events
                WHERE run_id=CAST(:run_id AS uuid) ORDER BY sequence
            """), {"run_id": run_id}).mappings().all()
        return [SimulationRunEvent(run_id=str(row["run_id"]), sequence=int(row["sequence"]),
                                   event_id=str(row["event_id"]), virtual_timestamp=row["virtual_timestamp"],
                                   output=dict(row["output"])) for row in rows]

    def get_result(self, project_id: str, session_id: str, run_id: str) -> SimulationResult | None:
        with self._engine.connect() as connection:
            row = connection.execute(text("""
                SELECT * FROM public.control_simulation_results
                WHERE project_id=CAST(:project_id AS uuid) AND session_id=CAST(:session_id AS uuid)
                  AND run_id=CAST(:run_id AS uuid)
            """), {"project_id": project_id, "session_id": session_id, "run_id": run_id}).mappings().first()
        return _map_result(row) if row else None

    def materialize_result(self, project_id: str, session_id: str, run_id: str) -> SimulationResult:
        """Idempotently materialize a result for an already completed run only."""
        with self._engine.begin() as connection:
            run = connection.execute(text("""
                SELECT r.*, s.experiment_fingerprint FROM public.control_simulation_runs r
                JOIN public.control_simulation_sessions s ON s.id=r.session_id AND s.project_id=r.project_id
                WHERE r.id=CAST(:run_id AS uuid) AND r.project_id=CAST(:project_id AS uuid)
                  AND r.session_id=CAST(:session_id AS uuid) FOR UPDATE
            """), {"run_id": run_id, "project_id": project_id, "session_id": session_id}).mappings().first()
            if run is None:
                raise LookupError("simulation run not found in project scope")
            if run["status"] != "COMPLETED":
                raise ValueError("only COMPLETED simulation runs may produce a result")
            events = self._events_in_transaction(connection, run_id)
            return self._materialize_result_in_transaction(connection, run, events)

    def trace(self, project_id: str, session_id: str, run_id: str, *, limit: int = 100, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
        if limit < 1 or limit > 500 or offset < 0:
            raise ValueError("trace pagination must use 1..500 limit and non-negative offset")
        with self._engine.connect() as connection:
            exists = connection.execute(text("""
                SELECT 1 FROM public.control_simulation_runs
                WHERE id=CAST(:run_id AS uuid) AND project_id=CAST(:project_id AS uuid) AND session_id=CAST(:session_id AS uuid)
            """), {"run_id": run_id, "project_id": project_id, "session_id": session_id}).first()
            if not exists:
                raise LookupError("simulation run not found in project scope")
            total = connection.execute(text("SELECT count(*) FROM public.control_simulation_run_events WHERE run_id=CAST(:run_id AS uuid)"), {"run_id": run_id}).scalar_one()
            rows = connection.execute(text("""
                SELECT sequence, event_id, virtual_timestamp, output FROM public.control_simulation_run_events
                WHERE run_id=CAST(:run_id AS uuid) ORDER BY sequence LIMIT :limit OFFSET :offset
            """), {"run_id": run_id, "limit": limit, "offset": offset}).mappings().all()
        return [self._trace_item(row) for row in rows], int(total)

    def _transition(self, run_id: str, status: str) -> SimulationRun:
        with self._engine.begin() as connection:
            row = connection.execute(text("""
                UPDATE public.control_simulation_runs
                SET status=:status, started_at=CASE WHEN :status='RUNNING' THEN NOW() ELSE started_at END
                WHERE id=CAST(:run_id AS uuid) AND status='CREATED'
                RETURNING *
            """), {"run_id": run_id, "status": status}).mappings().one()
            self._audit(connection, row, "SIMULATION_RUN_STARTED", {})
        return _map_run(row)

    def _materialize_result_in_transaction(self, connection, run: Any, events: Iterable[SimulationRunEvent]) -> SimulationResult:
        existing = connection.execute(text("SELECT * FROM public.control_simulation_results WHERE run_id=CAST(:run_id AS uuid)"), {"run_id": str(run["id"])}).mappings().first()
        if existing is not None:
            return _map_result(existing)
        evidence = canonical_result_evidence(experiment_fingerprint=str(run["experiment_fingerprint"]), outputs=[event.output for event in events])
        result_id = str(uuid.uuid4())
        row = connection.execute(text("""
            INSERT INTO public.control_simulation_results
              (id,project_id,session_id,run_id,experiment_fingerprint,result_fingerprint,processed_events,evaluation_count,
               recommendation_count,actionable_recommendation_count,recommendation_only_count,failed_domain_event_count,
               first_virtual_timestamp,last_virtual_timestamp,canonical_result_schema_version)
            VALUES (CAST(:id AS uuid),CAST(:project_id AS uuid),CAST(:session_id AS uuid),CAST(:run_id AS uuid),
                    :experiment_fingerprint,:result_fingerprint,:processed_events,:evaluation_count,:recommendation_count,
                    :actionable_recommendation_count,:recommendation_only_count,:failed_domain_event_count,
                    :first_virtual_timestamp,:last_virtual_timestamp,:canonical_result_schema_version)
            ON CONFLICT (run_id) DO NOTHING RETURNING *
        """), {"id": result_id, "project_id": str(run["project_id"]), "session_id": str(run["session_id"]), "run_id": str(run["id"]),
               "experiment_fingerprint": evidence.experiment_fingerprint, "result_fingerprint": evidence.result_fingerprint,
               "processed_events": evidence.processed_events, "evaluation_count": evidence.evaluation_count,
               "recommendation_count": evidence.recommendation_count, "actionable_recommendation_count": evidence.actionable_recommendation_count,
               "recommendation_only_count": evidence.recommendation_only_count, "failed_domain_event_count": evidence.failed_domain_event_count,
               "first_virtual_timestamp": evidence.first_virtual_timestamp, "last_virtual_timestamp": evidence.last_virtual_timestamp,
               "canonical_result_schema_version": evidence.canonical_result_schema_version}).mappings().first()
        if row is None:
            row = connection.execute(text("SELECT * FROM public.control_simulation_results WHERE run_id=CAST(:run_id AS uuid)"), {"run_id": str(run["id"])}).mappings().one()
        self._audit(connection, run, "SIMULATION_RESULT_MATERIALIZED", {"result_fingerprint": evidence.result_fingerprint})
        return _map_result(row)

    def _events_in_transaction(self, connection, run_id: str) -> list[SimulationRunEvent]:
        rows = connection.execute(text("""
            SELECT run_id, sequence, event_id, virtual_timestamp, output FROM public.control_simulation_run_events
            WHERE run_id=CAST(:run_id AS uuid) ORDER BY sequence
        """), {"run_id": run_id}).mappings().all()
        return [SimulationRunEvent(run_id=str(row["run_id"]), sequence=int(row["sequence"]), event_id=str(row["event_id"]),
                                   virtual_timestamp=row["virtual_timestamp"], output=dict(row["output"])) for row in rows]

    @staticmethod
    def _trace_item(row: Any) -> dict[str, Any]:
        output = dict(row["output"])
        return {
            "sequence": int(row["sequence"]), "source_event_id": str(row["event_id"]),
            "virtual_timestamp": row["virtual_timestamp"].isoformat(), "evaluation_outcome": output["evaluation_outcome"],
            "recommendation_state": "RECOMMENDATION_ONLY" if output["recommendation_only"] else "RECOMMENDATION" if output["has_recommendation"] else "NO_RECOMMENDATION",
            "actionable": bool(output["actionable"]), "reason_code": output["reason_code"],
        }

    @staticmethod
    def _audit(connection, row: Any, action: str, summary: dict[str, Any]) -> None:
        """Persist compact, simulation-scoped audit evidence without dataset payloads."""
        connection.execute(text("""
            INSERT INTO iot_schema.auditoria (entidad, entidad_id, accion, cambios, contexto)
            VALUES ('control_simulation_runs', CAST(:run_id AS uuid), :action,
                    CAST(:changes AS jsonb), CAST(:context AS jsonb))
        """), {
            "run_id": str(row["id"]), "action": action,
            "changes": json.dumps({"status": str(row["status"]), **summary}, sort_keys=True),
            "context": json.dumps({"subsystem": "simulation-replay", "execution_context": "SIMULATION",
                "project_id": str(row["project_id"]), "session_id": str(row["session_id"]),
                "replay_engine_version": str(row["replay_engine_version"]), "physical_effects": False}, sort_keys=True),
        })
