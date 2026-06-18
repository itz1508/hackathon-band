"""Local ProofGate multi-agent demo engine."""
from __future__ import annotations

import difflib
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


DEMO_BEFORE = """def is_valid_email(value):
    return "@" in value
"""

DEMO_AFTER = """def is_valid_email(value):
    value = value.strip()
    return bool(value) and "@" in value
"""

DEMO_CREATED_AT = "2026-06-18T17:00:00Z"


@dataclass
class RoomMessage:
    sender: str
    mention: str
    message_type: str
    content: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProofPacket:
    task_id: str
    title: str
    what_wrong: str
    why_it_matters: str
    how_to_fix: str
    scoped_files: list[str]
    simulated_diff: str
    validation_summary: dict[str, Any]
    safe_to_apply: bool
    human_action: str
    decision_reason: str
    created_at: str


class BandRoom:
    """Band-style local room with @mention routing and transcript capture."""

    def __init__(self, room_id: str) -> None:
        self.room_id = room_id
        self.messages: list[RoomMessage] = []

    def send(
        self,
        sender: str,
        mention: str,
        content: str,
        message_type: str = "text",
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.messages.append(
            RoomMessage(
                sender=sender,
                mention=mention,
                message_type=message_type,
                content=content,
                payload=payload or {},
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "room_id": self.room_id,
            "routing_model": "@mention",
            "messages": [asdict(message) for message in self.messages],
        }


class PlannerAgent:
    handle = "@itz1508/planner"

    def run(self, room: BandRoom, request: str) -> dict[str, Any]:
        plan = {
            "task_id": "proofgate-login-validator",
            "title": "Reject whitespace-only login emails",
            "request": request,
            "scoped_files": ["demo_repo/auth.py"],
            "success_criteria": [
                "Whitespace-only values are rejected",
                "Valid emails still pass",
                "Patch stays inside demo_repo/auth.py",
            ],
        }
        room.send(
            self.handle,
            "@itz1508/engineer",
            "Scope approved. Produce the smallest patch candidate.",
            "task",
            plan,
        )
        return plan


class EngineerAgent:
    handle = "@itz1508/engineer"

    def run(self, room: BandRoom, plan: dict[str, Any]) -> dict[str, Any]:
        diff = "\n".join(
            difflib.unified_diff(
                DEMO_BEFORE.splitlines(),
                DEMO_AFTER.splitlines(),
                fromfile="demo_repo/auth.py.before",
                tofile="demo_repo/auth.py.after",
                lineterm="",
            )
        )
        patch = {
            "scoped_files": plan["scoped_files"],
            "before_sha256": _sha256(DEMO_BEFORE),
            "after_sha256": _sha256(DEMO_AFTER),
            "diff": diff,
        }
        room.send(
            self.handle,
            "@itz1508/tester",
            "Patch candidate ready. Validate behavior and scope.",
            "tool_result",
            patch,
        )
        return patch


class TesterAgent:
    handle = "@itz1508/tester"

    def run(self, room: BandRoom, plan: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
        validation = {
            "tests_run": [
                {"name": "rejects_blank_email", "status": "passed"},
                {"name": "rejects_whitespace_email", "status": "passed"},
                {"name": "accepts_normal_email", "status": "passed"},
                {"name": "scope_limited_to_auth_py", "status": "passed"},
            ],
            "before_sha256": patch["before_sha256"],
            "after_sha256": patch["after_sha256"],
            "all_tests_passed": True,
            "scope_ok": patch["scoped_files"] == plan["scoped_files"],
        }
        room.send(
            self.handle,
            "@itz1508/reviewer",
            "Validation passed. Review proof packet readiness.",
            "tool_result",
            validation,
        )
        return validation


class ReviewerAgent:
    handle = "@itz1508/reviewer"

    def run(
        self,
        room: BandRoom,
        plan: dict[str, Any],
        patch: dict[str, Any],
        validation: dict[str, Any],
    ) -> ProofPacket:
        safe_to_apply = bool(validation["all_tests_passed"] and validation["scope_ok"])
        packet = ProofPacket(
            task_id=plan["task_id"],
            title=plan["title"],
            what_wrong="The login validator accepts whitespace-only values because it checks only for an at sign.",
            why_it_matters="A weak validator lets invalid identity input pass into downstream login and account flows.",
            how_to_fix="Trim the email value, reject empty strings, and keep the existing at-sign check.",
            scoped_files=plan["scoped_files"],
            simulated_diff=patch["diff"],
            validation_summary=validation,
            safe_to_apply=safe_to_apply,
            human_action="approve_or_reject",
            decision_reason=(
                "Patch stayed inside scope and validation passed."
                if safe_to_apply
                else "Patch is blocked until scope and validation both pass."
            ),
            created_at=DEMO_CREATED_AT,
        )
        room.send(
            self.handle,
            "@itz1508",
            "Proof packet ready for human apply decision.",
            "task",
            asdict(packet),
        )
        return packet


def run_demo() -> tuple[dict[str, Any], dict[str, Any]]:
    """Run the full local multi-agent demo and return transcript plus proof."""
    room = BandRoom("proofgate-demo-room")
    request = "Fix a login validator so whitespace-only emails are rejected."
    room.send("@itz1508", "@itz1508/planner", request, "text", {"intent": "code_change"})

    plan = PlannerAgent().run(room, request)
    patch = EngineerAgent().run(room, plan)
    validation = TesterAgent().run(room, plan, patch)
    proof = ReviewerAgent().run(room, plan, patch, validation)

    return room.to_dict(), asdict(proof)


def write_demo(output_dir: Path) -> dict[str, Path]:
    """Write transcript and proof packet for the static dashboard."""
    transcript, proof = run_demo()
    output_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = output_dir / "band_transcript.sample.json"
    proof_path = output_dir / "proof_packet.sample.json"
    transcript_path.write_text(json.dumps(transcript, indent=2), encoding="utf-8")
    proof_path.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    return {"transcript": transcript_path, "proof": proof_path}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
