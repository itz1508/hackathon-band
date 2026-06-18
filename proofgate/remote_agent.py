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
    adapter = LangGraphAdapter(
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
        checkpointer=InMemorySaver(),
    )
    agent = Agent.create(adapter=adapter, agent_id=agent_id, api_key=api_key)
    print(f"ProofGate {role} agent is running. Press Ctrl+C to stop.")
    print(f"Role note: {ROLE_NOTES[role]}")
    await agent.run()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one live ProofGate Band remote agent.")
    parser.add_argument("role", choices=sorted(ROLE_SYSTEM_PROMPTS))
    args = parser.parse_args()
    asyncio.run(run_remote_agent(args.role))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
