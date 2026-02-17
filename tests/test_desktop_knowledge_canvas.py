"""Tests for knowledge canvas widget."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets

from desktop.widgets.knowledge_canvas import KnowledgeCanvas


def _ensure_qt_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def test_knowledge_canvas_renders_graph_and_filters() -> None:
    app = _ensure_qt_app()
    canvas = KnowledgeCanvas()
    canvas.show()
    app.processEvents()
    try:
        payload = {
            "nodes": [
                {"node_id": "n1", "node_type": "file", "label": "core/runtime.py"},
                {"node_id": "n2", "node_type": "file", "label": "core/state.py"},
            ],
            "edges": [
                {"from_node": "n1", "to_node": "n2", "edge_type": "imports"},
            ],
        }
        canvas.set_graph(payload)
        app.processEvents()
        assert canvas.scene.items()
        assert canvas.edge_type_filter.findText("imports") >= 0

        canvas.node_query_filter.setText("runtime")
        app.processEvents()
        assert "runtime" in canvas.node_query_filter.text().lower()
    finally:
        canvas.close()

