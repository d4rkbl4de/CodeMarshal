"""Tests for desktop view inline validation behavior."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

from desktop.views.investigate import InvestigateView
from desktop.views.patterns import PatternsView


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


class _FakePatternBridge(QtCore.QObject):
    operation_started = QtCore.Signal(str)
    operation_progress = QtCore.Signal(str, int, int, str)
    operation_finished = QtCore.Signal(str, object)
    operation_error = QtCore.Signal(str, str, str, str)
    operation_cancelled = QtCore.Signal(str)
    busy_changed = QtCore.Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.last_create: dict | None = None
        self.last_share: dict | None = None

    def pattern_list(self, **_kwargs):
        return

    def pattern_scan(self, **_kwargs):
        return

    def pattern_search(self, **_kwargs):
        return

    def pattern_apply(self, **_kwargs):
        return

    def pattern_create(self, **kwargs):
        self.last_create = kwargs
        return

    def pattern_share(self, **kwargs):
        self.last_share = kwargs
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


def test_patterns_create_validation_for_invalid_assignments() -> None:
    _ensure_qt_app()
    bridge = _FakePatternBridge()
    view = PatternsView(command_bridge=bridge)

    view.template_values_input.setText("identifier")
    view._on_create_pattern()

    assert view.validation_label.isHidden() is False
    assert "Invalid template value" in view.validation_label.text()
    assert view.template_values_input.property("state") == "error"


def test_patterns_share_validation_for_missing_pattern_id() -> None:
    _ensure_qt_app()
    bridge = _FakePatternBridge()
    view = PatternsView(command_bridge=bridge)

    view.share_pattern_input.setText("")
    view._on_share_pattern()

    assert view.validation_label.isHidden() is False
    assert "Provide a pattern ID to share." in view.validation_label.text()
    assert view.share_pattern_input.property("state") == "error"


def test_patterns_create_and_share_forward_to_bridge() -> None:
    _ensure_qt_app()
    bridge = _FakePatternBridge()
    view = PatternsView(command_bridge=bridge)

    view.template_values_input.setText("identifier=api_key")
    view.create_pattern_id_input.setText("custom_api_key_rule")
    view.create_bundle_output_input.setText("exports/custom_api_key_rule.cmpattern.yaml")
    view.create_dry_run_checkbox.setChecked(True)
    view._on_create_pattern()

    assert bridge.last_create is not None
    assert bridge.last_create["template_id"]
    assert bridge.last_create["values"] == {"identifier": "api_key"}
    assert bridge.last_create["pattern_id"] == "custom_api_key_rule"
    assert bridge.last_create["output_path"] == "exports/custom_api_key_rule.cmpattern.yaml"
    assert bridge.last_create["dry_run"] is True

    view.share_pattern_input.setText("hardcoded_password")
    view.share_bundle_output_input.setText("exports/hardcoded_password.cmpattern.yaml")
    view._on_share_pattern()

    assert bridge.last_share is not None
    assert bridge.last_share["pattern_id"] == "hardcoded_password"
    assert (
        bridge.last_share["bundle_out"]
        == "exports/hardcoded_password.cmpattern.yaml"
    )
