"""Start the existing Edge Job API and ProofGate dashboard together."""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def resolve_edge_root(explicit_root: str | None = None) -> Path:
    """Resolve the Edge repository without reading credentials or local config."""
    candidates = [
        explicit_root,
        os.environ.get("EDGE_REPO_ROOT"),
        str(Path(__file__).resolve().parents[2] / "Edge"),
    ]
    for value in candidates:
        if not value:
            continue
        root = Path(value).expanduser().resolve()
        if (root / "edge_backend" / "api" / "app.py").is_file():
            return root
    checked = [str(Path(value).expanduser()) for value in candidates if value]
    raise RuntimeError(
        "Edge repository not found. Set EDGE_REPO_ROOT or pass --edge-root. "
        f"Checked: {checked}"
    )


def load_edge_app(edge_root: Path) -> Any:
    """Import the current Edge API while resolving its relative state root correctly."""
    original_cwd = Path.cwd()
    root_text = str(edge_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    try:
        os.chdir(edge_root)
        return importlib.import_module("edge_backend.api.app").app
    finally:
        os.chdir(original_cwd)


def endpoint_ready(url: str, timeout: float = 0.5) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


def wait_until_ready(url: str, timeout_seconds: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if endpoint_ready(url):
            return True
        time.sleep(0.1)
    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Start the Edge Job API and ProofGate dashboard with one command."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--dashboard-port", type=int, default=8787)
    parser.add_argument("--edge-port", type=int, default=8790)
    parser.add_argument("--edge-root")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify repository and import wiring without starting servers.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        edge_root = resolve_edge_root(args.edge_root)
        edge_app = load_edge_app(edge_root)
    except Exception as exc:
        print(f"ProofGate launch check failed: {exc}", file=sys.stderr)
        return 1

    dashboard_root = Path(__file__).resolve().parents[1] / "demo"
    if not dashboard_root.is_dir():
        print(f"ProofGate dashboard directory not found: {dashboard_root}", file=sys.stderr)
        return 1

    wiring = {
        "edge_root": str(edge_root),
        "edge_api": f"http://{args.host}:{args.edge_port}",
        "dashboard": f"http://{args.host}:{args.dashboard_port}",
        "dashboard_root": str(dashboard_root),
        "edge_app_loaded": edge_app is not None,
    }
    if args.check:
        print(json.dumps(wiring, indent=2))
        return 0

    import uvicorn

    edge_health = f"http://{args.host}:{args.edge_port}/api/health"
    edge_server = None
    edge_thread = None
    if endpoint_ready(edge_health):
        print(f"Using existing Edge Job API at {wiring['edge_api']}")
    else:
        edge_server = uvicorn.Server(
            uvicorn.Config(edge_app, host=args.host, port=args.edge_port, log_level="warning")
        )
        edge_thread = threading.Thread(
            target=edge_server.run,
            name="edge-job-api",
            daemon=True,
        )
        edge_thread.start()
        if not wait_until_ready(edge_health):
            edge_server.should_exit = True
            edge_thread.join(timeout=2)
            print("Edge Job API did not become ready within 10 seconds.", file=sys.stderr)
            return 1
        print(f"Started Edge Job API at {wiring['edge_api']}")

    print(f"ProofGate dashboard: {wiring['dashboard']}")
    try:
        uvicorn.run(
            "proofgate.server:app",
            host=args.host,
            port=args.dashboard_port,
            reload=False,
        )
    finally:
        if edge_server is not None and edge_thread is not None:
            edge_server.should_exit = True
            edge_thread.join(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
