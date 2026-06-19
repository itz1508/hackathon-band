"""Multiprocess-safe SQLite mirror for real Band collaboration events."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def default_database_path() -> Path:
    override = os.getenv("PROOFGATE_MIRROR_DB")
    if override:
        return Path(override)
    root = Path(os.getenv("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return root / "ProofGate" / "band_mirror.sqlite3"


class BandMirror:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else default_database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as db, db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY, room_id TEXT NOT NULL, objective TEXT NOT NULL,
                    current_stage TEXT NOT NULL, retry_count INTEGER NOT NULL,
                    outcome TEXT, packet_json TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, event_key TEXT NOT NULL UNIQUE,
                    run_id TEXT NOT NULL, sequence INTEGER NOT NULL, room_id TEXT NOT NULL,
                    event_type TEXT NOT NULL, from_role TEXT, to_role TEXT, stage TEXT,
                    delivery_state TEXT NOT NULL, content TEXT NOT NULL,
                    packet_json TEXT, created_at TEXT NOT NULL,
                    UNIQUE(run_id, sequence)
                );
                CREATE TABLE IF NOT EXISTS agents (
                    role TEXT PRIMARY KEY, display_name TEXT NOT NULL, handle TEXT NOT NULL,
                    responsibility TEXT NOT NULL
                );
            """)

    def upsert_agent(self, role: str, display_name: str, handle: str, responsibility: str) -> None:
        with closing(self._connect()) as db, db:
            db.execute("INSERT INTO agents VALUES (?, ?, ?, ?) ON CONFLICT(role) DO UPDATE SET display_name=excluded.display_name, handle=excluded.handle, responsibility=excluded.responsibility",
                       (role, display_name, handle, responsibility))

    def record_event(self, *, event_key: str, packet: dict[str, Any], event_type: str,
                     delivery_state: str, content: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(packet, separators=(",", ":"), sort_keys=True)
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT sequence FROM events WHERE event_key=?", (event_key,)).fetchone()
            if existing:
                return int(existing["sequence"])
            sequence = int(db.execute("SELECT COALESCE(MAX(sequence), 0) + 1 AS n FROM events WHERE run_id=?", (packet["run_id"],)).fetchone()["n"])
            db.execute("""INSERT INTO events(event_key,run_id,sequence,room_id,event_type,from_role,to_role,stage,delivery_state,content,packet_json,created_at)
                          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                       (event_key, packet["run_id"], sequence, packet["room_id"], event_type,
                        packet.get("from_role"), packet.get("to_role"), packet.get("current_stage"),
                        delivery_state, content, payload, now))
            outcome = (packet.get("final_result") or {}).get("outcome")
            db.execute("""INSERT INTO runs VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET
                          current_stage=excluded.current_stage,retry_count=excluded.retry_count,outcome=excluded.outcome,
                          packet_json=excluded.packet_json,updated_at=excluded.updated_at""",
                       (packet["run_id"], packet["room_id"], packet["objective"], packet["current_stage"],
                        packet["retry_count"], outcome, payload, now))
            return sequence

    def agents(self) -> list[dict[str, Any]]:
        with closing(self._connect()) as db, db:
            return [dict(row) for row in db.execute("SELECT * FROM agents ORDER BY rowid")]

    def runs(self, limit: int = 20) -> list[dict[str, Any]]:
        with closing(self._connect()) as db, db:
            rows = db.execute("SELECT run_id,room_id,objective,current_stage,retry_count,outcome,updated_at FROM runs ORDER BY updated_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in rows]

    def run(self, run_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as db, db:
            row = db.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if not row:
                return None
            data = dict(row)
            data["packet"] = json.loads(data.pop("packet_json"))
            return data

    def events(self, run_id: str, after_sequence: int = 0) -> list[dict[str, Any]]:
        with closing(self._connect()) as db, db:
            rows = db.execute("SELECT * FROM events WHERE run_id=? AND sequence>? ORDER BY sequence", (run_id, after_sequence))
            result = []
            for row in rows:
                item = dict(row)
                item["packet"] = json.loads(item.pop("packet_json")) if item["packet_json"] else None
                result.append(item)
            return result
