"""Tests for desktop view inline validation behavior."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

from desktop.views.investigate import InvestigateView


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


def test_investigate_inline_validation_for_missing_path() -> None:
    _ensure_qt_app()
    view = InvestigateView(command_bridge=_FakeBridge())
    view.path_input.setText("")
    view._on_start_investigation()

    assert view.validation_label.isHidden() is False
    assert "Select a target path first." in view.validation_label.text()
    assert view.path_input.property("state") == "error"

    view.path_input.setText("C:/tmp")
    assert view.validation_label.isHidden() is True
