"""Write ignored Band SDK config from local environment variables."""
from __future__ import annotations

import argparse
import os
from pathlib import Path


ROLE_ENV = {
    "planner": ("BAND_PLANNER_AGENT_ID", "BAND_PLANNER_API_KEY"),
    "engineer": ("BAND_ENGINEER_AGENT_ID", "BAND_ENGINEER_API_KEY"),
    "tester": ("BAND_TESTER_AGENT_ID", "BAND_TESTER_API_KEY"),
    "reviewer": ("BAND_REVIEWER_AGENT_ID", "BAND_REVIEWER_API_KEY"),
    "issue-isolator": ("BAND_ISSUE_ISOLATOR_AGENT_ID", "BAND_ISSUE_ISOLATOR_API_KEY"),
}


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip())


def build_agent_config() -> str:
    missing: list[str] = []
    lines: list[str] = []
    for role, (agent_id_env, api_key_env) in ROLE_ENV.items():
        agent_id = os.environ.get(agent_id_env, "")
        api_key = os.environ.get(api_key_env, "")
        if not agent_id:
            missing.append(agent_id_env)
        if not api_key:
            missing.append(api_key_env)
        lines.extend([
            f"{role}:",
            f"  agent_id: \"{agent_id}\"",
            f"  api_key: \"{api_key}\"",
            "",
        ])

    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing required environment values: {joined}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate local agent_config.yaml for Band SDK.")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--output", default="agent_config.yaml")
    args = parser.parse_args()

    load_dotenv(Path(args.env_file))
    content = build_agent_config()
    output = Path(args.output)
    output.write_text(content, encoding="utf-8")
    print(f"wrote={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
