"""
gui.py - Desktop GUI entry point for CodeMarshal.

Local-only interface. No network access. Single-focus UI.
"""

from __future__ import annotations

import sys
from pathlib import Path


def launch_gui(start_path: Path | None = None) -> int:
    """Launch the desktop GUI."""
    try:
        from desktop.app import main
    except Exception as exc:  # ImportError or runtime import failures
        print(f"Desktop GUI unavailable: {exc}", file=sys.stderr)
        return 1

    return main(start_path=start_path)

