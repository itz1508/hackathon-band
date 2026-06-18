from __future__ import annotations

import asyncio
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="ProofGate API Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8787",
        "http://localhost:8787",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    message: str
    mode: str = "success"

jobs: dict[str, dict[str, Any]] = {}

def build_results(job_id: str, message: str) -> dict[str, Any]:
    return {
        "job_id": job_id,
        "status": "completed",
        "scenario": message,
        "demo_scenario": {
            "title": "Login Validator Fix",
            "problem": "Missing login validation",
            "fix": "Add email and password validation",
            "coverage": "4 simulated tests passing",
        },
        "success_path": [
            {"id": "intake", "name": "Intake", "role": "Request Intake", "agent": "@itz1508/intake", "description": "Accepted request", "details": "Request accepted.", "status": "done"},
            {"id": "planner", "name": "Planner", "role": "Task Planner", "agent": "@itz1508/planner", "description": "Planned work", "details": "Plan created.", "status": "done"},
            {"id": "engineer", "name": "Engineer", "role": "Patch Engineer", "agent": "@itz1508/engineer", "description": "Created patch", "details": "Patch simulated.", "status": "done"},
            {"id": "tester", "name": "Tester", "role": "Test Runner", "agent": "@itz1508/tester", "description": "Ran tests", "details": "Tests passed.", "status": "done"},
            {"id": "reviewer", "name": "Reviewer", "role": "Safety Review", "agent": "@itz1508/reviewer", "description": "Reviewed patch", "details": "Safe for demo.", "status": "done"},
        ],
        "failure_path": [
            {"id": "issue-isolator", "name": "Issue Isolator", "role": "Issue Isolation", "agent": "@itz1508/issue-isolator", "description": "Handles blocked changes", "details": "Failure path available.", "status": "done"}
        ],
        "transcript": [
            {"agent": "Intake", "handle": "@itz1508/intake", "message": "Received request.", "timestamp": "00:00:01", "type": "intake"},
            {"agent": "Planner", "handle": "@itz1508/planner", "message": "Plan created.", "timestamp": "00:00:03", "type": "planning"},
            {"agent": "Tester", "handle": "@itz1508/tester", "message": "Tests passed.", "timestamp": "00:00:06", "type": "testing"},
            {"agent": "Reviewer", "handle": "@itz1508/reviewer", "message": "Review complete.", "timestamp": "00:00:08", "type": "review"},
        ],
        "proof_packet": {
            "title": "ProofGate Proof Packet",
            "status": "success",
            "scenario": message,
            "what_wrong": "Validation was missing.",
            "why_it_matters": "Invalid login data should be rejected.",
            "how_to_fix": "Add email and password validation.",
            "simulated_diff": "+ validate_email()\n+ validate_password()",
            "validation_summary": "Simulated tests passed.",
            "safe_to_apply": True,
            "human_action": "APPROVED",
            "decision_reason": "Demo result passed validation.",
        },
        "failure_proof_packet": {
            "title": "ProofGate Failure Packet",
            "status": "failure",
            "scenario": message,
            "what_wrong": "Unsafe changes would be blocked.",
            "why_it_matters": "Blocked changes require review.",
            "how_to_fix": "Route to issue isolation.",
            "simulated_diff": "",
            "validation_summary": "Failure path available.",
            "safe_to_apply": False,
            "human_action": "REVIEW_REQUIRED",
            "decision_reason": "Failure path is not auto-applied.",
        },
        "test_cases": [
            {"name": "valid_email", "input": "user@example.com", "expected": True, "passed": True},
            {"name": "invalid_email", "input": "bad", "expected": False, "passed": True},
            {"name": "strong_password", "input": "Str0ng!Pass", "expected": True, "passed": True},
            {"name": "short_password", "input": "Ab1!", "expected": False, "passed": True},
        ],
        "artifact": {
            "diff": "+ validate_email()\n+ validate_password()",
            "summary": "Simulated validator patch generated.",
        },
        "error": None,
    }

async def run_job(job_id: str) -> None:
    steps = [
        ("Assessing request", 10, "Intake"),
        ("Planning task", 30, "Planner"),
        ("Writing patch", 55, "Engineer"),
        ("Running tests", 75, "Tester"),
        ("Reviewing result", 90, "Reviewer"),
    ]
    job = jobs[job_id]
    job["status"] = "running"
    for step, progress, agent in steps:
        job["current_step"] = step
        job["progress"] = progress
        job["agent"] = agent
        await asyncio.sleep(1)
    job["status"] = "completed"
    job["current_step"] = "Complete"
    job["progress"] = 100
    job["agent"] = None
    job["results"] = build_results(job_id, job["message"])

@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/api/run", status_code=201)
async def start_job(req: RunRequest) -> dict[str, str]:
    if req.mode not in ("success", "failure"):
        raise HTTPException(status_code=422, detail="mode must be success or failure")
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "message": req.message,
        "mode": req.mode,
        "status": "queued",
        "current_step": "Queued",
        "progress": 0,
        "agent": None,
        "error": None,
        "results": None,
    }
    asyncio.create_task(run_job(job_id))
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str) -> dict[str, Any]:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "current_step": job["current_step"],
        "progress": job["progress"],
        "agent": job["agent"],
        "error": job["error"],
    }

@app.get("/api/results/{job_id}")
async def get_results(job_id: str) -> dict[str, Any]:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed":
        raise HTTPException(status_code=409, detail="Job not yet completed")
    return job["results"]
