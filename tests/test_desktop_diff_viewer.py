"""Tests for diff viewer widget."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets

from desktop.widgets.diff_viewer import DiffViewer


def _ensure_qt_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def test_diff_viewer_parses_hunks_and_fold_controls() -> None:
    app = _ensure_qt_app()
    viewer = DiffViewer()
    viewer.show()
    app.processEvents()
    try:
        diff = "\n".join(
            [
                "--- a/sample.py",
                "+++ b/sample.py",
                "@@ -1,3 +1,4 @@",
                " import os",
                "+import sys",
                " def run():",
                "-    return 1",
                "+    return 2",
            ]
        )
        viewer.set_unified_diff(diff)
        app.processEvents()
        assert viewer.hunks_tree.topLevelItemCount() >= 1
        viewer.fold_all_btn.click()
        viewer.unfold_all_btn.click()
        app.processEvents()
        assert viewer.diff_text.toPlainText().strip() != ""
    finally:
        viewer.close()

