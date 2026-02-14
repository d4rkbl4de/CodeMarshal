"""PyInstaller launch entrypoint for CodeMarshal desktop app."""

from __future__ import annotations

from bridge.entry.gui import launch_gui

if __name__ == "__main__":
    raise SystemExit(launch_gui())

