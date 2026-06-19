"""Centralized settings for ProofGate. Non-secret defaults live here.

Secret and environment-specific values are read only from os.environ (sourced from .env).
"""
from __future__ import annotations

import os

# --- Repository defaults (non-secret, stable) ---

PROOFGATE_HOST = "127.0.0.1"
PROOFGATE_PORT = 8080
PROOFGATE_CHAT_MODE = "local"  # "local" | "recorded"
BAND_API_BASE_URL = "https://app.band.ai/api/v1"
BAND_INTAKE_HANDLE = "itz1508/intake"
PROOFGATE_AUTOSTART_AGENTS = True
PROOFGATE_AGENT_START_TIMEOUT_SECONDS = 20
PROOFGATE_AGENT_RESTART_LIMIT = 1


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _env_bool(key: str, default: bool) -> bool:
    return _env(key, str(default)).lower() in ("true", "1", "yes")


def _env_int(key: str, default: int) -> int:
    try:
        return int(_env(key, str(default)))
    except ValueError:
        return default


# --- Resolved settings (env overrides defaults) ---

def host() -> str:
    return _env("PROOFGATE_HOST", PROOFGATE_HOST)


def port() -> int:
    return _env_int("PROOFGATE_PORT", PROOFGATE_PORT)


def local_url() -> str:
    return f"http://{host()}:{port()}"


def chat_mode() -> str:
    return _env("PROOFGATE_CHAT_MODE", PROOFGATE_CHAT_MODE)


def band_api_base_url() -> str:
    return _env("BAND_API_BASE_URL", BAND_API_BASE_URL)


def band_intake_handle() -> str:
    return _env("BAND_INTAKE_HANDLE", BAND_INTAKE_HANDLE)


def autostart_agents() -> bool:
    return _env_bool("PROOFGATE_AUTOSTART_AGENTS", PROOFGATE_AUTOSTART_AGENTS)


def agent_start_timeout() -> float:
    return float(_env_int("PROOFGATE_AGENT_START_TIMEOUT_SECONDS", PROOFGATE_AGENT_START_TIMEOUT_SECONDS))


def agent_restart_limit() -> int:
    return _env_int("PROOFGATE_AGENT_RESTART_LIMIT", PROOFGATE_AGENT_RESTART_LIMIT)


# --- Environment-only values (no defaults, must be configured) ---

def band_human_api_key() -> str:
    return _env("BAND_HUMAN_API_KEY")


def band_intake_api_key() -> str:
    return _env("BAND_INTAKE_API_KEY")


def band_sender_handle() -> str:
    return _env("BAND_SENDER_HANDLE", "itz1508/human")


def band_room_id() -> str:
    return _env("BAND_ROOM_ID")


def band_intake_participant_id() -> str:
    return _env("BAND_INTAKE_PARTICIPANT_ID")
