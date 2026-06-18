"""Small HTTP server for the ProofGate dashboard."""
from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .core import run_demo, write_demo


REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_DIR = REPO_ROOT / "demo"
RUN_DIR = REPO_ROOT / "docs" / "demo_run"


class ProofGateRequestHandler(BaseHTTPRequestHandler):
    """Serve dashboard files and ProofGate JSON endpoints."""

    server_version = "ProofGateHTTP/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/transcript":
            transcript, _ = run_demo()
            self._send_json(transcript)
            return
        if parsed.path == "/api/proof-packet":
            _, proof = run_demo()
            self._send_json(proof)
            return
        if parsed.path == "/api/run-demo":
            written = write_demo(RUN_DIR)
            self._send_json({key: str(path.relative_to(REPO_ROOT)) for key, path in written.items()})
            return

        self._send_static(parsed.path)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_json(self, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in {"", "/"} else request_path.lstrip("/")
        file_path = (DEMO_DIR / relative).resolve()
        if not str(file_path).startswith(str(DEMO_DIR.resolve())) or not file_path.is_file():
            self.send_error(404)
            return

        body = file_path.read_bytes()
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the ProofGate dashboard and JSON API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), ProofGateRequestHandler)
    print(f"ProofGate dashboard: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
