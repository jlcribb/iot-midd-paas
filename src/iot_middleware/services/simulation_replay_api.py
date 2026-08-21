"""Internal synchronous HTTP adapter for the isolated simulation runner.

It is intentionally not exposed on a host port.  The governed Next route is
the public boundary and authorizes the actor before forwarding a request here.
"""

from fastapi import FastAPI, HTTPException
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
