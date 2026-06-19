"""
ProofGate for Band — Upgraded Backend Server
=============================================
Serves both:
  - The dashboard frontend (demo/ directory)
  - The job-oriented REST API

Supports CLI: python -m proofgate.server --host 127.0.0.1 --port 8787

Replace SimulatedBandRunner with real Band agent calls when ready.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# -------------------------------------------------------------
# Pydantic models (match frontend types exactly)
# -------------------------------------------------------------


class RunJobRequest(BaseModel):
    message: str
    mode: str  # 'success' | 'failure'


class RunJobResponse(BaseModel):
    job_id: str
    status: str = "queued"


class JobStatusResponse(BaseModel):
    job_id: str
    status: str           # queued | running | completed | failed
    current_step: str | None = None
    progress: int = 0     # 0-100
    agent: str | None = None
    error: str | None = None


class AgentStepData(BaseModel):
    id: str
    name: str
    role: str
    agent: str
    description: str
    details: str
    status: str  # pending | active | done


class TranscriptMessageData(BaseModel):
    agent: str
    handle: str
    message: str
    timestamp: str
    type: str  # intake | planning | engineering | testing | review | human | issue


class TestCaseData(BaseModel):
    name: str
    input: str
    expected: str | bool
    passed: bool


class ProofPacketData(BaseModel):
    title: str
    status: str  # success | failure
    scenario: str
    what_wrong: str
    why_it_matters: str
    how_to_fix: str
    simulated_diff: str
    validation_summary: str
    safe_to_apply: bool
    human_action: str
    decision_reason: str


class DemoScenarioData(BaseModel):
    title: str
    problem: str
    fix: str
    coverage: str


class ArtifactData(BaseModel):
    diff: str
    summary: str


class JobResultsResponse(BaseModel):
    job_id: str
    status: str  # completed | failed
    scenario: str
    demo_scenario: DemoScenarioData
    success_path: list[AgentStepData]
    failure_path: list[AgentStepData]
    transcript: list[TranscriptMessageData]
    proof_packet: ProofPacketData
    failure_proof_packet: ProofPacketData
    test_cases: list[TestCaseData]
    artifact: ArtifactData | None = None
    error: str | None = None


# -------------------------------------------------------------
# In-memory job store
# -------------------------------------------------------------


class JobStage(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    job_id: str
    message: str
    mode: str
    status: JobStage = JobStage.QUEUED
    current_step: str | None = None
    progress: int = 0
    agent: str | None = None
    error: str | None = None
    results: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Global in-memory store
_jobs: dict[str, Job] = {}


# -------------------------------------------------------------
# Simulated Band Agent Runner
# -------------------------------------------------------------
# Isolated so real Band agents can replace it via the same interface.


class BandRunner:
    """
    Simulates the Band agent flow deterministically.
    To wire real agents, subclass or replace this class with one that
    calls actual Band APIs.
    """

    SUCCESS_AGENTS: list[dict[str, Any]] = [
        {
            "id": "intake",
            "name": "Intake",
            "role": "Request Intake",
            "agent": "@itz1508/intake",
            "description": "Accepts the request, assesses clarity, and assigns priority.",
            "step": "Assessing request clarity and priority",
            "progress": 10,
        },
        {
            "id": "planner",
            "name": "Planner",
            "role": "Task Planner",
            "agent": "@itz1508/planner",
            "description": "Breaks down the task into sub-tasks and identifies affected files.",
            "step": "Breaking down task into sub-tasks",
            "progress": 25,
        },
        {
            "id": "engineer",
            "name": "Engineer",
            "role": "Patch Engineer",
            "agent": "@itz1508/engineer",
            "description": "Writes the patch and produces a formatted diff.",
            "step": "Writing patch and generating diff",
            "progress": 45,
        },
        {
            "id": "tester",
            "name": "Tester",
            "role": "Test & Validate",
            "agent": "@itz1508/tester",
            "description": "Writes and runs tests, validates correctness.",
            "step": "Running test suite and validating",
            "progress": 65,
        },
        {
            "id": "reviewer",
            "name": "Reviewer",
            "role": "Safety Review",
            "agent": "@itz1508/reviewer",
            "description": "Evaluates safety, generates proof packet, and flags risks.",
            "step": "Reviewing patch for safety and generating proof packet",
            "progress": 80,
        },
        {
            "id": "human",
            "name": "Human",
            "role": "Human Apply Gate",
            "agent": "@itz1508/human",
            "description": "Reviews proof packet, makes final approval decision.",
            "step": "Human reviewing proof packet and making decision",
            "progress": 95,
        },
    ]

    FAILURE_AGENTS: list[dict[str, Any]] = [
        {
            "id": "reviewer-fail",
            "name": "Reviewer",
            "role": "Safety Review",
            "agent": "@itz1508/reviewer",
            "description": "Detects a critical issue in the patch during review.",
            "step": "Reviewing patch - detecting issues",
            "progress": 20,
        },
        {
            "id": "issue-isolator",
            "name": "Issue Isolator",
            "role": "Issue Isolation",
            "agent": "@itz1508/issue-isolator",
            "description": "Isolates the problem and produces a detailed isolation report.",
            "step": "Isolating root cause of detected issue",
            "progress": 50,
        },
        {
            "id": "reviewer-retry",
            "name": "Reviewer",
            "role": "Re-Review",
            "agent": "@itz1508/reviewer",
            "description": "Re-evaluates the patched fix after isolation.",
            "step": "Re-reviewing the fix",
            "progress": 75,
        },
        {
            "id": "human-fail",
            "name": "Human",
            "role": "Human Apply Gate",
            "agent": "@itz1508/human",
            "description": "Reviews the issue report and decides on the path forward.",
            "step": "Human reviewing issue isolation report",
            "progress": 95,
        },
    ]

    SUCCESS_TRANSCRIPT: list[dict[str, str]] = [
        {"agent": "Intake", "handle": "@itz1508/intake", "message": 'Received request: "Fix login validator to enforce email format and password strength." Assessing clarity...', "timestamp": "00:00:02", "type": "intake"},
        {"agent": "Intake", "handle": "@itz1508/intake", "message": "Request clear. Priority: High. Routing to @itz1508/planner with scope: `src/auth/validators.py`.", "timestamp": "00:00:04", "type": "intake"},
        {"agent": "Planner", "handle": "@itz1508/planner", "message": "Breaking down task. Identified 4 sub-tasks: (1) email validation function, (2) password validator, (3) update login(), (4) unit tests.", "timestamp": "00:00:08", "type": "planning"},
        {"agent": "Planner", "handle": "@itz1508/planner", "message": "Scope confirmed: single file. Risk: Low. Routing to @itz1508/engineer.", "timestamp": "00:00:10", "type": "planning"},
        {"agent": "Engineer", "handle": "@itz1508/engineer", "message": "Writing patch. Adding `validate_email()` with regex, `validate_password()` with multi-rule check.", "timestamp": "00:00:15", "type": "engineering"},
        {"agent": "Engineer", "handle": "@itz1508/engineer", "message": "Patch ready. 26 lines added, 2 lines changed. Routing to @itz1508/tester with diff.", "timestamp": "00:00:18", "type": "engineering"},
        {"agent": "Tester", "handle": "@itz1508/tester", "message": "Running test suite... 10 test cases for validation functions.", "timestamp": "00:00:22", "type": "testing"},
        {"agent": "Tester", "handle": "@itz1508/tester", "message": "All 10/10 tests pass. Coverage: 100%. Routing to @itz1508/reviewer.", "timestamp": "00:00:25", "type": "testing"},
        {"agent": "Reviewer", "handle": "@itz1508/reviewer", "message": "Reviewing patch. Checking for security issues, edge cases, code quality...", "timestamp": "00:00:30", "type": "review"},
        {"agent": "Reviewer", "handle": "@itz1508/reviewer", "message": "No issues found. Generating proof packet. safe_to_apply: true. Routing to @itz1508/human.", "timestamp": "00:00:33", "type": "review"},
        {"agent": "Human", "handle": "@itz1508/human", "message": "Proof packet received. Reviewing evidence: scope, plan, diff, test results, safety assessment.", "timestamp": "00:00:38", "type": "human"},
        {"agent": "Human", "handle": "@itz1508/human", "message": "APPROVED. Patch applied to main branch. Proof packet archived.", "timestamp": "00:00:42", "type": "human"},
    ]

    FAILURE_TRANSCRIPT: list[dict[str, str]] = [
        {"agent": "Intake", "handle": "@itz1508/intake", "message": 'Received request: "Fix SQL injection vulnerability in login query." Assessing...', "timestamp": "00:00:02", "type": "intake"},
        {"agent": "Planner", "handle": "@itz1508/planner", "message": "Task: parameterize SQL query in login endpoint. Scope: single file.", "timestamp": "00:00:06", "type": "planning"},
        {"agent": "Engineer", "handle": "@itz1508/engineer", "message": "Patch submitted - replaced query with f-string interpolation.", "timestamp": "00:00:12", "type": "engineering"},
        {"agent": "Reviewer", "handle": "@itz1508/reviewer", "message": "CRITICAL ISSUE: SQL injection vector detected (CWE-89). Routing to @itz1508/issue-isolator.", "timestamp": "00:00:18", "type": "review"},
        {"agent": "Issue Isolator", "handle": "@itz1508/issue-isolator", "message": "Isolating root cause: `src/auth/login.py` line 42 uses f-string. Suggested fix: parameterized query.", "timestamp": "00:00:24", "type": "issue"},
        {"agent": "Engineer", "handle": "@itz1508/engineer", "message": "Fix applied: replaced with parameterized query using %s placeholder.", "timestamp": "00:00:30", "type": "engineering"},
        {"agent": "Reviewer", "handle": "@itz1508/reviewer", "message": "Fix verified. No injection paths remain. Routing to @itz1508/human.", "timestamp": "00:00:36", "type": "review"},
        {"agent": "Human", "handle": "@itz1508/human", "message": "Issue isolation report reviewed. APPROVED with caveat: add integration test.", "timestamp": "00:00:42", "type": "human"},
    ]

    def __init__(self, delay_per_step: float = 1.5):
        self.delay = delay_per_step

    async def run(self, job: Job) -> None:
        """
        Simulate the agent pipeline deterministically.
        Sets job.results when done, or job.error on failure.
        """
        try:
            job.status = JobStage.RUNNING

            if job.mode == "failure":
                await self._simulate_failure_path(job)
            else:
                await self._simulate_success_path(job)

            job.status = JobStage.COMPLETED
            job.progress = 100
            job.current_step = "Complete"
            job.agent = None

        except Exception as exc:
            job.status = JobStage.FAILED
            job.error = str(exc)
            job.current_step = "Error"
            job.agent = None

    async def _simulate_success_path(self, job: Job) -> None:
        scenario = job.message or "Fix a login validator so whitespace-only emails are rejected."

        for agent_info in self.SUCCESS_AGENTS:
            job.current_step = agent_info["step"]
            job.progress = agent_info["progress"]
            job.agent = agent_info["agent"]
            await asyncio.sleep(self.delay)

        success_path = [
            {
                "id": "intake",
                "name": "Intake",
                "role": "Request Intake",
                "agent": "@itz1508/intake",
                "description": "Accepts the request, assesses clarity, and assigns priority.",
                "details": "## Task Assessment\n**Request:** \"" + scenario + "\"\n\n**Clarity:** Clear.\n**Priority:** High — login validation is a critical security boundary.\n**Scope:** Single file: `src/auth/validators.py`",
                "status": "done",
            },
            {
                "id": "planner",
                "name": "Planner",
                "role": "Task Planner",
                "agent": "@itz1508/planner",
                "description": "Breaks down the task into sub-tasks and identifies affected files.",
                "details": "## Task Breakdown\n**Sub-tasks:**\n1. Add email regex validation function\n2. Add password strength check function\n3. Update `login()` to call both validators\n4. Add unit tests\n\n**Risk:** Low — isolated change.",
                "status": "done",
            },
            {
                "id": "engineer",
                "name": "Engineer",
                "role": "Patch Engineer",
                "agent": "@itz1508/engineer",
                "description": "Writes the patch and produces a formatted diff.",
                "details": "## Patch Proposal\n\n```diff\n--- a/src/auth/validators.py\n+++ b/src/auth/validators.py\n@@ -1,5 +1,31 @@\n+import re\n+EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$')\n+\n+def validate_email(email: str) -> bool:\n+    return bool(EMAIL_REGEX.match(email.strip()))\n...```\n\n**26 lines added.**",
                "status": "done",
            },
            {
                "id": "tester",
                "name": "Tester",
                "role": "Test & Validate",
                "agent": "@itz1508/tester",
                "description": "Writes and runs tests, validates correctness.",
                "details": "## Test Results\n\n```\n test_valid_email — True\n test_invalid_email — False\n... 10/10 pass\n```\n\n**Coverage:** 100%",
                "status": "done",
            },
            {
                "id": "reviewer",
                "name": "Reviewer",
                "role": "Safety Review",
                "agent": "@itz1508/reviewer",
                "description": "Evaluates safety, generates proof packet, and flags risks.",
                "details": "## Review Assessment\n\n**Code quality:** Clean.\n**Security:** No issues.\n**Verdict:** SAFE TO APPLY",
                "status": "done",
            },
            {
                "id": "human",
                "name": "Human",
                "role": "Human Apply Gate",
                "agent": "@itz1508/human",
                "description": "Reviews proof packet, makes final approval decision.",
                "details": "## Human Review\n\n- Approve request assessed\n- Patch is correct\n- All tests pass\n- No security concerns\n\n**Decision:** APPROVED",
                "status": "done",
            },
        ]

        failure_path = [
            {
                "id": "reviewer-fail",
                "name": "Reviewer",
                "role": "Safety Review",
                "agent": "@itz1508/reviewer",
                "description": "Detects a critical issue in the patch during review.",
                "details": "## Review Assessment\n\n**Issue detected:** No issues — success mode.\n**Verdict:** Clean.",
                "status": "done",
            },
            {
                "id": "issue-isolator",
                "name": "Issue Isolator",
                "role": "Issue Isolation",
                "agent": "@itz1508/issue-isolator",
                "description": "Isolates the problem and produces a detailed isolation report.",
                "details": "## Issue Isolation Report\n\n**No issues in success mode.**\n\nAll agents completed successfully.",
                "status": "done",
            },
            {
                "id": "reviewer-retry",
                "name": "Reviewer",
                "role": "Re-Review",
                "agent": "@itz1508/reviewer",
                "description": "Re-evaluates the patched fix after isolation.",
                "details": "## Re-Review\n\n**All clear.**",
                "status": "done",
            },
            {
                "id": "human-fail",
                "name": "Human",
                "role": "Human Apply Gate",
                "agent": "@itz1508/human",
                "description": "Reviews the issue report and decides on the path forward.",
                "details": "## Human Review\n\n**Decision:** APPROVED\n\nNo issues found. Patch applied.",
                "status": "done",
            },
        ]

        transcript = [
            TranscriptMessageData(**msg).model_dump()
            for msg in self.SUCCESS_TRANSCRIPT
        ]

        job.results = {
            "job_id": job.job_id,
            "status": "completed",
            "scenario": scenario,
            "demo_scenario": {
                "title": "Login Validator Fix",
                "problem": "No email format or password strength validation",
                "fix": "26 lines added: regex + strength checks",
                "coverage": "10 test cases, 100% coverage",
            },
            "success_path": success_path,
            "failure_path": failure_path,
            "transcript": transcript,
            "proof_packet": {
                "title": "Login Validator — Clean Patch",
                "status": "success",
                "scenario": scenario,
                "what_wrong": "Login endpoint accepts any string as email and password - no validation.",
                "why_it_matters": "Unvalidated input causes 70%+ of auth-related issues.",
                "how_to_fix": "Add regex-based email validation and a multi-rule password strength check function.",
                "simulated_diff": "--- a/src/auth/validators.py\n+++ b/src/auth/validators.py\n@@ -1,5 +1,31 @@\n def is_valid_email(value):\n-    return \"@\" in value\n+    value = value.strip()\n+    return bool(value) and \"@\" in value",
                "validation_summary": "10/10 tests pass. 100% coverage on new code.",
                "safe_to_apply": True,
                "human_action": "APPROVED",
                "decision_reason": "Clean, minimal patch. All tests pass. No security concerns.",
            },
            "failure_proof_packet": {
                "title": "Login Query — SQL Injection Risk",
                "status": "failure",
                "scenario": scenario,
                "what_wrong": "The login validator accepts whitespace-only values because it checks only for an at sign.",
                "why_it_matters": "A weak validator lets invalid identity input pass into downstream login and account flows.",
                "how_to_fix": "Trim the email value, reject empty strings, and keep the existing at-sign check.",
                "simulated_diff": "--- a/src/auth/login.py\n+++ b/src/auth/login.py\n@@ -39,7 +39,9 @@\n-    query = f\"SELECT * FROM users WHERE email = '{email}'\"\n-    cursor.execute(query)\n+    cursor.execute(\n+        \"SELECT * FROM users WHERE email = %s\",\n+        (email,)\n+    )",
                "validation_summary": "Fix verified. No injection paths remain.",
                "safe_to_apply": False,
                "human_action": "APPROVED_WITH_CAVEAT",
                "decision_reason": "Original patch had critical vulnerability. Fix verified. Approved with caveat.",
            },
            "test_cases": [
                {"name": "test_valid_email", "input": "user@example.com", "expected": True, "passed": True},
                {"name": "test_valid_email_subdomain", "input": "user@sub.example.com", "expected": True, "passed": True},
                {"name": "test_invalid_email_no_at", "input": "userexample.com", "expected": False, "passed": True},
                {"name": "test_valid_password_strong", "input": "Str0ng!Pass", "expected": True, "passed": True},
                {"name": "test_invalid_password_short", "input": "Ab1!x", "expected": False, "passed": True},
                {"name": "test_invalid_password_no_upper", "input": "str0ng!pass", "expected": False, "passed": True},
                {"name": "test_invalid_password_no_number", "input": "Strong!Pass", "expected": False, "passed": True},
                {"name": "test_invalid_password_no_special", "input": "Str0ngPass", "expected": False, "passed": True},
                {"name": "test_invalid_email_empty", "input": "", "expected": False, "passed": True},
                {"name": "test_invalid_email_whitespace", "input": "   ", "expected": False, "passed": True},
            ],
            "artifact": {
                "diff": "--- a/src/auth/validators.py\n+++ b/src/auth/validators.py\n@@ -1,5 +1,31 @@\n+import re\n+...",
                "summary": "Added email validation and password strength check. 26 lines added.",
            },
        }

    async def _simulate_failure_path(self, job: Job) -> None:
        scenario = job.message or "Fix SQL injection vulnerability in login query"

        for agent_info in self.FAILURE_AGENTS:
            job.current_step = agent_info["step"]
            job.progress = agent_info["progress"]
            job.agent = agent_info["agent"]
            await asyncio.sleep(self.delay)

        success_path = [
            {
                "id": "intake",
                "name": "Intake",
                "role": "Request Intake",
                "agent": "@itz1508/intake",
                "description": "Accepts the request, assesses clarity, and assigns priority.",
                "details": "## Task Assessment\n**Request:** \"" + scenario + "\"\n\n**Priority:** High — SQL injection is critical.",
                "status": "done",
            },
            {
                "id": "planner",
                "name": "Planner",
                "role": "Task Planner",
                "agent": "@itz1508/planner",
                "description": "Breaks down the task into sub-tasks and identifies affected files.",
                "details": "## Task Breakdown\n**File:** `src/auth/login.py`\n**Sub-tasks:** 1. Replace f-string with parameterized query 2. Update tests",
                "status": "done",
            },
            {
                "id": "engineer",
                "name": "Engineer",
                "role": "Patch Engineer",
                "agent": "@itz1508/engineer",
                "description": "Writes the patch and produces a formatted diff.",
                "details": "## Patch Proposal\n\n Initial patch introduced SQL injection. Issue isolator identified the problem. Fix applied.",
                "status": "done",
            },
            {
                "id": "tester",
                "name": "Tester",
                "role": "Test & Validate",
                "agent": "@itz1508/tester",
                "description": "Writes and runs tests, validates correctness.",
                "details": "## Test Results\n\n```\n test_injection_attempt_blocked\n test_valid_login\n```\n\nAll edge cases covered.",
                "status": "done",
            },
            {
                "id": "reviewer",
                "name": "Reviewer",
                "role": "Safety Review",
                "agent": "@itz1508/reviewer",
                "description": "Evaluates safety, generates proof packet, and flags risks.",
                "details": "## Review Assessment\n\n**Original patch:** SQL injection (CWE-89)\n**Fixed patch:** Parameterized query — safe.\n**Verdict:** SAFE TO APPLY",
                "status": "done",
            },
            {
                "id": "human",
                "name": "Human",
                "role": "Human Apply Gate",
                "agent": "@itz1508/human",
                "description": "Reviews proof packet, makes final approval decision.",
                "details": "## Human Review\n\n- Original patch had SQL injection\n- Issue isolator identified root cause\n- Fix applied and verified\n\n**Decision:** APPROVED with caveat — add integration test.",
                "status": "done",
            },
        ]

        failure_path = [
            {
                "id": "reviewer-fail",
                "name": "Reviewer",
                "role": "Safety Review",
                "agent": "@itz1508/reviewer",
                "description": "Detects a critical issue in the patch during review.",
                "details": "## Review Assessment\n\n**Issue detected:** SQL injection vector (CWE-89).\n\n**Severity:** CRITICAL\n\n**Action:** Flagging patch. Routing to Issue Isolator.",
                "status": "done",
            },
            {
                "id": "issue-isolator",
                "name": "Issue Isolator",
                "role": "Issue Isolation",
                "agent": "@itz1508/issue-isolator",
                "description": "Isolates the problem and produces a detailed isolation report.",
                "details": "## Issue Isolation Report\n\n**Issue:** SQL Injection (CWE-89)\n**Root cause:** `src/auth/login.py` line 42 uses f-string.\n**Suggested fix:** Parameterized query.\n\n```python\ncursor.execute(\n    \"SELECT * FROM users WHERE email = %s\",\n    (email,)\n)\n```",
                "status": "done",
            },
            {
                "id": "reviewer-retry",
                "name": "Reviewer",
                "role": "Re-Review",
                "agent": "@itz1508/reviewer",
                "description": "Re-evaluates the patched fix after isolation.",
                "details": "## Re-Review Assessment\n\n**Fix verified:** Parameterized query applied.\n\n**Verdict:** FIX VERIFIED — Now safe to apply.",
                "status": "done",
            },
            {
                "id": "human-fail",
                "name": "Human",
                "role": "Human Apply Gate",
                "agent": "@itz1508/human",
                "description": "Reviews the issue report and decides on the path forward.",
                "details": "## Human Review\n\n- Original patch contained SQL injection\n- Issue isolator correctly identified root cause\n- Fix applied and verified\n\n**Decision:** APPROVED with caveat.",
                "status": "done",
            },
        ]

        transcript = [
            TranscriptMessageData(**msg).model_dump()
            for msg in self.FAILURE_TRANSCRIPT
        ]

        job.results = {
            "job_id": job.job_id,
            "status": "completed",
            "scenario": scenario,
            "demo_scenario": {
                "title": "SQL Injection Fix",
                "problem": "Engineer patch uses f-string interpolation — introduces SQL injection",
                "fix": "3 lines changed: parameterized query with %s placeholder",
                "coverage": "3 test cases, 100% coverage",
            },
            "success_path": success_path,
            "failure_path": failure_path,
            "transcript": transcript,
            "proof_packet": {
                "title": "Login Validator — Clean Patch",
                "status": "success",
                "scenario": scenario,
                "what_wrong": "Login endpoint accepts any string as email and password — no validation.",
                "why_it_matters": "Unvalidated input causes 70%+ of auth-related issues.",
                "how_to_fix": "Add regex-based email validation and a multi-rule password strength check function.",
                "simulated_diff": "--- a/src/auth/validators.py\n+++ b/src/auth/validators.py\n@@ -1,5 +1,31 @@\n+import re\n+...",
                "validation_summary": "All tests pass. Fix verified.",
                "safe_to_apply": True,
                "human_action": "APPROVED",
                "decision_reason": "Clean, minimal patch.",
            },
            "failure_proof_packet": {
                "title": "Login Query — SQL Injection Risk",
                "status": "failure",
                "scenario": scenario,
                "what_wrong": "Engineer patch used f-string interpolation for SQL query instead of parameterized query.",
                "why_it_matters": "SQL injection is a top-3 OWASP vulnerability.",
                "how_to_fix": "Replace string interpolation with parameterized query using %s placeholders.",
                "simulated_diff": "--- a/src/auth/login.py\n+++ b/src/auth/login.py\n@@ -39,7 +39,9 @@\n-    query = f\"SELECT * FROM users WHERE email = '{email}'\"\n-    cursor.execute(query)\n+    cursor.execute(\n+        \"SELECT * FROM users WHERE email = %s\",\n+        (email,)\n+    )",
                "validation_summary": "Fix verified. No injection paths remain.",
                "safe_to_apply": False,
                "human_action": "APPROVED_WITH_CAVEAT",
                "decision_reason": "Original patch had critical vulnerability. Fix verified. Approved with caveat.",
            },
            "test_cases": [
                {"name": "test_injection_attempt_blocked", "input": "admin' OR '1'='1", "expected": False, "passed": True},
                {"name": "test_valid_login", "input": "user@example.com", "expected": True, "passed": True},
                {"name": "test_empty_email", "input": "", "expected": False, "passed": True},
            ],
            "artifact": {
                "diff": "--- a/src/auth/login.py\n+++ b/src/auth/login.py\n@@ -39,7 +39,9 @@\n-    query = f\"SELECT * FROM users WHERE email = '{email}'\"\n+    cursor.execute(\n+        \"SELECT * FROM users WHERE email = %s\",\n+        (email,)\n+    )",
                "summary": "Replaced SQL string interpolation with parameterized query to fix SQL injection.",
            },
        }


# -------------------------------------------------------------
# FastAPI app
# -------------------------------------------------------------

app = FastAPI(
    title="ProofGate for Band",
    version="0.1.0",
    description="Backend API for the ProofGate Band-agent demo",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

runner = BandRunner(delay_per_step=1.5)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/run", status_code=201)
async def run_job(
    req: RunJobRequest, background_tasks: BackgroundTasks
) -> RunJobResponse:
    if req.mode not in ("success", "failure"):
        raise HTTPException(status_code=422, detail="mode must be 'success' or 'failure'")

    job_id = str(uuid.uuid4())
    job = Job(
        job_id=job_id,
        message=req.message,
        mode=req.mode,
    )
    _jobs[job_id] = job

    # Kick off the simulation in the background using FastAPI's BackgroundTasks
    background_tasks.add_task(runner.run, job)

    return RunJobResponse(job_id=job_id, status="queued")


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str) -> JobStatusResponse:
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status.value,
        current_step=job.current_step,
        progress=job.progress,
        agent=job.agent,
        error=job.error,
    )


@app.get("/api/results/{job_id}")
async def get_job_results(job_id: str) -> JobResultsResponse:
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == JobStage.RUNNING or job.status == JobStage.QUEUED:
        raise HTTPException(status_code=409, detail="Job not yet completed")

    if job.results is None:
        raise HTTPException(status_code=500, detail="Job completed but no results available")

    # job.results already contains job_id and status — avoid duplication
    return JobResultsResponse(
        job_id=job.job_id,
        status=job.status.value,
        **{k: v for k, v in job.results.items() if k not in ("job_id", "status")},
    )


# Serve static dashboard files from the demo/ directory
# IMPORTANT: Mounted AFTER API routes so /api/* reaches handlers first
_demo_dir = os.path.join(os.path.dirname(__file__), "..", "demo")
if os.path.isdir(_demo_dir):
    app.mount("/", StaticFiles(directory=_demo_dir, html=True), name="dashboard")


# -------------------------------------------------------------
# CLI entry point
# Run:    python -m proofgate.server --host 127.0.0.1 --port 8787
# -------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="ProofGate for Band — Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8787, help="Port to bind (default: 8787)")
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(
        "proofgate.server:app",
        host=args.host,
        port=args.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
