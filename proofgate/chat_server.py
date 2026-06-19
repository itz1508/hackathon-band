"""ProofGate local application: static website + agent runtime + mirror display.

Run:
    python -m proofgate.chat_server

Serves:
    http://127.0.0.1:8080

Entry method: direct Human API submission to Intake, followed by Band agent handoffs.
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import settings
from .agent_supervisor import AgentSupervisor
from .band_human_client import BandHumanAPIError, BandHumanClient
from .chat_entry import ChatEntryError, prepare_intake_message
from .chat_models import ChatSendRequest, ChatSendResponse, ChatStatusResponse
from .mirror import BandMirror

# --- State ---

_supervisor: AgentSupervisor | None = None
_mirror: BandMirror | None = None
_submitted_request_ids: set[str] = set()


# --- Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _supervisor, _mirror

    _mirror = BandMirror()

    if settings.autostart_agents():
        _supervisor = AgentSupervisor(
            start_timeout=settings.agent_start_timeout(),
            restart_limit=settings.agent_restart_limit(),
        )
        results = _supervisor.start_all()
        for r in results:
            if r["status"] == "failed":
                _supervisor.restart_role(r["role"])

    yield

    if _supervisor:
        _supervisor.stop_all()


# --- App ---

DEMO_DIR = Path(__file__).resolve().parents[1] / "demo"

app = FastAPI(title="ProofGate for Band", version="1.0", lifespan=lifespan)


# --- Static serving ---

@app.get("/")
async def serve_index():
    return FileResponse(DEMO_DIR / "index.html", media_type="text/html")


app.mount("/assets", StaticFiles(directory=str(DEMO_DIR / "assets"), check_dir=False), name="assets")
app.mount("/data", StaticFiles(directory=str(DEMO_DIR / "data"), check_dir=False), name="data")


@app.get("/styles.css")
async def serve_css():
    return FileResponse(DEMO_DIR / "styles.css", media_type="text/css")


@app.get("/app.js")
async def serve_js():
    return FileResponse(DEMO_DIR / "app.js", media_type="application/javascript")


# --- Runtime API ---

@app.get("/internal/runtime/status")
async def runtime_status() -> dict[str, Any]:
    agents = _supervisor.status() if _supervisor else []
    all_running = _supervisor.all_running() if _supervisor else False
    return {
        "runtime_on": all_running,
        "agents": agents,
        "all_running": all_running,
    }


@app.post("/internal/runtime/start")
async def runtime_start() -> dict[str, Any]:
    global _supervisor
    if _supervisor and _supervisor.all_running():
        return {"status": "already_running", "agents": _supervisor.status()}

    if not _supervisor:
        _supervisor = AgentSupervisor(
            start_timeout=settings.agent_start_timeout(),
            restart_limit=settings.agent_restart_limit(),
        )

    results = _supervisor.start_all()
    for r in results:
        if r["status"] == "failed":
            _supervisor.restart_role(r["role"])

    return {"status": "started", "agents": _supervisor.status()}


@app.post("/internal/runtime/stop")
async def runtime_stop() -> dict[str, Any]:
    if _supervisor:
        _supervisor.stop_all()
    return {"status": "stopped", "agents": _supervisor.status() if _supervisor else []}


# --- Chat Status ---

def _human_client() -> BandHumanClient | None:
    api_key = settings.band_human_api_key()
    if not api_key:
        return None
    return BandHumanClient(api_key=api_key, base_url=settings.band_api_base_url())


def _safe_band_error(exc: Exception) -> str:
    if isinstance(exc, BandHumanAPIError):
        if exc.status in (401, 403):
            return "Band authentication or room access failed"
        if exc.status == 404:
            return "Band room or participant was not found"
    return "Band is unavailable"


def _message_id(payload: dict[str, Any]) -> str:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    value = data.get("id") or data.get("message_id") if isinstance(data, dict) else None
    return str(value or "accepted")


@app.get("/internal/chat/status", response_model=ChatStatusResponse)
async def chat_status() -> ChatStatusResponse:
    room_url = settings._env("BAND_ROOM_URL", "")
    all_running = _supervisor.all_running() if _supervisor else False
    agents = _supervisor.status() if _supervisor else []
    agents_running = sum(1 for item in agents if item.get("running"))
    room_id = settings.band_room_id()
    client = _human_client()
    band_connected = False
    room_selected = False
    intake_present = False
    error = None

    if not client:
        error = "Band Human API key is missing"
    elif not room_id:
        error = "Band room is not configured"
    else:
        try:
            health = await client.health()
            band_connected = bool(health.get("connected") and health.get("authenticated"))
            if not band_connected:
                error = "Band authentication failed"
            else:
                await client.get_room(room_id)
                room_selected = True
                intake_present = bool(await client.resolve_participant(
                    room_id, settings.band_intake_handle()
                ))
                if not intake_present:
                    error = "Intake participant is not present in the configured room"
        except Exception as exc:
            error = _safe_band_error(exc)

    # Check for active run from mirror
    active_run_id = None
    if _mirror:
        runs = _mirror.runs(limit=1)
        if runs and not runs[0].get("outcome"):
            active_run_id = runs[0]["run_id"]

    return ChatStatusResponse(
        mode=settings.chat_mode(),
        band_connected=band_connected,
        room_selected=room_selected,
        intake_present=intake_present,
        intake_handle=f"@{settings.band_intake_handle()}",
        agents_running=agents_running,
        all_agents_running=all_running,
        send_enabled=bool(all_running and band_connected and room_selected and intake_present),
        room_url=room_url,
        active_run_id=active_run_id,
        error=error or (None if all_running else "Start all five agents"),
    )


@app.post("/internal/chat/send", response_model=ChatSendResponse)
async def chat_send(request: ChatSendRequest) -> ChatSendResponse:
    if not _supervisor or not _supervisor.all_running():
        raise HTTPException(
            status_code=409,
            detail={"code": "agents_not_running", "message": "Start all five agents before sending."},
        )

    client = _human_client()
    room_id = settings.band_room_id()
    if not client or not room_id:
        raise HTTPException(
            status_code=503,
            detail={"code": "band_not_configured", "message": "Band submission is not configured."},
        )

    request_id = request.client_request_id
    if request_id and request_id in _submitted_request_ids:
        raise HTTPException(
            status_code=409,
            detail={"code": "duplicate_submission", "message": "This request was already submitted."},
        )

    if request_id:
        _submitted_request_ids.add(request_id)
    try:
        health = await client.health()
        if not health.get("connected") or not health.get("authenticated"):
            raise HTTPException(
                status_code=503,
                detail={"code": "band_unavailable", "message": "Band authentication failed."},
            )
        await client.get_room(room_id)
        intake = await client.resolve_participant(room_id, settings.band_intake_handle())
        intake_id = (intake or {}).get("id") or (intake or {}).get("participant_id")
        if not intake_id:
            raise HTTPException(
                status_code=409,
                detail={"code": "intake_missing", "message": "Intake is not present in the configured Band room."},
            )
        prepared = prepare_intake_message(
            request.text,
            intake_handle=settings.band_intake_handle(),
            intake_participant_id=intake_id,
        )
        sent = await client.send_message(room_id, prepared.band_content, prepared.mentions)
    except ChatEntryError as exc:
        if request_id:
            _submitted_request_ids.discard(request_id)
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_request", "message": str(exc)},
        ) from exc
    except HTTPException:
        if request_id:
            _submitted_request_ids.discard(request_id)
        raise
    except Exception as exc:
        if request_id:
            _submitted_request_ids.discard(request_id)
        raise HTTPException(
            status_code=503,
            detail={"code": "band_send_failed", "message": _safe_band_error(exc)},
        ) from exc

    return ChatSendResponse(
        message_id=_message_id(sent),
        display_text=prepared.display_text,
        routed_to=f"@{prepared.target_handle}",
        status="sent",
    )


# --- Events from Mirror ---

@app.get("/internal/chat/events")
async def chat_events(run_id: str = "", after_sequence: int = 0) -> dict[str, Any]:
    if not _mirror:
        return {"events": [], "next_sequence": 0, "terminal": False}

    if not run_id:
        # Get latest run
        runs = _mirror.runs(limit=1)
        if not runs:
            return {"events": [], "next_sequence": 0, "terminal": False}
        run_id = runs[0]["run_id"]

    events = _mirror.events(run_id, after_sequence)
    terminal = False
    for ev in events:
        packet = ev.get("packet")
        if (packet and packet.get("from_role") == "finalizing"
                and packet.get("to_role") == "human"
                and packet.get("final_result")
                and packet["final_result"].get("outcome") in ("completed", "resolved_after_isolation", "blocked", "failed")):
            terminal = True

    next_seq = events[-1]["sequence"] if events else after_sequence
    return {"run_id": run_id, "events": events, "next_sequence": next_seq, "terminal": terminal}


@app.get("/internal/chat/runs/{run_id}")
async def chat_run(run_id: str) -> dict[str, Any]:
    if not _mirror:
        raise HTTPException(status_code=404, detail="Mirror not available")

    run = _mirror.run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    events = _mirror.events(run_id)
    packet = run.get("packet", {})

    workflow_path = []
    stage_results = {}
    roles = []
    stage_result_sequence = packet.get("stage_results", [])
    for sr in stage_result_sequence:
        stage = sr.get("stage", "")
        if stage and stage not in roles:
            roles.append(stage)
        display_stage = stage
        if stage == "resolution" and stage in stage_results:
            display_stage = "resolution-retry"
        if display_stage:
            workflow_path.append(display_stage)
            stage_results[display_stage] = sr

    final_result = packet.get("final_result", {}) or {}
    outcome = run.get("outcome", "") or final_result.get("outcome", "")

    conversation_events = []
    for ev in events:
        ep = ev.get("packet", {}) or {}
        routing = ep.get("routing", {})
        conversation_events.append({
            "sequence": ev.get("sequence", 0),
            "timestamp": ev.get("created_at", ""),
            "sender_role": ep.get("from_role", ""),
            "recipient_role": ep.get("to_role", ""),
            "event": routing.get("reason", ""),
            "summary": _summarize(routing.get("reason", "")),
        })

    return {
        "run_id": run_id,
        "objective": packet.get("objective", ""),
        "constraints": packet.get("constraints", []),
        "outcome": outcome,
        "retry_count": packet.get("retry_count", 0),
        "roles_participated": roles,
        "workflow_path": workflow_path,
        "stage_results": stage_results,
        "stage_result_sequence": stage_result_sequence,
        "conversation_events": conversation_events,
        "final_result": final_result,
        "terminal": bool(outcome),
        "status": "terminal" if outcome else ("running" if roles else "pending"),
    }


# --- Commands & Test Inputs ---

BUILT_IN_COMMANDS = [
    {"id": "fix", "label": "Fix", "action_lane": "resolve", "template": "Fix the following issue: [describe the problem and target file]."},
    {"id": "review", "label": "Review", "action_lane": "review", "template": "Review the following target: [target file or path]. Focus on: [what to look for]."},
]


@app.get("/internal/commands")
async def get_commands() -> dict[str, Any]:
    return {"commands": BUILT_IN_COMMANDS}


@app.get("/internal/test-inputs")
async def get_test_inputs() -> dict[str, Any]:
    items = []
    scan_dirs = [
        (DEMO_DIR / "data", "demo/data"),
        (Path(__file__).resolve().parents[1] / "docs" / "demo_run", "docs/demo_run"),
    ]
    for directory, prefix in scan_dirs:
        if directory.is_dir():
            for f in sorted(directory.glob("*.json")):
                try:
                    content = json.loads(f.read_text(encoding="utf-8"))
                    if not isinstance(content, dict) or "request_text" not in content:
                        continue
                    items.append({
                        "id": f.stem,
                        "label": content.get("label", f.stem.replace("-", " ").title()),
                        "path": f"{prefix}/{f.name}",
                        "request_text": content.get("request_text", ""),
                        "expected_workflow_path": content.get("expected_workflow_path", []),
                        "expected_outcome": content.get("expected_outcome", ""),
                    })
                except (json.JSONDecodeError, OSError):
                    continue
    return {"items": items}


def _summarize(reason: str) -> str:
    return {
        "new_request": "Human request submitted",
        "intake_complete": "Structured request created",
        "plan_complete": "Success criteria defined",
        "requirements_met": "Requirements met",
        "requirements_not_met": "Requirements not met — routing to isolation",
        "focused_retry": "Isolation context supplied for retry",
        "retry_exhausted": "Retry did not meet requirements",
        "terminal_result": "Terminal result delivered",
    }.get(reason, reason)


# --- Entrypoint ---

def main() -> int:
    import uvicorn

    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    except ImportError:
        pass

    h, p = settings.host(), settings.port()
    print(f"ProofGate for Band — http://{h}:{p}")
    print("Entry method: Direct Band submission")
    print(f"Auto-start agents: {settings.autostart_agents()}")

    uvicorn.run("proofgate.chat_server:app", host=h, port=p, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
