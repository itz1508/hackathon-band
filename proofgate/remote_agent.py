"""Band SDK runner scaffold for ProofGate remote agents.

This file follows Band's remote-agent shape:

    agent = Agent.create(adapter=..., agent_id=agent_id, api_key=api_key)
    await agent.run()

The local demo and tests do not require Band SDK installation. Install the SDK
only when running live remote agents for the hackathon room.
"""
from __future__ import annotations

import argparse
import asyncio
import os


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


async def run_remote_agent(role: str) -> None:
    try:
        from band import Agent
        from band.adapters import LangGraphAdapter
        from band.config import load_agent_config
        from dotenv import load_dotenv
        from langchain_openai import ChatOpenAI
        from langgraph.checkpoint.memory import InMemorySaver
    except ImportError as exc:
        raise SystemExit(
            "Missing live Band dependencies. Install with: "
            'uv add "band-sdk[langgraph]" langchain-openai langgraph python-dotenv'
        ) from exc

    if role not in ROLE_NOTES:
        roles = ", ".join(sorted(ROLE_NOTES))
        raise SystemExit(f"Unknown role {role!r}. Expected one of: {roles}")

    load_dotenv()
    agent_id, api_key = load_agent_config(role)
    llm_api_key = os.getenv("FEATHERLESS_API_KEY") or os.getenv("OPENAI_API_KEY")
    llm_base_url = os.getenv("OPENAI_BASE_URL", "https://api.featherless.ai/v1")
    llm_model = os.getenv("OPENAI_MODEL", "openai/gpt-oss-20b")
    if not llm_api_key:
        raise SystemExit("Missing FEATHERLESS_API_KEY or OPENAI_API_KEY in .env")

    adapter = LangGraphAdapter(
        llm=ChatOpenAI(
            model=llm_model,
            api_key=llm_api_key,
            base_url=llm_base_url,
            temperature=0,
            max_tokens=4096,
        ),
        checkpointer=InMemorySaver(),
    )
    agent = Agent.create(adapter=adapter, agent_id=agent_id, api_key=api_key)
    print(f"ProofGate {role} agent is running. Press Ctrl+C to stop.")
    print(f"Role note: {ROLE_NOTES[role]}")
    await agent.run()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one live ProofGate Band remote agent.")
    parser.add_argument("role", choices=sorted(ROLE_NOTES))
    args = parser.parse_args()
    asyncio.run(run_remote_agent(args.role))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
