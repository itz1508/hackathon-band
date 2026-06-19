"""Local process supervisor for the five ProofGate Band remote agents."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AGENT_ROLES = ("intake", "planner", "resolution", "issue-isolator", "finalizing")
DEFAULT_START_TIMEOUT = 20.0
DEFAULT_RESTART_LIMIT = 1


@dataclass
class AgentProcess:
    role: str
    process: subprocess.Popen | None = None
    pid: int | None = None
    started_at: str | None = None
    restart_count: int = 0
    externally_managed: bool = False


class AgentSupervisor:
    """Start, track, and terminate the five remote-agent processes."""

    def __init__(
        self,
        *,
        working_dir: Path | None = None,
        start_timeout: float = DEFAULT_START_TIMEOUT,
        restart_limit: int = DEFAULT_RESTART_LIMIT,
    ) -> None:
        self.working_dir = working_dir or Path(__file__).resolve().parents[1]
        self.start_timeout = start_timeout
        self.restart_limit = restart_limit
        self._agents: dict[str, AgentProcess] = {}

    def start_all(self) -> list[dict[str, Any]]:
        """Launch all five agent processes. Returns status for each."""
        results = []
        for role in AGENT_ROLES:
            result = self._start_role(role)
            results.append(result)
        return results

    def _start_role(self, role: str) -> dict[str, Any]:
        """Start a single agent process if not already running."""
        existing = self._agents.get(role)
        if existing and existing.process and existing.process.poll() is None:
            return {"role": role, "status": "already_running", "pid": existing.pid}

        cmd = [sys.executable, "-m", "proofgate.remote_agent", role]
        log_dir = Path(tempfile.gettempdir()) / "proofgate-agents"
        log_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = log_dir / f"{role}.stdout.log"
        stderr_path = log_dir / f"{role}.stderr.log"
        try:
            with stdout_path.open("a", encoding="utf-8") as stdout_log, stderr_path.open("a", encoding="utf-8") as stderr_log:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(self.working_dir),
                    stdout=stdout_log,
                    stderr=stderr_log,
                    text=True,
                )
            # Brief check that process didn't immediately exit
            time.sleep(0.5)
            if proc.poll() is not None:
                stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
                return {"role": role, "status": "failed", "error": stderr.strip()[:500]}

            now = datetime.now(timezone.utc).isoformat()
            self._agents[role] = AgentProcess(
                role=role,
                process=proc,
                pid=proc.pid,
                started_at=now,
            )
            return {"role": role, "status": "started", "pid": proc.pid}
        except Exception as exc:
            return {"role": role, "status": "failed", "error": str(exc)[:500]}

    def restart_role(self, role: str) -> dict[str, Any]:
        """Attempt one bounded restart for a failed role (pre-run only)."""
        existing = self._agents.get(role)
        if existing and existing.restart_count >= self.restart_limit:
            return {"role": role, "status": "restart_limit_reached"}
        if existing:
            existing.restart_count += 1
        result = self._start_role(role)
        return result

    def status(self) -> list[dict[str, Any]]:
        """Return status of all supervised agents."""
        statuses = []
        for role in AGENT_ROLES:
            agent = self._agents.get(role)
            if agent is None:
                statuses.append({"role": role, "running": False, "pid": None})
            elif agent.process and agent.process.poll() is None:
                statuses.append({"role": role, "running": True, "pid": agent.pid, "started_at": agent.started_at})
            else:
                statuses.append({"role": role, "running": False, "pid": agent.pid, "exited": True})
        return statuses

    def all_running(self) -> bool:
        """Check if all five agents are alive."""
        for role in AGENT_ROLES:
            agent = self._agents.get(role)
            if agent is None or agent.process is None or agent.process.poll() is not None:
                return False
        return True

    def failed_roles(self) -> list[str]:
        """Return roles that are not running."""
        failed = []
        for role in AGENT_ROLES:
            agent = self._agents.get(role)
            if agent is None or agent.process is None or agent.process.poll() is not None:
                failed.append(role)
        return failed

    def stop_all(self, timeout: float = 5.0) -> None:
        """Terminate all owned child processes."""
        for role in AGENT_ROLES:
            agent = self._agents.get(role)
            if agent and agent.process and agent.process.poll() is None:
                agent.process.terminate()
        # Wait for graceful exit
        deadline = time.monotonic() + timeout
        for role in AGENT_ROLES:
            agent = self._agents.get(role)
            if agent and agent.process:
                remaining = max(0.1, deadline - time.monotonic())
                try:
                    agent.process.wait(timeout=remaining)
                except subprocess.TimeoutExpired:
                    agent.process.kill()
        self._agents.clear()
