"""Live Band remote-agent runner using the ProofGate structured packet."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import os
import re
from pathlib import Path
from typing import Any
from uuid import uuid4

from .band_adapter import ROLE_BY_KEY
from .mirror import BandMirror
from .workflow import ROLES, advance, new_packet, stage_result, validate_packet, validate_stage_result

RECONNECT_DELAY_SECONDS = 5.0


def _strip_target_prefix(content: str) -> str:
    """Remove one visible Band mention before parsing a structured packet."""
    mention = r"(?:@\[\[[0-9A-Fa-f-]+\]\]|@[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"
    return re.sub(rf"^{mention}\s+", "", content, count=1).strip()


class ProofGateDirectAdapter:
    def __init__(self, *, role: str, llm_client: Any = None, model: str = "") -> None:
        if role not in ROLES:
            raise ValueError(f"Unknown role {role!r}")
        self.role, self.llm_client, self.model = role, llm_client, model
        self.mirror = BandMirror()
        self._processed: set[str] = set()

    async def on_started(self, agent_name: str, agent_description: str) -> None:
        return None

    async def on_cleanup(self, room_id: str) -> None:
        return None

    async def on_event(self, inp: Any) -> None:
        await self.on_message(inp.msg, inp.tools, inp.history, inp.participants_msg,
                              inp.contacts_msg, is_session_bootstrap=inp.is_session_bootstrap,
                              room_id=inp.room_id)

    async def on_message(self, msg: Any, tools: Any, history: Any = None,
                         participants_msg: str | None = None, contacts_msg: str | None = None,
                         *, is_session_bootstrap: bool = False, room_id: str = "") -> None:
        raw = getattr(msg, "content", msg)
        if not isinstance(raw, str):
            raw = str(raw)
        raw = _strip_target_prefix(raw)
        try:
            packet = json.loads(raw)
        except json.JSONDecodeError:
            if self.role != "intake":
                return  # Silently skip non-JSON messages (human text, etc.)
            constraints = []
            if "[constraint:force_failure]" in raw:
                constraints.append("force_failure")
                raw = raw.replace("[constraint:force_failure]", "").strip()
            packet = new_packet(run_id=str(uuid4()), task_id=str(uuid4()), room_id=room_id,
                                objective=raw, constraints=constraints)
        # Skip packets not addressed to this role
        if packet.get("to_role") != self.role and self.role != "intake":
            return
        validate_packet(packet)
        fingerprint = hashlib.sha256(f"{room_id}:{self.role}:{raw}".encode()).hexdigest()
        if fingerprint in self._processed:
            return
        self.mirror.record_event(event_key=f"{fingerprint}:received", packet=packet,
                                 event_type="received", delivery_state="delivered", content=raw)
        result = await self._produce_result(packet)
        validate_stage_result(result)
        updated = advance(packet, result)
        outgoing = json.dumps(updated, separators=(",", ":"), sort_keys=True)
        outgoing_key = hashlib.sha256(outgoing.encode()).hexdigest()
        self.mirror.record_event(event_key=f"{outgoing_key}:outgoing", packet=updated,
                                 event_type="outgoing", delivery_state="pending", content=outgoing)
        target = ROLE_BY_KEY[updated["to_role"]].handle if updated["to_role"] in ROLE_BY_KEY else "@itz1508"
        wire_content = f"{target} {outgoing}"
        try:
            await tools.send_message(wire_content, mentions=[target])
        except ValueError as ve:
            # Mention failed — target may not be in room. Try adding them first.
            try:
                await tools.add_participant(target)
                await tools.send_message(wire_content, mentions=[target])
            except Exception:
                self.mirror.record_event(event_key=f"{outgoing_key}:failed", packet=updated,
                                         event_type="delivery", delivery_state="failed", content=outgoing)
                raise
        except Exception:
            self.mirror.record_event(event_key=f"{outgoing_key}:failed", packet=updated,
                                     event_type="delivery", delivery_state="failed", content=outgoing)
            raise
        self.mirror.record_event(event_key=f"{outgoing_key}:sent", packet=updated,
                                 event_type="delivery", delivery_state="sent", content=outgoing)
        self._processed.add(fingerprint)

    async def _produce_result(self, packet: dict[str, Any]) -> dict[str, Any]:
        if self.llm_client is None:
            return fallback_result(self.role, packet)
        prompt = (
            f"Act as ProofGate role {self.role}. Return JSON only: one stage_results object. "
            "Every field in proofgate.band.v1 is mandatory. Tool delivery is not role success. "
            f"Input packet: {json.dumps(packet)}"
        )
        try:
            response = await self.llm_client.chat.completions.create(
                model=self.model, temperature=0, max_tokens=4096,
                messages=[{"role": "system", "content": prompt}])
            content = response.choices[0].message.content
            result = json.loads(content)
            result.setdefault("evidence", []).append({"source": "model", "label": "provider_generated"})
            validate_stage_result(result)
            return result
        except Exception as exc:
            result = fallback_result(self.role, packet)
            result["evidence"].append({"source": "fallback", "label": "fallback_generated", "reason": type(exc).__name__})
            return result


def fallback_result(role: str, packet: dict[str, Any]) -> dict[str, Any]:
    prior = packet["stage_results"]
    if role == "intake":
        return stage_result(role, output={"objective": packet["objective"], "constraints": packet["constraints"]},
                            criteria=["objective captured", "constraints captured"], met=["objective captured", "constraints captured"],
                            role_success="Intake converted the human request into a complete bounded task.")
    if role == "planner":
        return stage_result(role, output={"requirements": [packet["objective"]], "risks": []},
                            criteria=["requirements measurable", "scope bounded"], met=["requirements measurable", "scope bounded"],
                            role_success="Plan defined measurable requirements, scope, and risks.")
    if role == "resolution":
        isolation = next((item for item in reversed(prior) if item["stage"] == "issue-isolator"), None)
        met = isolation is not None or not any("force_failure" in str(value) for value in packet["constraints"])
        return stage_result(role, output={"solution": "Structured resolution produced.", "retry_context": isolation},
                            criteria=["solution addresses objective"], met=["solution addresses objective"] if met else [],
                            requirements_met=met, unmet_requirements=[] if met else ["solution addresses objective"],
                            role_success="Resolution produced a solution and assessed every requirement.")
    if role == "issue-isolator":
        failed = next(item for item in reversed(prior) if item["stage"] == "resolution")
        return stage_result(role, output={"recovery": "Address the failed requirement and reassess it."},
                            criteria=["failure explained", "retry actionable"], met=["failure explained", "retry actionable"],
                            role_success="Issue Isolation explained the failure and supplied a focused retry.",
                            failed_stage="resolution", failed_requirement=failed["unmet_requirements"],
                            failure_point="requirement assessment", failure_reason="Resolution reported requirements_met=false.",
                            why_it_matters="Finalizing cannot claim completion with unmet requirements.",
                            missing_information=failed["unmet_requirements"], how_to_overcome="Correct the unmet requirement and provide evidence.",
                            what_success_looks_like="Retry reports requirements_met=true with evidence.",
                            retry_instruction="Retry Resolution once using this isolation context.", failed_resolution=failed)
    if role == "finalizing":
        resolution = next(item for item in reversed(prior) if item["stage"] == "resolution")
        isolated = any(item["stage"] == "issue-isolator" for item in prior)
        met = bool(resolution["requirements_met"])
        outcome = "resolved_after_isolation" if met and isolated else "completed" if met else "blocked"
        successes = {item["stage"]: item["role_success"] for item in prior}
        final = {"outcome": outcome, "objective": packet["objective"], "role_successes": successes,
                 "final_summary": "Workflow finalized from structured Band context.", "resolution": resolution["output"],
                 "evidence": [item["evidence"] for item in prior],
                 "isolation_summary": next((item["output"] for item in prior if item["stage"] == "issue-isolator"), None),
                 "requirements_met": met, "unresolved_items": resolution["unmet_requirements"],
                 "remaining_uncertainty": resolution["remaining_uncertainty"],
                 "recommended_next_step": "Use the final result; no user workflow decision is required."}
        return stage_result(role, output=final, criteria=["all roles represented", "terminal outcome assigned"],
                            met=["all roles represented", "terminal outcome assigned"],
                            role_success="Finalizing synthesized the terminal result and all role contributions.")
    raise ValueError(role)


async def run_remote_agent(role: str) -> None:
    try:
        from band import Agent
        from band.config import load_agent_config
        from dotenv import load_dotenv
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise SystemExit("Missing live dependencies: band-sdk openai python-dotenv") from exc
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    agent_id, api_key = load_agent_config(role)
    key = os.getenv("FEATHERLESS_API_KEY") or os.getenv("OPENAI_API_KEY")
    client = AsyncOpenAI(base_url=os.getenv("OPENAI_BASE_URL", "https://api.featherless.ai/v1"), api_key=key) if key else None
    adapter = ProofGateDirectAdapter(role=role, llm_client=client, model=os.getenv("OPENAI_MODEL", "openai/gpt-oss-20b"))
    await Agent.create(adapter=adapter, agent_id=agent_id, api_key=api_key).run()


async def run_remote_agent_forever(role: str) -> None:
    while True:
        try:
            await run_remote_agent(role)
        except (KeyboardInterrupt, asyncio.CancelledError):
            return
        except Exception as exc:
            print(f"ProofGate {role} disconnected: {_safe_error(exc)}", flush=True)
            await asyncio.sleep(RECONNECT_DELAY_SECONDS)


def _safe_error(exc: Exception) -> str:
    return re.sub(r"(band_[au]_|rc_)[A-Za-z0-9_-]+", "<redacted>", f"{type(exc).__name__}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one ProofGate Band agent.")
    parser.add_argument("--no-reconnect", action="store_true")
    parser.add_argument("role", choices=ROLES)
    args = parser.parse_args()
    asyncio.run((run_remote_agent if args.no_reconnect else run_remote_agent_forever)(args.role))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
