"""Knowledge graph canvas widget."""

from __future__ import annotations

import math
from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets

from .a11y import apply_accessible


class KnowledgeCanvas(QtWidgets.QFrame):
    """Graph canvas with simple node/edge rendering and filtering."""

    node_selected = QtCore.Signal(str)
    filters_changed = QtCore.Signal(dict)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("knowledgeCanvas")
        self._graph_payload: dict[str, Any] = {"nodes": [], "edges": []}
        self._node_items: dict[str, QtWidgets.QGraphicsEllipseItem] = {}
        self._node_labels: dict[str, QtWidgets.QGraphicsSimpleTextItem] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        controls = QtWidgets.QHBoxLayout()
        self.edge_type_filter = QtWidgets.QComboBox()
        self.edge_type_filter.addItems(["all"])
        self.edge_type_filter.currentTextChanged.connect(self._on_filters_changed)
        apply_accessible(self.edge_type_filter, name="Knowledge edge type filter")
        self.node_query_filter = QtWidgets.QLineEdit()
        self.node_query_filter.setPlaceholderText("Filter nodes by label")
        self.node_query_filter.textChanged.connect(self._on_filters_changed)
        apply_accessible(self.node_query_filter, name="Knowledge node label filter")
        controls.addWidget(QtWidgets.QLabel("Edge Type:"))
        controls.addWidget(self.edge_type_filter)
        controls.addWidget(self.node_query_filter, stretch=1)
        layout.addLayout(controls)

        body = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)
        self.scene = QtWidgets.QGraphicsScene(self)
        self.canvas = QtWidgets.QGraphicsView(self.scene)
        self.canvas.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.canvas.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        apply_accessible(self.canvas, name="Knowledge graph canvas")
        self.scene.selectionChanged.connect(self._on_selection_changed)
        body.addWidget(self.canvas)

        self.details = QtWidgets.QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlaceholderText("Select a node to inspect details")
        self.details.setMaximumWidth(340)
        apply_accessible(self.details, name="Knowledge node details")
        body.addWidget(self.details)
        body.setSizes([780, 280])
        layout.addWidget(body, stretch=1)

    def set_graph(self, payload: dict[str, Any]) -> None:
        self._graph_payload = payload if isinstance(payload, dict) else {"nodes": [], "edges": []}
        self._refresh_edge_types()
        self._render_graph()

    def graph_payload(self) -> dict[str, Any]:
        return dict(self._graph_payload)

    def _refresh_edge_types(self) -> None:
        edges = self._graph_payload.get("edges", [])
        edge_types = {"all"}
        if isinstance(edges, list):
            edge_types.update(str(item.get("edge_type") or "unknown") for item in edges if isinstance(item, dict))
        current = self.edge_type_filter.currentText()
        self.edge_type_filter.blockSignals(True)
        self.edge_type_filter.clear()
        self.edge_type_filter.addItems(sorted(edge_types))
        index = self.edge_type_filter.findText(current)
        if index >= 0:
            self.edge_type_filter.setCurrentIndex(index)
        self.edge_type_filter.blockSignals(False)

    def _on_filters_changed(self) -> None:
        self._render_graph()
        self.filters_changed.emit(
            {
                "edge_type": self.edge_type_filter.currentText().strip(),
                "query": self.node_query_filter.text().strip(),
            }
        )

    def _render_graph(self) -> None:
        self.scene.clear()
        self._node_items.clear()
        self._node_labels.clear()
        nodes = self._graph_payload.get("nodes", [])
        edges = self._graph_payload.get("edges", [])
        if not isinstance(nodes, list):
            nodes = []
        if not isinstance(edges, list):
            edges = []

        query = self.node_query_filter.text().strip().lower()
        visible_nodes = [
            node
            for node in nodes
            if isinstance(node, dict)
            and (
                not query
                or query in str(node.get("label") or "").lower()
                or query in str(node.get("node_id") or "").lower()
            )
        ]
        if not visible_nodes:
            self.details.setPlainText("No nodes match current filters.")
            return

        radius = 170.0
        center_x = 260.0
        center_y = 220.0
        step = (2.0 * math.pi) / max(len(visible_nodes), 1)
        for idx, node in enumerate(visible_nodes):
            node_id = str(node.get("node_id") or "")
            if not node_id:
                continue
            angle = idx * step
            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius

            item = self.scene.addEllipse(
                x - 16,
                y - 16,
                32,
                32,
                QtGui.QPen(QtGui.QColor("#6B87A5"), 1.5),
                QtGui.QBrush(QtGui.QColor("#7FBCE6")),
            )
            item.setData(0, node_id)
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
            label = self.scene.addSimpleText(str(node.get("label") or node_id))
            label.setPos(x + 18, y - 9)
            self._node_items[node_id] = item
            self._node_labels[node_id] = label

        selected_edge_type = self.edge_type_filter.currentText().strip()
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            edge_type = str(edge.get("edge_type") or "unknown")
            if selected_edge_type != "all" and edge_type != selected_edge_type:
                continue
            src = str(edge.get("from_node") or "")
            dst = str(edge.get("to_node") or "")
            src_item = self._node_items.get(src)
            dst_item = self._node_items.get(dst)
            if not src_item or not dst_item:
                continue
            src_center = src_item.rect().center() + src_item.pos()
            dst_center = dst_item.rect().center() + dst_item.pos()
            self.scene.addLine(
                src_center.x(),
                src_center.y(),
                dst_center.x(),
                dst_center.y(),
                QtGui.QPen(QtGui.QColor("#A7B8CA"), 1.1),
            )

        self.canvas.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)

    def _on_selection_changed(self) -> None:
        selected = self.scene.selectedItems()
        if not selected:
            return
        node_id = str(selected[0].data(0) or "")
        if not node_id:
            return
        node = self._find_node(node_id)
        if node is None:
            return
        lines = [
            f"node_id: {node_id}",
            f"type: {node.get('node_type', 'unknown')}",
            f"label: {node.get('label', '')}",
        ]
        meta = node.get("metadata")
        if isinstance(meta, dict) and meta:
            lines.append("metadata:")
            for key, value in sorted(meta.items()):
                lines.append(f"  - {key}: {value}")
        self.details.setPlainText("\n".join(lines))
        self.node_selected.emit(node_id)

    def _find_node(self, node_id: str) -> dict[str, Any] | None:
        nodes = self._graph_payload.get("nodes", [])
        if not isinstance(nodes, list):
            return None
        for node in nodes:
            if isinstance(node, dict) and str(node.get("node_id") or "") == node_id:
                return node
        return None
