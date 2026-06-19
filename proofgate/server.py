"""Read-only HTTP mirror for actual ProofGate Band collaboration events."""
from __future__ import annotations

import argparse

from fastapi import FastAPI, HTTPException, Query

from .band_adapter import BAND_AGENTS
from .mirror import BandMirror

app = FastAPI(title="ProofGate Band Mirror", version="1.0")
mirror = BandMirror()
for agent in BAND_AGENTS:
    mirror.upsert_agent(agent.role, agent.display_name, agent.handle, agent.responsibility)


@app.get("/api/band/health")
def band_health() -> dict[str, object]:
    return {"status": "ok", "source": "band_mirror", "live_claim": False, "database": str(mirror.path)}


@app.get("/api/band/agents")
def band_agents() -> dict[str, object]:
    return {"agents": mirror.agents()}


@app.get("/api/band/runs")
def band_runs(limit: int = Query(20, ge=1, le=100)) -> dict[str, object]:
    return {"runs": mirror.runs(limit)}


@app.get("/api/band/runs/{run_id}")
def band_run(run_id: str) -> dict[str, object]:
    run = mirror.run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Band run not found")
    return run


@app.get("/api/band/runs/{run_id}/events")
def band_events(run_id: str, after_sequence: int = Query(0, ge=0)) -> dict[str, object]:
    if mirror.run(run_id) is None:
        raise HTTPException(status_code=404, detail="Band run not found")
    return {"events": mirror.events(run_id, after_sequence)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ProofGate Band mirror API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
