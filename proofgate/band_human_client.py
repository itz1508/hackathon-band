"""Band Human API client for sending messages and reading room state.

This is a transport adapter only. No workflow routing logic.

Base URL is expected as: https://app.band.ai/api/v1
Human API paths are: /me/chats/{id}/messages, /me/profile, etc.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://app.band.ai/api/v1"


class BandHumanAPIError(RuntimeError):
    """Raised when the Band Human API returns an error."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(f"Band Human API {status}: {detail}")
        self.status = status
        self.detail = detail


@dataclass
class BandHumanClient:
    """Thin HTTP client for Band Human API. No workflow logic."""

    api_key: str
    base_url: str = DEFAULT_BASE_URL

    def _headers(self) -> dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _url(self, path: str) -> str:
        """Build full URL. Path should start with /me/..."""
        return f"{self.base_url}{path}"

    async def health(self) -> dict[str, Any]:
        """Check connectivity and authentication via /me/profile."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(self._url("/me/profile"), headers=self._headers())
            if resp.status_code == 200:
                return {"connected": True, "authenticated": True}
            if resp.status_code in (401, 403):
                return {"connected": True, "authenticated": False, "status": resp.status_code}
            return {"connected": False, "authenticated": False, "status": resp.status_code}

    async def get_room(self, room_id: str) -> dict[str, Any]:
        """Get room details."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(self._url(f"/me/chats/{room_id}"), headers=self._headers())
            if resp.status_code != 200:
                raise BandHumanAPIError(resp.status_code, resp.text)
            return resp.json()

    async def list_participants(self, room_id: str) -> list[dict[str, Any]]:
        """List participants in a room."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                self._url(f"/me/chats/{room_id}/participants"),
                headers=self._headers(),
            )
            if resp.status_code != 200:
                raise BandHumanAPIError(resp.status_code, resp.text)
            data = resp.json()
            if isinstance(data, list):
                return data
            return data.get("participants", data.get("data", []))

    async def resolve_participant(self, room_id: str, handle: str) -> dict[str, Any] | None:
        """Find a participant by handle in the room (fallback only)."""
        participants = await self.list_participants(room_id)
        for p in participants:
            p_handle = p.get("handle", "") or ""
            if p_handle == handle or p_handle.endswith(f"/{handle}"):
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
        payload = {
            "message": {
                "content": content,
                "mentions": mentions,
            }
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                self._url(f"/me/chats/{room_id}/messages"),
                headers=self._headers(),
                json=payload,
            )
            if resp.status_code not in (200, 201):
                raise BandHumanAPIError(resp.status_code, resp.text)
            return resp.json()

    async def get_messages(
        self,
        room_id: str,
        after: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Read messages from a room. Human sees all messages (not mention-filtered)."""
        params: dict[str, Any] = {"limit": limit}
        if after:
            params["after"] = after
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                self._url(f"/me/chats/{room_id}/messages"),
                headers=self._headers(),
                params=params,
            )
            if resp.status_code != 200:
                raise BandHumanAPIError(resp.status_code, resp.text)
            data = resp.json()
            if isinstance(data, list):
                return data
            return data.get("messages", data.get("data", []))
