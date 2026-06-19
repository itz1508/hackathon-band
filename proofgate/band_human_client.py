"""Band remote-agent sender client for UI ingress and room inspection.

This is a transport adapter only. No workflow routing logic.

The dashboard uses a dedicated remote-agent key and Band's Agent API surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from band.client.rest import (
    AsyncRestClient,
    ChatMessageRequest,
    ChatMessageRequestMentionsItem,
    DEFAULT_REQUEST_OPTIONS,
    ParticipantRequest,
)

DEFAULT_BASE_URL = "https://app.band.ai"


class BandHumanAPIError(RuntimeError):
    """Compatibility error for the dashboard Band sender transport."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(f"Band sender API {status}: {detail}")
        self.status = status
        self.detail = detail


@dataclass
class BandHumanClient:
    """Thin Agent API client used by the local UI sender. No workflow logic."""

    api_key: str
    base_url: str = DEFAULT_BASE_URL

    def _client(self) -> AsyncRestClient:
        return AsyncRestClient(
            api_key=self.api_key,
            base_url=self.base_url.removesuffix("/api/v1"),
        )

    @staticmethod
    def _dict(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if hasattr(value, "model_dump"):
            return value.model_dump()
        return {}

    async def health(self) -> dict[str, Any]:
        """Check remote-agent authentication without exposing identity data."""
        try:
            await self._client().agent_api_identity.get_agent_me(
                request_options=DEFAULT_REQUEST_OPTIONS
            )
            return {"connected": True, "authenticated": True}
        except Exception as exc:
            status = int(getattr(exc, "status_code", 0) or 0)
            return {"connected": bool(status), "authenticated": False, "status": status}

    async def get_room(self, room_id: str) -> dict[str, Any]:
        """Get a room visible to the sender agent."""
        try:
            response = await self._client().agent_api_chats.get_agent_chat(
                room_id, request_options=DEFAULT_REQUEST_OPTIONS
            )
            return self._dict(response.data)
        except Exception as exc:
            raise BandHumanAPIError(
                int(getattr(exc, "status_code", 0) or 0), "room lookup failed"
            ) from exc

    async def list_participants(self, room_id: str) -> list[dict[str, Any]]:
        """List participants visible to the sender agent."""
        try:
            response = await self._client().agent_api_participants.list_agent_chat_participants(
                room_id, request_options=DEFAULT_REQUEST_OPTIONS
            )
            return [self._dict(item) for item in (response.data or [])]
        except Exception as exc:
            raise BandHumanAPIError(
                int(getattr(exc, "status_code", 0) or 0), "participant lookup failed"
            ) from exc

    async def resolve_participant(self, room_id: str, handle: str) -> dict[str, Any] | None:
        """Find a participant by handle in the room (fallback only)."""
        participants = await self.list_participants(room_id)
        expected = handle.lower().lstrip("@")
        for p in participants:
            p_handle = str(p.get("handle", "") or "").lower().lstrip("@")
            if p_handle == expected:
                return p
        return None

    async def validate_participant(self, room_id: str, participant_id: str, expected_handle: str) -> bool:
        """Verify that a configured UUID is present in the room with the expected handle."""
        participants = await self.list_participants(room_id)
        for p in participants:
            p_id = p.get("id", "") or p.get("participant_id", "")
            if p_id == participant_id:
                p_handle = p.get("handle", "") or ""
                return p_handle == expected_handle or expected_handle in p_handle
        return False

    async def send_message(
        self,
        room_id: str,
        content: str,
        mentions: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Send a text message to a room with mentions.

        Band requires both:
        - The @mention in the content string
        - The mentions array with participant UUID
        """
        mention_items = [
            ChatMessageRequestMentionsItem(id=item["id"], handle=item["handle"])
            for item in mentions
        ]
        try:
            response = await self._client().agent_api_messages.create_agent_chat_message(
                chat_id=room_id,
                message=ChatMessageRequest(content=content, mentions=mention_items),
                request_options=DEFAULT_REQUEST_OPTIONS,
            )
            return self._dict(response.data)
        except Exception as exc:
            raise BandHumanAPIError(
                int(getattr(exc, "status_code", 0) or 0), "message delivery failed"
            ) from exc

    async def get_messages(
        self,
        room_id: str,
        after: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Unused compatibility surface; mirrored events are the read path."""
        raise NotImplementedError("Use BandMirror for dashboard event reads")

    async def ensure_room_membership(
        self, room_id: str, member_handle: str, sponsor_api_key: str
    ) -> bool:
        """Use an existing room member to add the UI sender by handle."""
        sponsor = AsyncRestClient(
            api_key=sponsor_api_key,
            base_url=self.base_url.removesuffix("/api/v1"),
        )
        normalized = member_handle.lower().lstrip("@")
        try:
            current = await sponsor.agent_api_participants.list_agent_chat_participants(
                room_id, request_options=DEFAULT_REQUEST_OPTIONS
            )
            for participant in current.data or []:
                data = self._dict(participant)
                if str(data.get("handle", "")).lower().lstrip("@") == normalized:
                    return True

            page = 1
            while True:
                peers = await sponsor.agent_api_peers.list_agent_peers(
                    not_in_chat=room_id,
                    page=page,
                    page_size=100,
                    request_options=DEFAULT_REQUEST_OPTIONS,
                )
                values = peers.data or []
                for peer in values:
                    data = self._dict(peer)
                    if str(data.get("handle", "")).lower().lstrip("@") != normalized:
                        continue
                    participant_id = data.get("id")
                    if not participant_id:
                        return False
                    await sponsor.agent_api_participants.add_agent_chat_participant(
                        room_id,
                        participant=ParticipantRequest(
                            participant_id=str(participant_id), role="member"
                        ),
                        request_options=DEFAULT_REQUEST_OPTIONS,
                    )
                    return True
                if len(values) < 100:
                    return False
                page += 1
        except Exception:
            return False

    async def discover_workflow_room(
        self, sponsor_api_key: str, required_handles: set[str], sender_handle: str
    ) -> str | None:
        """Find the best sponsor-visible room for the canonical workflow."""
        sponsor = AsyncRestClient(
            api_key=sponsor_api_key,
            base_url=self.base_url.removesuffix("/api/v1"),
        )
        required = {value.lower().lstrip("@") for value in required_handles}
        sender = sender_handle.lower().lstrip("@")
        candidates: list[tuple[int, str]] = []
        try:
            rooms = await sponsor.agent_api_chats.list_agent_chats(
                page=1, page_size=100, request_options=DEFAULT_REQUEST_OPTIONS
            )
            for room in rooms.data or []:
                room_data = self._dict(room)
                room_id = room_data.get("id")
                if not room_id:
                    continue
                participants = await sponsor.agent_api_participants.list_agent_chat_participants(
                    str(room_id), request_options=DEFAULT_REQUEST_OPTIONS
                )
                handles = {
                    str(self._dict(item).get("handle", "")).lower().lstrip("@")
                    for item in (participants.data or [])
                }
                matched = len(required & handles)
                if matched == len(required):
                    candidates.append((matched + (1 if sender in handles else 0), str(room_id)))
            if not candidates:
                return None
            candidates.sort(reverse=True)
            return candidates[0][1]
        except Exception:
            return None
