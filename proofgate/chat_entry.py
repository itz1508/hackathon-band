"""Transform normal human text into a valid Band message targeting Intake."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

MAX_INPUT_LENGTH = 2000
DEFAULT_INTAKE_HANDLE = "itz1508/intake"
DEFAULT_INTAKE_NAME = "Intake Agent"


@dataclass(frozen=True)
class PreparedBandMessage:
    """Ready-to-send Band message with content and mention metadata."""
    display_text: str
    band_content: str
    target_handle: str
    mentions: list[dict[str, str]] = field(default_factory=list)


class ChatEntryError(ValueError):
    """Raised when input text cannot be prepared."""


def prepare_intake_message(
    text: str,
    intake_handle: str = DEFAULT_INTAKE_HANDLE,
    intake_participant_id: str = "",
    intake_name: str = DEFAULT_INTAKE_NAME,
) -> PreparedBandMessage:
    """Convert normal user text into a Band message with Intake mention.

    The output includes both the visible @mention in content and the structured
    mentions array with the participant UUID. Band requires both.

    Rules:
    - Trims whitespace
    - Rejects empty input
    - Enforces length limit
    - Removes duplicate @intake prefix if user typed it
    - Adds exactly one @handle prefix
    - Includes mention metadata with configured UUID
    - Never broadcasts to all agents
    """
    if not isinstance(text, str):
        raise ChatEntryError("Input must be a string")

    cleaned = text.strip()
    if not cleaned:
        raise ChatEntryError("Input text is empty")

    if len(cleaned) > MAX_INPUT_LENGTH:
        raise ChatEntryError(f"Input exceeds {MAX_INPUT_LENGTH} characters")

    if not intake_participant_id:
        raise ChatEntryError("Intake participant ID is required for mention metadata")

    # Remove existing @intake prefix to avoid duplication
    at_handle = f"@{intake_handle}"
    pattern = re.compile(rf"^\s*@?{re.escape(intake_handle)}\s*", re.IGNORECASE)
    display_text = pattern.sub("", cleaned).strip()

    # If stripping the prefix left nothing, use the original cleaned text
    if not display_text:
        display_text = cleaned

    # Construct Band content with exactly one mention prefix
    band_content = f"{at_handle} {display_text}"

    mentions = [{
        "id": intake_participant_id,
        "handle": intake_handle,
        "name": intake_name,
    }]

    return PreparedBandMessage(
        display_text=display_text,
        band_content=band_content,
        target_handle=intake_handle,
        mentions=mentions,
    )
