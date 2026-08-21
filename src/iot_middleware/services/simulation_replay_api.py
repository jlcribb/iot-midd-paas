"""Internal synchronous HTTP adapter for the isolated simulation runner.

It is intentionally not exposed on a host port.  The governed Next route is
the public boundary and authorizes the actor before forwarding a request here.
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from uuid import UUID

from iot_middleware.services.simulation_replay_runner import SimulationReplayRejected, SimulationReplayRunner
from iot_middleware.storage.simulation_run_repository import SimulationRunRepository


app = FastAPI(title="Midd IoT Simulation Replay", docs_url=None, redoc_url=None, openapi_url=None)


class ExecuteRequest(BaseModel):
    project_id: UUID
    session_id: UUID
    created_by: str


def serialize(run):
    return {"id": run.id, "project_id": run.project_id, "session_id": run.session_id, "status": run.status,
            "created_by": run.created_by, "engine_version": run.engine_version,
            "replay_engine_version": run.replay_engine_version, "clock_model_version": run.clock_model_version,
            "output_count": run.output_count, "created_at": run.created_at.isoformat(),
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "failure_code": run.failure_code}


@app.post("/internal/simulation-runs")
def execute(request: ExecuteRequest):
    try:
        return serialize(SimulationReplayRunner().execute(project_id=str(request.project_id), session_id=str(request.session_id), created_by=request.created_by))
    except SimulationReplayRejected as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/internal/simulation-runs/{project_id}/{session_id}/{run_id}")
def get_run(project_id: UUID, session_id: UUID, run_id: UUID):
    run = SimulationRunRepository().get(str(project_id), str(session_id), str(run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    return serialize(run)


@app.get("/internal/simulation-runs/{project_id}/{session_id}/{run_id}/result")
def get_result(project_id: UUID, session_id: UUID, run_id: UUID):
    result = SimulationRunRepository().get_result(str(project_id), str(session_id), str(run_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Simulation result not found")
    return {"id": result.id, "project_id": result.project_id, "session_id": result.session_id, "run_id": result.run_id,
            "experiment_fingerprint": result.experiment_fingerprint, "result_fingerprint": result.result_fingerprint,
            "processed_events": result.processed_events, "evaluation_count": result.evaluation_count,
            "recommendation_count": result.recommendation_count, "actionable_recommendation_count": result.actionable_recommendation_count,
            "recommendation_only_count": result.recommendation_only_count, "failed_domain_event_count": result.failed_domain_event_count,
            "first_virtual_timestamp": result.first_virtual_timestamp.isoformat() if result.first_virtual_timestamp else None,
            "last_virtual_timestamp": result.last_virtual_timestamp.isoformat() if result.last_virtual_timestamp else None,
            "canonical_result_schema_version": result.canonical_result_schema_version}


@app.get("/internal/simulation-runs/{project_id}/{session_id}/{run_id}/trace")
def get_trace(project_id: UUID, session_id: UUID, run_id: UUID, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    try:
        items, total = SimulationRunRepository().trace(str(project_id), str(session_id), str(run_id), limit=limit, offset=offset)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Simulation run not found") from exc
    return {"items": items, "total": total, "limit": limit, "offset": offset}
