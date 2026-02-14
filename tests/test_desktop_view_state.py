"""Tests for desktop view-state synchronization binder."""

from __future__ import annotations

from pathlib import Path

from desktop.core.view_state import ViewStateBinder


class _DummyView:
    def __init__(self) -> None:
        self.path = None
        self.session = None
        self.sessions = []
        self.busy = False

    def set_current_path(self, value):
        self.path = value

    def set_current_session(self, value):
        self.session = value

    def set_known_sessions(self, value):
        self.sessions = list(value)

    def set_busy(self, value):
        self.busy = bool(value)


def test_binder_replays_state_on_register() -> None:
    binder = ViewStateBinder()
    binder.set_path("C:/tmp")
    binder.set_session("s1")
    binder.set_sessions([{"session_id": "s1"}])
    binder.set_busy(True)

    view = _DummyView()
    binder.register(view)

    assert Path(view.path) == Path("C:/tmp")
    assert view.session == "s1"
    assert view.sessions == [{"session_id": "s1"}]
    assert view.busy is True


def test_binder_propagates_updates() -> None:
    binder = ViewStateBinder()
    view = _DummyView()
    binder.register(view)

    binder.set_path("X:/workspace")
    binder.set_session("session-42")
    binder.set_sessions([{"session_id": "session-42"}, {"session_id": "session-41"}])
    binder.set_busy(True)

    assert Path(view.path) == Path("X:/workspace")
    assert view.session == "session-42"
    assert len(view.sessions) == 2
    assert view.busy is True
