"""Deterministic local contract demonstration; not evidence of live Band delivery."""
from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from .remote_agent import fallback_result
from .workflow import advance, new_packet


def run_demo(*, force_isolation: bool = True) -> tuple[dict, dict]:
    packet = new_packet(run_id=str(uuid4()), task_id="demo-task", room_id="local-simulation",
                        objective="Demonstrate structured multi-agent collaboration.",
                        constraints=["force_failure"] if force_isolation else [])
    events = []
    while packet["to_role"] != "human":
        role = packet["to_role"]
        result = fallback_result(role, packet)
        packet = advance(packet, result)
        events.append({"source": "local_simulation", "from_role": role,
                       "to_role": packet["to_role"], "packet": packet})
    return {"source": "local_simulation", "events": events}, packet["final_result"]


def write_demo(output_dir: Path) -> dict[str, Path]:
    transcript, result = run_demo()
    output_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = output_dir / "band_transcript.sample.json"
    result_path = output_dir / "final_result.sample.json"
    transcript_path.write_text(json.dumps(transcript, indent=2), encoding="utf-8")
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return {"transcript": transcript_path, "result": result_path}
