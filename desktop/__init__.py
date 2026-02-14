"""Desktop GUI entry points for CodeMarshal."""

from __future__ import annotations

from pathlib import Path

__all__ = ["main"]


def main(argv: list[str] | None = None, start_path: Path | None = None) -> int:
    """Lazy desktop launcher to avoid importing PySide6 on module import."""
    from .app import main as _main

    return _main(argv=argv, start_path=start_path)

