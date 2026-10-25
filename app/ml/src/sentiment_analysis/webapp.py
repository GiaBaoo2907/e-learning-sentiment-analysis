"""Backward-compatible ASGI import for older run commands."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
BACKEND_ROOT = str(PROJECT_ROOT / "app")
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from be.webapp import app  # noqa: E402

__all__ = ["app"]