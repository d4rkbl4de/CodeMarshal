"""Tests for desktop shell layout and persistent sidebar behavior."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

import desktop.app as app_module
from desktop.core.session_manager import SessionManager


def _ensure_qt_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


class _FakeBridge(QtCore.QObject):
    operation_started = QtCore.Signal(str)
    operation_progress = QtCore.Signal(str, int, int, str)
    operation_finished = QtCore.Signal(str, object)
    operation_error = QtCore.Signal(str, str, str, str)
    operation_cancelled = QtCore.Signal(str)
    busy_changed = QtCore.Signal(bool)

    def __init__(self, facade) -> None:
        super().__init__()
        self.facade = facade

    def cancel_all(self) -> None:
        return

    def cancel_operation(self, _operation: str) -> None:
        return

    def list_recent_investigations(self, limit: int = 10):
        del limit
        return []

    def load_session_metadata(self, session_id: str):
        del session_id
        return None

    def observe(self, **_kwargs):
        return

    def investigate(self, **_kwargs):
        return

    def query(self, **_kwargs):
        return

    def pattern_list(self, **_kwargs):
        return

    def pattern_scan(self, **_kwargs):
        return

    def preview_export(self, **_kwargs):
        return

    def export(self, **_kwargs):
        return


class _FakeDialog:
    def __init__(self, *args, **kwargs) -> None:
        del args, kwargs

    def exec(self) -> int:
        return int(QtWidgets.QDialog.Rejected)

    def result_payload(self):
        return {
            "accepted": False,
            "path": None,
            "first_action": "investigate",
            "show_hints": True,
            "dont_show_again": True,
        }


def test_shell_navigation_updates_sidebar_and_context(tmp_path, monkeypatch) -> None:
    app = _ensure_qt_app()

    class _FakeSessionManager(SessionManager):
        def __init__(self) -> None:
            super().__init__(state_path=tmp_path / "gui_state.json")

    monkeypatch.setattr(app_module, "SessionManager", _FakeSessionManager)
    monkeypatch.setattr(app_module, "GUICommandBridge", _FakeBridge)
    monkeypatch.setattr(app_module, "OnboardingDialog", _FakeDialog)

    window = app_module.MainWindow(start_path=tmp_path)
    try:
        window.show()
        app.processEvents()

        window._navigate("patterns")
        app.processEvents()

        assert window._stack.currentWidget() is window._views["patterns"]
        assert window._sidebar._buttons["patterns"].isChecked()
        assert "Patterns" in window._context_bar.route_title.text()
        assert (
            window.findChild(QtWidgets.QWidget, "shellContentGutter") is not None
        )
    finally:
        window.close()


def test_sidebar_collapse_persists_preference(tmp_path, monkeypatch) -> None:
    app = _ensure_qt_app()

    class _FakeSessionManager(SessionManager):
        def __init__(self) -> None:
            super().__init__(state_path=tmp_path / "gui_state.json")

    monkeypatch.setattr(app_module, "SessionManager", _FakeSessionManager)
    monkeypatch.setattr(app_module, "GUICommandBridge", _FakeBridge)
    monkeypatch.setattr(app_module, "OnboardingDialog", _FakeDialog)

    window = app_module.MainWindow(start_path=tmp_path)
    try:
        window.show()
        app.processEvents()
        window._sidebar.set_collapsed(True)
        app.processEvents()
        assert window._session_manager.get_sidebar_collapsed() is True
    finally:
        window.close()
