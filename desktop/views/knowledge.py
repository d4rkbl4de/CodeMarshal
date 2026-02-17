"""Knowledge workflow view."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtWidgets

from desktop.widgets import (
    ActionStrip,
    CommentsPanel,
    ErrorDialog,
    HistorySidebar,
    HintPanel,
    KnowledgeCanvas,
    PageScaffold,
    ResultsViewer,
    SectionHeader,
    apply_accessible,
    clear_invalid,
    mark_invalid,
)


class KnowledgeView(QtWidgets.QWidget):
    """History, graph, and recommendation workflows."""

    navigate_requested = QtCore.Signal(str)
    layout_splitter_ratio_changed = QtCore.Signal(float)

    def __init__(
        self,
        command_bridge: Any | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._bridge = None
        self._current_session_id: str | None = None
        self._hints_enabled = True
        self._build_ui()
        if command_bridge is not None:
            self.set_command_bridge(command_bridge)

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.page_scaffold = PageScaffold(default_ratio=0.52, narrow_breakpoint=1360)
        self.page_scaffold.splitter_ratio_changed.connect(
            self.layout_splitter_ratio_changed.emit
        )
        layout.addWidget(self.page_scaffold)

        header = SectionHeader(
            "Knowledge",
            "Query history, graph context, and recommendations.",
        )
        self.page_scaffold.set_header_widget(header)

        form_layout = self.page_scaffold.form_layout
        results_layout = self.page_scaffold.results_layout

        self.hint_panel = HintPanel(
            "Knowledge Base",
            (
                "History shows timeline events.\n"
                "Graph reveals relationships.\n"
                "Recommendations suggest next actions."
            ),
        )
        form_layout.addWidget(self.hint_panel)

        self.history_sidebar = HistorySidebar()
        self.history_sidebar.history_requested.connect(self._run_history_from_sidebar)
        self.history_sidebar.quick_restore_requested.connect(
            self._restore_session_from_history
        )
        form_layout.addWidget(self.history_sidebar)

        session_group = QtWidgets.QGroupBox("Session")
        session_form = QtWidgets.QFormLayout(session_group)

        self.session_combo = QtWidgets.QComboBox()
        self.session_combo.setEditable(True)
        self.session_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        apply_accessible(self.session_combo, name="Knowledge session selector")
        session_form.addRow("Session ID:", self.session_combo)
        form_layout.addWidget(session_group)

        history_group = QtWidgets.QGroupBox("History Query")
        history_form = QtWidgets.QFormLayout(history_group)

        self.history_query_input = QtWidgets.QLineEdit()
        self.history_query_input.setPlaceholderText("Search history text")
        apply_accessible(self.history_query_input, name="History search query")
        history_form.addRow("Query:", self.history_query_input)

        date_row = QtWidgets.QHBoxLayout()
        self.from_date_input = QtWidgets.QLineEdit()
        self.from_date_input.setPlaceholderText("YYYY-MM-DD")
        self.to_date_input = QtWidgets.QLineEdit()
        self.to_date_input.setPlaceholderText("YYYY-MM-DD")
        apply_accessible(self.from_date_input, name="History from date")
        apply_accessible(self.to_date_input, name="History to date")
        date_row.addWidget(self.from_date_input)
        date_row.addWidget(self.to_date_input)
        history_form.addRow("Date Range:", date_row)

        self.event_type_combo = QtWidgets.QComboBox()
        self.event_type_combo.addItems(
            ["all", "investigate", "observe", "query", "pattern_scan", "export", "insight"]
        )
        apply_accessible(self.event_type_combo, name="History event type")
        history_form.addRow("Event Type:", self.event_type_combo)

        self.history_limit_spin = QtWidgets.QSpinBox()
        self.history_limit_spin.setRange(1, 5000)
        self.history_limit_spin.setValue(100)
        apply_accessible(self.history_limit_spin, name="History result limit")
        history_form.addRow("Limit:", self.history_limit_spin)
        form_layout.addWidget(history_group)

        graph_group = QtWidgets.QGroupBox("Graph Query")
        graph_form = QtWidgets.QFormLayout(graph_group)

        self.graph_focus_input = QtWidgets.QLineEdit()
        self.graph_focus_input.setPlaceholderText("Optional node id focus")
        apply_accessible(self.graph_focus_input, name="Graph focus node")
        graph_form.addRow("Focus Node:", self.graph_focus_input)

        self.graph_depth_spin = QtWidgets.QSpinBox()
        self.graph_depth_spin.setRange(1, 5)
        self.graph_depth_spin.setValue(2)
        apply_accessible(self.graph_depth_spin, name="Graph traversal depth")
        graph_form.addRow("Depth:", self.graph_depth_spin)

        self.graph_edge_type_combo = QtWidgets.QComboBox()
        self.graph_edge_type_combo.addItems(
            [
                "all",
                "imports",
                "exports",
                "depends_on",
                "mentions_pattern",
                "asked_question",
                "contains_file",
                "hits_file",
            ]
        )
        apply_accessible(self.graph_edge_type_combo, name="Graph edge type")
        graph_form.addRow("Edge Type:", self.graph_edge_type_combo)

        self.graph_limit_spin = QtWidgets.QSpinBox()
        self.graph_limit_spin.setRange(1, 5000)
        self.graph_limit_spin.setValue(200)
        apply_accessible(self.graph_limit_spin, name="Graph edge limit")
        graph_form.addRow("Limit:", self.graph_limit_spin)
        form_layout.addWidget(graph_group)

        rec_group = QtWidgets.QGroupBox("Recommendations")
        rec_form = QtWidgets.QFormLayout(rec_group)
        self.rec_category_combo = QtWidgets.QComboBox()
        self.rec_category_combo.addItems(["all", "next_step", "hotspot", "workflow"])
        apply_accessible(self.rec_category_combo, name="Recommendation category")
        rec_form.addRow("Category:", self.rec_category_combo)

        self.rec_limit_spin = QtWidgets.QSpinBox()
        self.rec_limit_spin.setRange(1, 200)
        self.rec_limit_spin.setValue(10)
        apply_accessible(self.rec_limit_spin, name="Recommendation limit")
        rec_form.addRow("Limit:", self.rec_limit_spin)

        self.rec_refresh_check = QtWidgets.QCheckBox("Refresh (ignore cache)")
        apply_accessible(self.rec_refresh_check, name="Refresh recommendations cache")
        rec_form.addRow("", self.rec_refresh_check)
        form_layout.addWidget(rec_group)

        self.validation_label = QtWidgets.QLabel("")
        self.validation_label.setObjectName("validationError")
        self.validation_label.setWordWrap(True)
        self.validation_label.setVisible(False)
        form_layout.addWidget(self.validation_label)

        progress_row = QtWidgets.QHBoxLayout()
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label = QtWidgets.QLabel("Idle")
        apply_accessible(self.progress_label, name="Knowledge progress status")
        progress_row.addWidget(self.progress_bar, stretch=1)
        progress_row.addWidget(self.progress_label)
        form_layout.addLayout(progress_row)

        self.action_strip = ActionStrip()
        self.action_strip.setProperty("sticky", True)
        self.history_btn = self.action_strip.add_button("Load History", self._run_history, primary=True)
        self.graph_btn = self.action_strip.add_button("Load Graph", self._run_graph)
        self.rec_btn = self.action_strip.add_button("Recommendations", self._run_recommendations)
        self.cancel_btn = self.action_strip.add_button("Cancel", self._on_cancel)
        self.cancel_btn.setEnabled(False)
        form_layout.addStretch(1)
        form_layout.addWidget(self.action_strip)

        self.comments_panel = CommentsPanel()
        form_layout.addWidget(self.comments_panel)

        results_header = SectionHeader(
            "Knowledge Results",
            "Rendered summary and full payload for the latest operation.",
        )
        results_layout.addWidget(results_header)
        self.knowledge_canvas = KnowledgeCanvas()
        results_layout.addWidget(self.knowledge_canvas, stretch=1)
        self.results = ResultsViewer()
        results_layout.addWidget(self.results, stretch=1)

    def set_layout_splitter_ratio(self, ratio: float) -> None:
        self.page_scaffold.set_splitter_ratio(ratio)

    def set_command_bridge(self, command_bridge: Any) -> None:
        if self._bridge is command_bridge:
            return
        self._bridge = command_bridge
        self.comments_panel.set_command_bridge(command_bridge)
        self._bridge.operation_started.connect(self._on_operation_started)
        self._bridge.operation_progress.connect(self._on_operation_progress)
        self._bridge.operation_finished.connect(self._on_operation_finished)
        self._bridge.operation_error.connect(self._on_operation_error)
        self._bridge.operation_cancelled.connect(self._on_operation_cancelled)

    def set_current_path(self, path: str | Path) -> None:
        del path

    def set_current_session(self, session_id: str | None) -> None:
        self._current_session_id = session_id
        self.history_sidebar.set_session_id(session_id)
        if session_id:
            self.session_combo.setCurrentText(session_id)

    def _run_history_from_sidebar(self, payload: dict[str, Any]) -> None:
        if self._bridge is None:
            ErrorDialog.show_error(self, "Unavailable", "Command bridge is not initialized.")
            return
        session_id = str(payload.get("session_id") or self._current_session_id or "").strip()
        if not session_id:
            self._set_validation("Select a session before running knowledge queries.", self.session_combo)
            return
        self._clear_validation()
        try:
            self._bridge.history(
                session_id=session_id,
                query=payload.get("query"),
                from_date=payload.get("from_date"),
                to_date=payload.get("to_date"),
                event_type=payload.get("event_type"),
                limit=int(payload.get("limit") or 100),
            )
        except RuntimeError as exc:
            ErrorDialog.show_error(self, "Operation Running", str(exc))

    def _restore_session_from_history(self, session_id: str) -> None:
        if not session_id:
            return
        self.set_current_session(session_id)
        self.session_combo.setCurrentText(session_id)

    def set_known_sessions(self, sessions: list[dict[str, Any]]) -> None:
        current = self.session_combo.currentText().strip()
        self.session_combo.blockSignals(True)
        self.session_combo.clear()
        self.session_combo.addItem("")
        for session in sessions:
            session_id = str(session.get("session_id") or session.get("id") or "")
            if session_id:
                self.session_combo.addItem(session_id)
        self.session_combo.setCurrentText(current or (self._current_session_id or ""))
        self.session_combo.blockSignals(False)

    def _resolve_session(self) -> str | None:
        value = self.session_combo.currentText().strip() or self._current_session_id
        if value:
            self._clear_validation()
            return value
        self._set_validation("Select a session before running knowledge queries.", self.session_combo)
        return None

    def _run_history(self) -> None:
        if self._bridge is None:
            ErrorDialog.show_error(self, "Unavailable", "Command bridge is not initialized.")
            return
        session_id = self._resolve_session()
        if not session_id:
            return
        event_type = self.event_type_combo.currentText().strip().lower()
        try:
            self._bridge.history(
                session_id=session_id,
                query=self.history_query_input.text().strip() or None,
                from_date=self.from_date_input.text().strip() or None,
                to_date=self.to_date_input.text().strip() or None,
                event_type=None if event_type == "all" else event_type,
                limit=int(self.history_limit_spin.value()),
            )
        except RuntimeError as exc:
            ErrorDialog.show_error(self, "Operation Running", str(exc))

    def _run_graph(self) -> None:
        if self._bridge is None:
            ErrorDialog.show_error(self, "Unavailable", "Command bridge is not initialized.")
            return
        session_id = self._resolve_session()
        if not session_id:
            return
        edge_type = self.graph_edge_type_combo.currentText().strip().lower()
        try:
            self._bridge.graph(
                session_id=session_id,
                focus=self.graph_focus_input.text().strip() or None,
                depth=int(self.graph_depth_spin.value()),
                edge_type=None if edge_type == "all" else edge_type,
                limit=int(self.graph_limit_spin.value()),
            )
        except RuntimeError as exc:
            ErrorDialog.show_error(self, "Operation Running", str(exc))

    def _run_recommendations(self) -> None:
        if self._bridge is None:
            ErrorDialog.show_error(self, "Unavailable", "Command bridge is not initialized.")
            return
        session_id = self._resolve_session()
        if not session_id:
            return
        category = self.rec_category_combo.currentText().strip().lower()
        try:
            self._bridge.recommendations(
                session_id=session_id,
                limit=int(self.rec_limit_spin.value()),
                category=None if category == "all" else category,
                refresh=self.rec_refresh_check.isChecked(),
            )
        except RuntimeError as exc:
            ErrorDialog.show_error(self, "Operation Running", str(exc))

    def _on_cancel(self) -> None:
        if self._bridge is None:
            return
        self._bridge.cancel_operation("history")
        self._bridge.cancel_operation("graph")
        self._bridge.cancel_operation("recommendations")

    def _on_operation_started(self, operation: str) -> None:
        if operation not in {"history", "graph", "recommendations"}:
            return
        self.cancel_btn.setEnabled(True)
        self.history_btn.setEnabled(False)
        self.graph_btn.setEnabled(False)
        self.rec_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"{operation} started")

    def _on_operation_progress(
        self,
        operation: str,
        current: int,
        total: int,
        message: str,
    ) -> None:
        if operation not in {"history", "graph", "recommendations"}:
            return
        value = int((current / max(total, 1)) * 100)
        self.progress_bar.setValue(max(0, min(100, value)))
        self.progress_label.setText(message or f"{operation}: {current}/{total}")

    def _on_operation_finished(self, operation: str, payload: object) -> None:
        if operation not in {"history", "graph", "recommendations"}:
            return
        self.cancel_btn.setEnabled(False)
        self.history_btn.setEnabled(True)
        self.graph_btn.setEnabled(True)
        self.rec_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.progress_label.setText(f"{operation} completed")

        data = payload if isinstance(payload, dict) else {"result": payload}
        summary: dict[str, Any] = {}
        if operation == "history":
            summary = {
                "count": data.get("count", 0),
                "session_id": data.get("session_id"),
                "suggestions": data.get("suggestions", [])[:5],
            }
            self.history_sidebar.set_history_payload(data)
        elif operation == "graph":
            summary = {
                "summary": data.get("summary", {}),
                "focus": data.get("focus"),
                "depth": data.get("depth"),
            }
            self.knowledge_canvas.set_graph(data)
        elif operation == "recommendations":
            summary = {
                "count": data.get("count", 0),
                "session_id": data.get("session_id"),
                "recommendations": data.get("recommendations", [])[:5],
            }

        self.results.set_sections(
            json.dumps(summary, indent=2, default=str),
            json.dumps(data, indent=2, default=str),
        )
        self.results.set_metadata(f"Latest operation: {operation}")
        session_id = str(data.get("session_id") or "")
        if session_id:
            self.set_current_session(session_id)

    def _on_operation_error(
        self,
        operation: str,
        error_type: str,
        message: str,
        _details: str,
    ) -> None:
        if operation not in {"history", "graph", "recommendations"}:
            return
        self.cancel_btn.setEnabled(False)
        self.history_btn.setEnabled(True)
        self.graph_btn.setEnabled(True)
        self.rec_btn.setEnabled(True)
        self.progress_label.setText(f"Failed: {error_type} - {message}")

    def _on_operation_cancelled(self, operation: str) -> None:
        if operation not in {"history", "graph", "recommendations"}:
            return
        self.cancel_btn.setEnabled(False)
        self.history_btn.setEnabled(True)
        self.graph_btn.setEnabled(True)
        self.rec_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"{operation} cancelled")

    def set_busy(self, is_busy: bool) -> None:
        if is_busy:
            self.history_btn.setEnabled(False)
            self.graph_btn.setEnabled(False)
            self.rec_btn.setEnabled(False)
        else:
            self.history_btn.setEnabled(True)
            self.graph_btn.setEnabled(True)
            self.rec_btn.setEnabled(True)

    def trigger_primary_action(self) -> None:
        self._run_history()

    def set_hints_enabled(self, enabled: bool) -> None:
        self._hints_enabled = bool(enabled)
        self.hint_panel.setVisible(self._hints_enabled)

    def _set_validation(self, message: str, widget: QtWidgets.QWidget | None = None) -> None:
        mark_invalid(widget, self.validation_label, message)

    def _clear_validation(self, *_args: object) -> None:
        clear_invalid((self.session_combo,), self.validation_label)
