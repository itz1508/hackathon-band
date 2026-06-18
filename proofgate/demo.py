"""Command-line entry point for the ProofGate demo."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import write_demo


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ProofGate local Band-room demo.")
    parser.add_argument("--output", default="docs/demo_run", help="Output directory for generated JSON artifacts.")
    args = parser.parse_args()

    written = write_demo(Path(args.output))
    print(json.dumps({key: str(path) for key, path in written.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

