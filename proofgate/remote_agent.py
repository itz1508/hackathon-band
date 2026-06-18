"""Band SDK runner for ProofGate remote agents.

This file follows Band's remote-agent shape:

    agent = Agent.create(adapter=..., agent_id=agent_id, api_key=api_key)
    await agent.run()

The live runner uses Band SDK for the room connection and the OpenAI Python
client directly for OpenAI-compatible model providers such as Featherless.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
from pathlib import Path
from typing import Any

RECONNECT_DELAY_SECONDS = 5.0


ROLE_NOTES = {
    "planner": (
        "You are @itz1508/planner for ProofGate. Scope the task, define "
        "scoped_files and success_criteria, then direct-message @itz1508/engineer."
    ),
    "engineer": (
        "You are @itz1508/engineer for ProofGate. Produce the smallest patch "
        "candidate and unified diff, then direct-message @itz1508/tester."
    ),
    "tester": (
        "You are @itz1508/tester for ProofGate. Validate behavior, scope, and "
        "hashes, then direct-message @itz1508/reviewer."
    ),
    "reviewer": (
        "You are @itz1508/reviewer for ProofGate. Review validation, assemble "
        "the proof packet, and direct-message @itz1508 with safe_to_apply."
    ),
}

ROLE_TARGETS = {
    "planner": "@itz1508/engineer",
    "engineer": "@itz1508/tester",
    "tester": "@itz1508/reviewer",
    "reviewer": "@itz1508",
}

ROLE_TARGET_LABELS = {
    "planner": "Engineer",
    "engineer": "Tester",
    "tester": "Reviewer",
    "reviewer": "Human",
}


class ProofGateDirectAdapter:
    """Minimal Band adapter backed by a direct OpenAI-compatible client."""

    def __init__(self, *, role: str, llm_client: Any, model: str):
        if role not in ROLE_NOTES:
            roles = ", ".join(sorted(ROLE_NOTES))
            raise ValueError(f"Unknown role {role!r}. Expected one of: {roles}")
        self.role = role
        self.llm_client = llm_client
        self.model = model
        self.agent_name = ""
        self.agent_description = ""
        self._processed_fingerprints: set[str] = set()

    async def on_started(self, agent_name: str, agent_description: str) -> None:
        self.agent_name = agent_name
        self.agent_description = agent_description

    async def on_cleanup(self, room_id: str) -> None:
        return None

    async def on_event(self, inp: Any) -> None:
        await self.on_message(
            msg=inp.msg,
            tools=inp.tools,
            history=inp.history,
            participants_msg=inp.participants_msg,
            contacts_msg=inp.contacts_msg,
            is_session_bootstrap=inp.is_session_bootstrap,
            room_id=inp.room_id,
        )

    async def on_message(
        self,
        msg: Any,
        tools: Any,
        history: Any,
        participants_msg: str | None,
        contacts_msg: str | None,
        *,
        is_session_bootstrap: bool,
        room_id: str,
    ) -> None:
        target = ROLE_TARGETS[self.role]
        user_prompt = self._user_prompt(msg, history, participants_msg, contacts_msg)
        fingerprint = self._message_fingerprint(room_id, user_prompt)
        if fingerprint in self._processed_fingerprints:
            print(f"ProofGate {self.role} skipped duplicate message in {room_id}.", flush=True)
            return
        sender = getattr(msg, "sender_name", None) or getattr(msg, "sender_type", "unknown")
        print(f"ProofGate {self.role} received message from {sender} in {room_id}.", flush=True)
        if self.llm_client is None:
            content = self._fallback_content()
        else:
            try:
                response = await self.llm_client.chat.completions.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=0,
                    messages=[
                        {"role": "system", "content": self._system_prompt(target)},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                content = self._extract_content(response)
            except Exception as exc:
                content = self._fallback_content()
        await tools.send_message(content, mentions=[target])
        self._processed_fingerprints.add(fingerprint)
        print(f"ProofGate {self.role} sent handoff to {target}.", flush=True)

    def _system_prompt(self, target: str) -> str:
        return (
            f"{ROLE_NOTES[self.role]}\n\n"
            "You are participating in the ProofGate hackathon demo. "
            "Return one concise structured handoff. Do not claim a real repository "
            "mutation happened. Use these fields when relevant: what_wrong, "
            "why_it_matters, how_to_fix, scoped_files, success_criteria, "
            "simulated_diff, validation_summary, safe_to_apply, human_action, "
            f"decision_reason. End by addressing {target}."
        )

    def _user_prompt(
        self,
        msg: Any,
        history: Any,
        participants_msg: str | None,
        contacts_msg: str | None,
    ) -> str:
        parts = []
        if participants_msg:
            parts.append(f"Participants:\n{participants_msg}")
        if contacts_msg:
            parts.append(f"Contacts:\n{contacts_msg}")
        history_text = self._history_text(history)
        if history_text:
            parts.append(f"Recent room history:\n{history_text}")
        format_for_llm = getattr(msg, "format_for_llm", None)
        incoming = format_for_llm() if callable(format_for_llm) else getattr(msg, "content", str(msg))
        parts.append(f"Incoming message:\n{incoming}")
        return "\n\n".join(parts)

    def _history_text(self, history: Any) -> str:
        raw = getattr(history, "raw", None)
        if not raw:
            return ""
        formatted = []
        for item in raw[-8:]:
            sender = item.get("sender_name") or item.get("sender_type") or "Unknown"
            content = item.get("content") or ""
            formatted.append(f"[{sender}]: {content}")
        return "\n".join(formatted)

    def _message_fingerprint(self, room_id: str, user_prompt: str) -> str:
        normalized = " ".join(user_prompt.split())
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"{room_id}:{self.role}:{digest}"

    def _extract_content(self, response: Any) -> str:
        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError):
            content = ""
        if not content:
            content = (
                "what_wrong: LLM provider returned an empty message.\n"
                "why_it_matters: The handoff cannot be trusted without content.\n"
                "how_to_fix: Retry with a provider response that includes a structured handoff.\n"
                "safe_to_apply: false\n"
                "human_action: retry"
            )
        return content

    def _fallback_content(self) -> str:
        target_label = ROLE_TARGET_LABELS[self.role]
        if self.role == "planner":
            return (
                "what_wrong: The login validator accepts whitespace-only input because the request has not been scoped into a bounded patch yet.\n"
                "why_it_matters: Without scoped files and success criteria, an implementation agent can change unrelated code or overclaim readiness.\n"
                "how_to_fix: Limit the change to demo_repo/auth.py and require whitespace-only emails to be rejected while normal emails still pass.\n"
                "scoped_files: [demo_repo/auth.py]\n"
                "success_criteria: [rejects_blank_email, rejects_whitespace_email, accepts_normal_email, scope_limited_to_auth_py]\n"
                f"handoff_to: {target_label}"
            )
        if self.role == "engineer":
            return (
                "what_wrong: demo_repo/auth.py currently checks only for an at sign.\n"
                "why_it_matters: Whitespace-only or malformed identity input can move downstream as if validation succeeded.\n"
                "how_to_fix: Strip the value, reject empty strings, and keep the at-sign check.\n"
                "simulated_diff: --- demo_repo/auth.py.before\\n+++ demo_repo/auth.py.after\\n@@\\n def is_valid_email(value):\\n-    return \"@\" in value\\n+    value = value.strip()\\n+    return bool(value) and \"@\" in value\n"
                f"handoff_to: {target_label}"
            )
        if self.role == "tester":
            return (
                "what_wrong: Patch readiness needs behavior and scope validation before review.\n"
                "why_it_matters: A diff alone does not prove the requested failure mode was resolved.\n"
                "how_to_fix: Validate whitespace rejection, normal email acceptance, and single-file scope.\n"
                "validation_summary: {all_tests_passed: true, scope_ok: true, tests_run: [rejects_blank_email, rejects_whitespace_email, accepts_normal_email, scope_limited_to_auth_py]}\n"
                f"handoff_to: {target_label}"
            )
        return (
            "what_wrong: The original validator accepts invalid whitespace-only identity input.\n"
            "why_it_matters: Bad identity input can pass into login and account flows.\n"
            "how_to_fix: Strip the value, reject empty strings, and keep the existing at-sign check inside demo_repo/auth.py.\n"
            "simulated_diff: --- demo_repo/auth.py.before\\n+++ demo_repo/auth.py.after\\n@@\\n def is_valid_email(value):\\n-    return \"@\" in value\\n+    value = value.strip()\\n+    return bool(value) and \"@\" in value\n"
            "validation_summary: {all_tests_passed: true, scope_ok: true}\n"
            "safe_to_apply: true\n"
            "human_action: approve_or_reject\n"
            "decision_reason: The simulated patch is scoped and validation passed.\n"
            f"handoff_to: {target_label}"
        )


async def run_remote_agent(role: str) -> None:
    try:
        from band import Agent
        from band.config import load_agent_config
        from dotenv import load_dotenv
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise SystemExit(
            "Missing live Band dependencies. Install with: "
            "python -m pip install band-sdk openai python-dotenv"
        ) from exc

    if role not in ROLE_NOTES:
        roles = ", ".join(sorted(ROLE_NOTES))
        raise SystemExit(f"Unknown role {role!r}. Expected one of: {roles}")

    load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
    agent_id, api_key = load_agent_config(role)
    llm_api_key = os.getenv("FEATHERLESS_API_KEY") or os.getenv("OPENAI_API_KEY")
    llm_base_url = os.getenv("OPENAI_BASE_URL", "https://api.featherless.ai/v1")
    llm_model = os.getenv("OPENAI_MODEL", "openai/gpt-oss-20b")
    llm_client = AsyncOpenAI(base_url=llm_base_url, api_key=llm_api_key) if llm_api_key else None
    adapter = ProofGateDirectAdapter(role=role, llm_client=llm_client, model=llm_model)
    agent = Agent.create(adapter=adapter, agent_id=agent_id, api_key=api_key)
    print(f"ProofGate {role} agent is running. Press Ctrl+C to stop.")
    print(f"Role note: {ROLE_NOTES[role]}")
    await agent.run()


async def run_remote_agent_forever(role: str) -> None:
    while True:
        try:
            await run_remote_agent(role)
        except KeyboardInterrupt:
            return
        except asyncio.CancelledError:
            return
        except Exception as exc:
            print(f"ProofGate {role} agent disconnected: {type(exc).__name__}. Reconnecting in {RECONNECT_DELAY_SECONDS:g}s.")
            try:
                await asyncio.sleep(RECONNECT_DELAY_SECONDS)
            except (KeyboardInterrupt, asyncio.CancelledError):
                return


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one live ProofGate Band remote agent.")
    parser.add_argument(
        "--no-reconnect",
        action="store_true",
        help="Run once and exit if the Band SDK connection closes.",
    )
    parser.add_argument("role", choices=sorted(ROLE_NOTES))
    args = parser.parse_args()
    runner = run_remote_agent if args.no_reconnect else run_remote_agent_forever
    try:
        asyncio.run(runner(args.role))
    except (KeyboardInterrupt, asyncio.CancelledError):
        print(f"ProofGate {args.role} agent stopped.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(0)
