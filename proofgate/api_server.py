"""Compatibility import for the canonical read-only Band mirror API."""
from .server import app, main

__all__ = ["app", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
