"""Tests for desktop GUI command bridge threading behavior."""

from __future__ import annotations

import time

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore

from desktop.core.command_bridge import GUICommandBridge
from desktop.core.exceptions import OperationCancelledError


def _ensure_qt_app() -> QtCore.QCoreApplication:
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtCore.QCoreApplication([])
    return app


class _FakeFacade:
    def run_observation(
        self,
        path,
        eye_types,
        session_id=None,
        progress_callback=None,
        cancel_event=None,
    ):
        del path, eye_types, cancel_event
        if callable(progress_callback):
            progress_callback(1, 2, "step 1")
            progress_callback(2, 2, "step 2")
        return {"session_id": session_id or "fake-session", "success": True}

    def run_pattern_scan(
        self,
        path,
        category=None,
        pattern_ids=None,
        glob="*",
        max_files=10000,
        session_id=None,
        progress_callback=None,
        cancel_event=None,
    ):
        del path, category, pattern_ids, glob, max_files, session_id
        for _ in range(50):
            if cancel_event is not None and cancel_event.is_set():
                raise OperationCancelledError("cancelled")
            if callable(progress_callback):
                progress_callback(1, 1, "running")
            time.sleep(0.01)
        return {"matches_found": 0}

    def list_recent_investigations(self, limit=10):
        del limit
        return []

    def load_session_metadata(self, session_id):
        return {"id": session_id}

    def resolve_session_id(self, session_id=None):
        return session_id


def test_bridge_emits_finished_signal_for_observe() -> None:
    _ensure_qt_app()
    bridge = GUICommandBridge(facade=_FakeFacade())

    loop = QtCore.QEventLoop()
    received: dict[str, object] = {}

    def on_finished(operation: str, payload: object) -> None:
        if operation != "observe":
            return
        received["payload"] = payload
        loop.quit()

    bridge.operation_finished.connect(on_finished)
    bridge.observe(path=".", eye_types=["file_sight"], session_id="test-session")

    QtCore.QTimer.singleShot(3000, loop.quit)
    loop.exec()

    assert "payload" in received
    payload = received["payload"]
    assert isinstance(payload, dict)
    assert payload["session_id"] == "test-session"


def test_bridge_cancel_operation_emits_cancelled_signal() -> None:
    _ensure_qt_app()
    bridge = GUICommandBridge(facade=_FakeFacade())

    loop = QtCore.QEventLoop()
    received: dict[str, bool] = {"cancelled": False}

    def on_cancelled(operation: str) -> None:
        if operation != "pattern_scan":
            return
        received["cancelled"] = True
        loop.quit()

    bridge.operation_cancelled.connect(on_cancelled)
    bridge.pattern_scan(path=".")

    QtCore.QTimer.singleShot(40, lambda: bridge.cancel_operation("pattern_scan"))
    QtCore.QTimer.singleShot(3000, loop.quit)
    loop.exec()

    assert received["cancelled"] is True

