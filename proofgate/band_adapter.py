"""Band SDK integration boundary.

The local demo does not require credentials. For a live Band room, create
external agents in Band, store credentials outside git, then wire each role to
Band's SDK using the same role handles used by the local room.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class BandAgentConfig:
    role: str
    handle: str
    agent_id_env: str
    api_key_env: str


BAND_AGENTS = [
    BandAgentConfig("planner", "@itz1508/planner", "BAND_PLANNER_AGENT_ID", "BAND_PLANNER_API_KEY"),
    BandAgentConfig("engineer", "@itz1508/engineer", "BAND_ENGINEER_AGENT_ID", "BAND_ENGINEER_API_KEY"),
    BandAgentConfig("tester", "@itz1508/tester", "BAND_TESTER_AGENT_ID", "BAND_TESTER_API_KEY"),
    BandAgentConfig("reviewer", "@itz1508/reviewer", "BAND_REVIEWER_AGENT_ID", "BAND_REVIEWER_API_KEY"),
]


@dataclass(frozen=True)
class BandToolContract:
    service: str
    purpose: str
    required_for: str
    payload_shape: dict[str, Any]


BAND_TOOL_CONTRACTS = [
    BandToolContract(
        service="list_available_participants_service",
        purpose="Find Planner, Engineer, Tester, and Reviewer external agents before adding them to the room.",
        required_for="room_bootstrap",
        payload_shape={"page": 1, "page_size": 50},
    ),
    BandToolContract(
        service="add_participant_service",
        purpose="Add the missing ProofGate role agent to the active Band chat room.",
        required_for="room_bootstrap",
        payload_shape={"chat_id": "<band_chat_id>", "participant_id": "<agent_or_user_id>"},
    ),
    BandToolContract(
        service="list_chat_participants_service",
        purpose="Verify that Human, Planner, Engineer, Tester, and Reviewer are present before work starts.",
        required_for="room_bootstrap",
        payload_shape={"chat_id": "<band_chat_id>"},
    ),
    BandToolContract(
        service="send_direct_message_service",
        purpose="Send the next structured handoff to exactly the mentioned participant.",
        required_for="agent_handoff",
        payload_shape={
            "chat_id": "<band_chat_id>",
            "participant_id": "<target_participant_id>",
            "message": "@itz1508/engineer <structured payload>",
        },
    ),
    BandToolContract(
        service="remove_participant_service",
        purpose="Remove a role only after the demo or when replacing a failed participant.",
        required_for="cleanup_or_recovery",
        payload_shape={"chat_id": "<band_chat_id>", "participant_id": "<agent_or_user_id>"},
    ),
]


LIVE_HANDOFFS = [
    {
        "from": "@itz1508",
        "to": "@itz1508/planner",
        "service": "send_direct_message_service",
        "message": "@itz1508/planner Fix a login validator so whitespace-only emails are rejected.",
    },
    {
        "from": "@itz1508/planner",
        "to": "@itz1508/engineer",
        "service": "send_direct_message_service",
        "message": "@itz1508/engineer Scope approved. Produce the smallest patch candidate.",
    },
    {
        "from": "@itz1508/engineer",
        "to": "@itz1508/tester",
        "service": "send_direct_message_service",
        "message": "@itz1508/tester Patch candidate ready. Validate behavior and scope.",
    },
    {
        "from": "@itz1508/tester",
        "to": "@itz1508/reviewer",
        "service": "send_direct_message_service",
        "message": "@itz1508/reviewer Validation passed. Review proof packet readiness.",
    },
    {
        "from": "@itz1508/reviewer",
        "to": "@itz1508",
        "service": "send_direct_message_service",
        "message": "@itz1508 Proof packet ready for approve/reject.",
    },
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


def describe_band_tool_contracts() -> list[dict[str, Any]]:
    """Return the Band platform tools ProofGate expects in a live room."""
    return [asdict(contract) for contract in BAND_TOOL_CONTRACTS]


def describe_live_handoffs() -> list[dict[str, str]]:
    """Return the expected live Band handoff sequence for the demo video."""
    return LIVE_HANDOFFS
