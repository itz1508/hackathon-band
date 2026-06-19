"""Pydantic models for the ProofGate internal chat API."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatStatusResponse(BaseModel):
    mode: Literal["local", "recorded"] = "local"
    band_connected: bool = False
    room_selected: bool = False
    intake_present: bool = False
    intake_handle: str = ""
    agents_expected: int = 5
    agents_running: int = 0
    all_agents_running: bool = False
    send_enabled: bool = False
    room_url: str = ""
    active_run_id: str | None = None
    error: str | None = None


class ChatSendRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    constraints: list[str] = []
    client_request_id: str | None = None


class ChatSendResponse(BaseModel):
    run_id: str | None = None
    message_id: str
    display_text: str
    routed_to: str
    status: Literal["sent", "failed"]
    error: str | None = None


class ChatEvent(BaseModel):
    sequence: int
    timestamp: str
    run_id: str
    sender_role: str = ""
    sender_handle: str = ""
    recipient_role: str = ""
    recipient_handle: str = ""
    stage: str = ""
    event: str = ""
    summary: str = ""
    packet: dict[str, Any] | None = None


class ChatEventsResponse(BaseModel):
    run_id: str
    events: list[ChatEvent] = []
    next_sequence: int = 0
    terminal: bool = False


class ChatRunResponse(BaseModel):
    run_id: str
    objective: str = ""
    constraints: list[str] = []
    outcome: str = ""
    retry_count: int = 0
    roles_participated: list[str] = []
    workflow_path: list[str] = []
    stage_results: dict[str, Any] = {}
    stage_result_sequence: list[dict[str, Any]] = []
    conversation_events: list[ChatEvent] = []
    final_result: dict[str, Any] = {}
    terminal: bool = False
    status: str = "pending"
