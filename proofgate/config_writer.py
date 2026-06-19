"""Write ignored Band SDK config from local environment variables."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

ROLE_ENV = {
    "intake": (("BAND_INTAKE_AGENT_ID",), ("BAND_INTAKE_API_KEY",)),
    "planner": (("BAND_PLANNER_AGENT_ID",), ("BAND_PLANNER_API_KEY",)),
    "resolution": (("BAND_RESOLUTION_AGENT_ID", "BAND_ENGINEER_AGENT_ID"), ("BAND_RESOLUTION_API_KEY", "BAND_ENGINEER_API_KEY")),
    "issue-isolator": (("BAND_ISSUE_ISOLATOR_AGENT_ID",), ("BAND_ISSUE_ISOLATOR_API_KEY",)),
    "finalizing": (("BAND_FINALIZING_AGENT_ID", "BAND_REVIEWER_AGENT_ID"), ("BAND_FINALIZING_API_KEY", "BAND_REVIEWER_API_KEY")),
}


def _first(names: tuple[str, ...]) -> str:
    return next((os.getenv(name, "") for name in names if os.getenv(name)), "")


def build_agent_config() -> str:
    lines: list[str] = []
    missing: list[str] = []
    for role, (id_names, key_names) in ROLE_ENV.items():
        agent_id, api_key = _first(id_names), _first(key_names)
        if not agent_id:
            missing.append(" or ".join(id_names))
        if not api_key:
            missing.append(" or ".join(key_names))
        lines.extend((f"{role}:", f'  agent_id: "{agent_id}"', f'  api_key: "{api_key}"', ""))
    if missing:
        raise ValueError("Missing required environment values: " + ", ".join(missing))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate local Band agent config.")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--output", default="agent_config.yaml")
    args = parser.parse_args()
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(args.env_file))
    except ImportError:
        pass
    Path(args.output).write_text(build_agent_config(), encoding="utf-8")
    print(f"wrote={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
