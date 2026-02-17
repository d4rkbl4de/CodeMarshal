"""Tests for history sidebar widget."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets

from desktop.widgets.history_sidebar import HistorySidebar


def _ensure_qt_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def test_history_sidebar_emits_request_and_quick_restore() -> None:
    app = _ensure_qt_app()
    widget = HistorySidebar()
    widget.show()
    app.processEvents()
    requests: list[dict] = []
    restores: list[str] = []
    widget.history_requested.connect(requests.append)
    widget.quick_restore_requested.connect(restores.append)

    try:
        widget.set_session_id("session-1")
        widget.query_input.setText("imports")
        widget.load_btn.click()
        app.processEvents()
        assert len(requests) == 1
        assert requests[0]["session_id"] == "session-1"
        assert requests[0]["query"] == "imports"

        widget.set_history_payload(
            {
                "events": [
                    {"session_id": "session-1", "timestamp": "t1", "event_type": "query"},
                ],
                "suggestions": [{"query": "show imports", "count": 3}],
            }
        )
        app.processEvents()
        assert widget.timeline_list.count() == 1
        assert widget.suggestions_list.count() == 1

        widget.timeline_list.setCurrentRow(0)
        widget.quick_restore_btn.click()
        app.processEvents()
        assert restores == ["session-1"]
    finally:
        widget.close()

