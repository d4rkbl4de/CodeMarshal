"""Keyboard navigation tests for desktop GUI views."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtTest, QtWidgets

from desktop.views.home import HomeView
from desktop.views.investigate import InvestigateView
from desktop.widgets.onboarding_dialog import OnboardingDialog


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

    def investigate(self, **_kwargs):
        return

    def query(self, **_kwargs):
        return

    def cancel_operation(self, _operation: str):
        return


def test_home_recent_paths_enter_activates_selected_path() -> None:
    app = _ensure_qt_app()
    home = HomeView()
    home.show()
    app.processEvents()
    try:
        home.set_recent_paths(["C:/repo_a", "C:/repo_b"])
        home.recent_paths.setCurrentRow(1)
        home.recent_paths.setFocus()
        captured: list[str] = []
        home.path_selected.connect(captured.append)

        QtTest.QTest.keyClick(home.recent_paths, QtCore.Qt.Key_Return)
        app.processEvents()

        assert captured == ["C:/repo_b"]
    finally:
        home.close()


def test_onboarding_focus_starts_on_path_input() -> None:
    app = _ensure_qt_app()
    dialog = OnboardingDialog(default_path="C:/workspace", show_hints=True)
    dialog.show()
    app.processEvents()
    try:
        assert dialog.focusWidget() is dialog.path_input
    finally:
        dialog.close()


def test_investigate_tab_order_moves_to_browse_after_path() -> None:
    app = _ensure_qt_app()
    view = InvestigateView(command_bridge=_FakeBridge())
    view.show()
    app.processEvents()
    try:
        view.path_input.setFocus()
        app.processEvents()
        QtTest.QTest.keyClick(view.path_input, QtCore.Qt.Key_Tab)
        app.processEvents()
        assert view.focusWidget() is view.browse_btn
    finally:
        view.close()
