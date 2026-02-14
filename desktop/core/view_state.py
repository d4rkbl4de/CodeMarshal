"""Shared desktop view-state synchronization utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class ViewStateBinder:
    """Synchronize common state across GUI views."""

    def __init__(self) -> None:
        self._views: list[Any] = []
        self._path: str | None = None
        self._session_id: str | None = None
        self._sessions: list[dict[str, Any]] = []
        self._busy: bool = False

    def register(self, view: Any) -> None:
        """Register a view and replay current binder state to it."""
        if view in self._views:
            return
        self._views.append(view)
        self._apply_state_to_view(view)

    def _apply_state_to_view(self, view: Any) -> None:
        if self._path is not None and hasattr(view, "set_current_path"):
            view.set_current_path(self._path)
        if hasattr(view, "set_known_sessions"):
            view.set_known_sessions(list(self._sessions))
        if hasattr(view, "set_current_session"):
            view.set_current_session(self._session_id)
        if hasattr(view, "set_busy"):
            view.set_busy(self._busy)

    def set_path(self, path: str | Path) -> None:
        self._path = str(Path(path))
        for view in self._views:
            if hasattr(view, "set_current_path"):
                view.set_current_path(self._path)

    def set_session(self, session_id: str | None) -> None:
        self._session_id = session_id
        for view in self._views:
            if hasattr(view, "set_current_session"):
                view.set_current_session(session_id)

    def set_sessions(self, sessions: list[dict[str, Any]]) -> None:
        self._sessions = list(sessions)
        for view in self._views:
            if hasattr(view, "set_known_sessions"):
                view.set_known_sessions(list(self._sessions))

    def set_busy(self, is_busy: bool) -> None:
        self._busy = bool(is_busy)
        for view in self._views:
            if hasattr(view, "set_busy"):
                view.set_busy(self._busy)

