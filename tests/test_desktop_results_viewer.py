"""Tests for desktop results viewer interactions."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets

from desktop.widgets.results_viewer import ResultsViewer


def _ensure_qt_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def test_copy_actions_use_clipboard() -> None:
    _ensure_qt_app()
    viewer = ResultsViewer()
    viewer.set_sections("summary content", "raw content")

    viewer.copy_summary_btn.click()
    assert QtWidgets.QApplication.clipboard().text() == "summary content"

    viewer.copy_raw_btn.click()
    assert QtWidgets.QApplication.clipboard().text() == "raw content"
