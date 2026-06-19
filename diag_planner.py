"""Diagnostic: does Planner receive any Band events?"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from band import Agent
from band.config import load_agent_config


class DiagnosticAdapter:
    def __init__(self):
        self.count = 0

    async def on_started(self, agent_name, agent_description):
        print(f"PLANNER STARTED as: {agent_name}", flush=True)

    async def on_cleanup(self, room_id):
        pass

    async def on_event(self, inp):
        self.count += 1
        raw = getattr(inp.msg, "content", str(inp.msg))
        is_json = raw.strip().startswith("{")
        print(f"EVENT #{self.count} room={inp.room_id} bootstrap={inp.is_session_bootstrap}", flush=True)
        print(f"  content_length: {len(raw)}", flush=True)
        print(f"  is_json: {is_json}", flush=True)
        if is_json:
            import json
            try:
                p = json.loads(raw)
                print(f"  schema: {p.get('schema_version')}", flush=True)
                print(f"  to_role: {p.get('to_role')}", flush=True)
                print(f"  from_role: {p.get('from_role')}", flush=True)
            except Exception as e:
                print(f"  parse_error: {e}", flush=True)
        else:
            print(f"  content_start: {raw[:80]}", flush=True)


async def main():
    agent_id, api_key = load_agent_config("planner")
    print(f"Planner ID: {agent_id}", flush=True)
    adapter = DiagnosticAdapter()
    agent = Agent.create(adapter=adapter, agent_id=agent_id, api_key=api_key)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
