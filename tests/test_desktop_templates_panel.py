"""Tests for templates panel widget."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets

from desktop.widgets.templates_panel import TemplatesPanel


def _ensure_qt_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def test_templates_panel_emits_create_payload() -> None:
    app = _ensure_qt_app()
    panel = TemplatesPanel(template_ids=["security.keyword_assignment"])
    panel.show()
    app.processEvents()
    captured: list[dict] = []
    panel.create_requested.connect(captured.append)
    try:
        panel.template_values_input.setText("identifier=api_key")
        panel.create_pattern_id_input.setText("custom_rule")
        panel.create_dry_run_checkbox.setChecked(True)
        panel.create_pattern_btn.click()
        app.processEvents()

        assert len(captured) == 1
        payload = captured[0]
        assert payload["template_id"] == "security.keyword_assignment"
        assert payload["values"] == {"identifier": "api_key"}
        assert payload["pattern_id"] == "custom_rule"
        assert payload["dry_run"] is True
    finally:
        panel.close()


def test_templates_panel_marks_validation_for_invalid_values() -> None:
    app = _ensure_qt_app()
    panel = TemplatesPanel(template_ids=["security.keyword_assignment"])
    panel.show()
    app.processEvents()
    try:
        panel.template_values_input.setText("identifier")
        panel.create_pattern_btn.click()
        app.processEvents()
        assert panel.validation_label.isVisible()
        assert "Invalid template value" in panel.validation_label.text()
    finally:
        panel.close()

