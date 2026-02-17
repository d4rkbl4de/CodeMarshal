"""Tests for comments panel widget."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

from desktop.widgets.comments_panel import CommentsPanel


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

    def __init__(self) -> None:
        super().__init__()
        self.last_add: dict | None = None
        self.last_list: dict | None = None
        self.last_resolve: dict | None = None

    def comment_list(self, **kwargs):
        self.last_list = kwargs
        self.operation_finished.emit(
            "comment_list",
            {
                "success": True,
                "comments": [
                    {
                        "comment_id": "c1",
                        "author_id": "owner_1",
                        "status": "active",
                        "body": "Looks good",
                        "parent_comment_id": None,
                    }
                ],
            },
        )

    def comment_add(self, **kwargs):
        self.last_add = kwargs
        self.operation_finished.emit("comment_add", {"success": True, "comment": {"comment_id": "c2"}})

    def comment_resolve(self, **kwargs):
        self.last_resolve = kwargs
        self.operation_finished.emit("comment_resolve", {"success": True})


def test_comments_panel_validation_and_actions(monkeypatch) -> None:
    app = _ensure_qt_app()
    bridge = _FakeBridge()
    panel = CommentsPanel(command_bridge=bridge)
    panel.show()
    app.processEvents()
    try:
        monkeypatch.setenv("CM_PASS", "strong-passphrase")
        panel.refresh_lock_btn.click()
        app.processEvents()
        assert panel.lock_state_label.text() == "Unlocked"

        panel.share_id_input.setText("share_1")
        panel.author_id_input.setText("owner_1")
        panel.author_name_input.setText("Owner One")
        panel.comment_body_input.setText("Please review.")
        panel.load_btn.click()
        app.processEvents()
        assert bridge.last_list is not None
        assert panel.comments_tree.topLevelItemCount() >= 1

        panel.add_btn.click()
        app.processEvents()
        assert bridge.last_add is not None
        assert bridge.last_add["share_id"] == "share_1"

        panel.resolve_comment_id_input.setText("c1")
        panel.resolver_id_input.setText("owner_1")
        panel.resolve_btn.click()
        app.processEvents()
        assert bridge.last_resolve is not None
        assert bridge.last_resolve["comment_id"] == "c1"
    finally:
        panel.close()

