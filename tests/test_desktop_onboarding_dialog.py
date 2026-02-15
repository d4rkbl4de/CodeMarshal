"""Tests for the desktop onboarding dialog contract."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets

from desktop.widgets.onboarding_dialog import OnboardingDialog


def _ensure_qt_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def test_onboarding_dialog_result_payload_accept() -> None:
    _ensure_qt_app()
    dialog = OnboardingDialog(default_path="C:/workspace", show_hints=True)
    dialog.path_input.setText("C:/project")
    dialog.first_action_combo.setCurrentIndex(1)  # Observe
    dialog.hints_check.setChecked(False)
    dialog.accept()

    payload = dialog.result_payload()
    assert payload["accepted"] is True
    assert payload["path"] == "C:/project"
    assert payload["first_action"] == "observe"
    assert payload["show_hints"] is False


def test_onboarding_dialog_result_payload_skip_with_dont_show() -> None:
    _ensure_qt_app()
    dialog = OnboardingDialog(default_path="", show_hints=True)
    dialog.dont_show_again_check.setChecked(True)
    dialog.reject()

    payload = dialog.result_payload()
    assert payload["accepted"] is False
    assert payload["dont_show_again"] is True
