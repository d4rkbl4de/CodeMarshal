"""Tests for MainWindow onboarding orchestration."""

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

    # view callable stubs
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


def test_mainwindow_applies_onboarding_accept_payload(tmp_path, monkeypatch) -> None:
    app = _ensure_qt_app()

    class _FakeSessionManager(SessionManager):
        def __init__(self) -> None:
            super().__init__(state_path=tmp_path / "gui_state.json")

    class _FakeDialog:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs

        def exec(self) -> int:
            return int(QtWidgets.QDialog.Accepted)

        def result_payload(self):
            return {
                "accepted": True,
                "path": str(tmp_path),
                "first_action": "observe",
                "show_hints": False,
                "dont_show_again": False,
            }

    monkeypatch.setattr(app_module, "SessionManager", _FakeSessionManager)
    monkeypatch.setattr(app_module, "GUICommandBridge", _FakeBridge)
    monkeypatch.setattr(app_module, "OnboardingDialog", _FakeDialog)

    window = app_module.MainWindow(start_path=tmp_path)
    try:
        window.show()
        app.processEvents()
        assert window._session_manager.is_onboarding_completed() is True
        assert window._session_manager.get_show_context_hints() is False
        assert window._stack.currentWidget() is window._views["observe"]
        assert window.focusWidget() is window._views["observe"].path_input
    finally:
        window.close()


def test_recovery_prompt_runs_before_onboarding(tmp_path, monkeypatch) -> None:
    app = _ensure_qt_app()
    call_order: list[str] = []

    class _FakeSessionManager(SessionManager):
        def __init__(self) -> None:
            super().__init__(state_path=tmp_path / "gui_state.json")
            self.save_recovery_state("session-1", str(tmp_path))

    class _FakeDialog:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs
            call_order.append("onboarding")

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

    def _fake_question(*args, **kwargs):
        del args, kwargs
        call_order.append("recovery")
        return QtWidgets.QMessageBox.No

    monkeypatch.setattr(app_module, "SessionManager", _FakeSessionManager)
    monkeypatch.setattr(app_module, "GUICommandBridge", _FakeBridge)
    monkeypatch.setattr(app_module, "OnboardingDialog", _FakeDialog)
    monkeypatch.setattr(QtWidgets.QMessageBox, "question", _fake_question)

    window = app_module.MainWindow(start_path=tmp_path)
    try:
        window.show()
        app.processEvents()
        assert call_order[:2] == ["recovery", "onboarding"]
        assert window._session_manager.is_onboarding_completed() is True
        assert window.focusWidget() is window._views["home"].path_input
    finally:
        window.close()


def test_accessibility_menu_updates_session_preferences(tmp_path, monkeypatch) -> None:
    app = _ensure_qt_app()

    class _FakeSessionManager(SessionManager):
        def __init__(self) -> None:
            super().__init__(state_path=tmp_path / "gui_state.json")

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

    monkeypatch.setattr(app_module, "SessionManager", _FakeSessionManager)
    monkeypatch.setattr(app_module, "GUICommandBridge", _FakeBridge)
    monkeypatch.setattr(app_module, "OnboardingDialog", _FakeDialog)

    window = app_module.MainWindow(start_path=tmp_path)
    try:
        window.show()
        app.processEvents()
        window._set_accessibility_mode("high_contrast")
        window._set_font_scale(1.3)

        assert window._session_manager.get_accessibility_mode() == "high_contrast"
        assert window._session_manager.get_font_scale() == 1.3
        assert window._accessibility_mode_actions["high_contrast"].isChecked()
        assert window._font_scale_actions[1.3].isChecked()
    finally:
        window.close()
