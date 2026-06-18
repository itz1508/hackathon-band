"""Band SDK integration boundary.

The local demo does not require credentials. For a live Band room, create
external agents in Band, store credentials outside git, then wire each role to
Band's SDK using the same role handles used by the local room.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BandAgentConfig:
    role: str
    handle: str
    agent_id_env: str
    api_key_env: str


BAND_AGENTS = [
    BandAgentConfig("planner", "@Planner", "BAND_PLANNER_AGENT_ID", "BAND_PLANNER_API_KEY"),
    BandAgentConfig("engineer", "@Engineer", "BAND_ENGINEER_AGENT_ID", "BAND_ENGINEER_API_KEY"),
    BandAgentConfig("tester", "@Tester", "BAND_TESTER_AGENT_ID", "BAND_TESTER_API_KEY"),
    BandAgentConfig("reviewer", "@Reviewer", "BAND_REVIEWER_AGENT_ID", "BAND_REVIEWER_API_KEY"),
]


def describe_live_band_setup() -> list[dict[str, str]]:
    """Return the environment contract needed to attach real Band agents."""
    return [
        {
            "role": config.role,
            "handle": config.handle,
            "agent_id_env": config.agent_id_env,
            "api_key_env": config.api_key_env,
        }
        for config in BAND_AGENTS
    ]

