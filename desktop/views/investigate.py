"""Investigate workflow view."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtWidgets

from desktop.widgets import ErrorDialog, ResultsViewer


class InvestigateView(QtWidgets.QWidget):
    """Manage investigation sessions and follow-up queries."""

    navigate_requested = QtCore.Signal(str)

    def __init__(
        self,
        command_bridge: Any | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._bridge = None
        self._current_session_id: str | None = None
        self._build_ui()
        if command_bridge is not None:
            self.set_command_bridge(command_bridge)

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)

        header = QtWidgets.QHBoxLayout()
        back_btn = QtWidgets.QPushButton("Home")
        back_btn.clicked.connect(lambda: self.navigate_requested.emit("home"))
        title = QtWidgets.QLabel("Investigate")
        title.setObjectName("sectionTitle")
        self.session_label = QtWidgets.QLabel("Session: none")
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.session_label)
        layout.addLayout(header)

        config_group = QtWidgets.QGroupBox("Investigation Configuration")
        config_form = QtWidgets.QFormLayout(config_group)

        path_row = QtWidgets.QHBoxLayout()
        self.path_input = QtWidgets.QLineEdit()
        self.path_input.setPlaceholderText("Project root or file path")
        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.clicked.connect(self._on_browse)
        path_row.addWidget(self.path_input, stretch=1)
        path_row.addWidget(browse_btn)
        config_form.addRow("Target:", path_row)

        self.scope_combo = QtWidgets.QComboBox()
        self.scope_combo.addItems(["project", "package", "module", "file"])
        config_form.addRow("Scope:", self.scope_combo)

        self.intent_combo = QtWidgets.QComboBox()
        self.intent_combo.addItems(
            [
                "initial_scan",
                "constitutional_check",
                "dependency_analysis",
                "architecture_review",
            ]
        )
        config_form.addRow("Intent:", self.intent_combo)

        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Optional investigation name")
        config_form.addRow("Name:", self.name_input)

        self.notes_input = QtWidgets.QLineEdit()
        self.notes_input.setPlaceholderText("Optional notes")
        config_form.addRow("Notes:", self.notes_input)
        layout.addWidget(config_group)

        query_group = QtWidgets.QGroupBox("Query")
        query_form = QtWidgets.QFormLayout(query_group)

        self.session_combo = QtWidgets.QComboBox()
        self.session_combo.setEditable(True)
        self.session_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        query_form.addRow("Session:", self.session_combo)

        self.question_type_combo = QtWidgets.QComboBox()
        self.question_type_combo.addItems(
            ["structure", "purpose", "connections", "anomalies", "thinking"]
        )
        query_form.addRow("Question Type:", self.question_type_combo)

        self.question_input = QtWidgets.QLineEdit()
        self.question_input.setPlaceholderText("Ask a structured question")
        query_form.addRow("Question:", self.question_input)

        self.focus_input = QtWidgets.QLineEdit()
        self.focus_input.setPlaceholderText("Optional focus path or anchor")
        query_form.addRow("Focus:", self.focus_input)

        self.limit_spin = QtWidgets.QSpinBox()
        self.limit_spin.setRange(1, 5000)
        self.limit_spin.setValue(25)
        query_form.addRow("Limit:", self.limit_spin)
        layout.addWidget(query_group)

        actions = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Start Investigation")
        self.start_btn.clicked.connect(self._on_start_investigation)
        self.query_btn = QtWidgets.QPushButton("Run Query")
        self.query_btn.clicked.connect(self._on_run_query)
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel)
        actions.addWidget(self.start_btn)
        actions.addWidget(self.query_btn)
        actions.addWidget(self.cancel_btn)
        actions.addStretch(1)
        layout.addLayout(actions)

        progress_row = QtWidgets.QHBoxLayout()
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label = QtWidgets.QLabel("Idle")
        progress_row.addWidget(self.progress_bar, stretch=1)
        progress_row.addWidget(self.progress_label)
        layout.addLayout(progress_row)

        results_group = QtWidgets.QGroupBox("Results")
        results_layout = QtWidgets.QVBoxLayout(results_group)
        self.results = ResultsViewer()
        results_layout.addWidget(self.results)
        layout.addWidget(results_group, stretch=1)

    def set_command_bridge(self, command_bridge: Any) -> None:
        if self._bridge is command_bridge:
            return
        self._bridge = command_bridge
        self._bridge.operation_started.connect(self._on_operation_started)
        self._bridge.operation_progress.connect(self._on_operation_progress)
        self._bridge.operation_finished.connect(self._on_operation_finished)
        self._bridge.operation_error.connect(self._on_operation_error)
        self._bridge.operation_cancelled.connect(self._on_operation_cancelled)

    def set_current_path(self, path: str | Path) -> None:
        self.path_input.setText(str(path))

    def set_current_session(self, session_id: str | None) -> None:
        self._current_session_id = session_id
        if session_id:
            self.session_combo.setCurrentText(session_id)
            self.session_label.setText(f"Session: {session_id}")
        else:
            self.session_label.setText("Session: none")

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

    def set_session_metadata(self, metadata: dict[str, Any] | None) -> None:
        if not metadata:
            return
        session_id = str(metadata.get("session_id") or metadata.get("id") or "")
        if session_id:
            self.set_current_session(session_id)
        if metadata.get("path"):
            self.path_input.setText(str(metadata["path"]))
        if metadata.get("name"):
            self.name_input.setText(str(metadata["name"]))
        if metadata.get("intent"):
            idx = self.intent_combo.findText(str(metadata["intent"]))
            if idx >= 0:
                self.intent_combo.setCurrentIndex(idx)
        if metadata.get("scope"):
            idx = self.scope_combo.findText(str(metadata["scope"]))
            if idx >= 0:
                self.scope_combo.setCurrentIndex(idx)

    def _on_browse(self) -> None:
        start = self.path_input.text().strip() or str(Path(".").resolve())
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose Target", start)
        if not path:
            file_path, _filter = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Choose File",
                start,
                "All Files (*.*)",
            )
            path = file_path
        if path:
            self.path_input.setText(path)

    def _on_start_investigation(self) -> None:
        if self._bridge is None:
            ErrorDialog.show_error(self, "Unavailable", "Command bridge is not initialized.")
            return

        path_value = self.path_input.text().strip()
        if not path_value:
            ErrorDialog.show_error(self, "Missing Path", "Select a target path first.")
            return
        if not Path(path_value).exists():
            ErrorDialog.show_error(self, "Invalid Path", f"Path does not exist: {path_value}")
            return

        try:
            self._bridge.investigate(
                path=path_value,
                scope=self.scope_combo.currentText().strip().lower(),
                intent=self.intent_combo.currentText().strip().lower(),
                name=self.name_input.text().strip(),
                notes=self.notes_input.text().strip(),
            )
        except RuntimeError as exc:
            ErrorDialog.show_error(
                self,
                "Investigation Already Running",
                str(exc),
                suggestion="Wait for completion or cancel the active operation.",
            )

    def _on_run_query(self) -> None:
        if self._bridge is None:
            ErrorDialog.show_error(self, "Unavailable", "Command bridge is not initialized.")
            return

        question = self.question_input.text().strip()
        if not question:
            ErrorDialog.show_error(self, "Missing Question", "Enter a query question first.")
            return

        session_id = self.session_combo.currentText().strip() or self._current_session_id
        if not session_id:
            ErrorDialog.show_error(
                self,
                "Missing Session",
                "Run or open an investigation before querying.",
            )
            return

        try:
            self._bridge.query(
                question=question,
                question_type=self.question_type_combo.currentText().strip().lower(),
                focus=self.focus_input.text().strip() or None,
                limit=int(self.limit_spin.value()),
                session_id=session_id,
            )
        except RuntimeError as exc:
            ErrorDialog.show_error(
                self,
                "Query Already Running",
                str(exc),
                suggestion="Wait for completion or cancel the active operation.",
            )

    def _on_cancel(self) -> None:
        if self._bridge is not None:
            self._bridge.cancel_operation("investigate")
            self._bridge.cancel_operation("query")

    def _on_operation_started(self, operation: str) -> None:
        if operation not in {"investigate", "query"}:
            return
        self.cancel_btn.setEnabled(True)
        if operation == "investigate":
            self.start_btn.setEnabled(False)
        if operation == "query":
            self.query_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"{operation} started")

    def _on_operation_progress(
        self,
        operation: str,
        current: int,
        total: int,
        message: str,
    ) -> None:
        if operation not in {"investigate", "query"}:
            return
        value = int((current / max(total, 1)) * 100)
        self.progress_bar.setValue(max(0, min(100, value)))
        self.progress_label.setText(message or f"{operation}: {current}/{total}")

    def _on_operation_finished(self, operation: str, payload: object) -> None:
        if operation not in {"investigate", "query"}:
            return
        self.start_btn.setEnabled(True)
        self.query_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        self.progress_label.setText(f"{operation} completed")

        data = payload if isinstance(payload, dict) else {"result": payload}
        if operation == "investigate":
            session_id = str(data.get("investigation_id") or data.get("session_id") or "")
            if session_id:
                self.set_current_session(session_id)
            self.results.set_text(json.dumps(data, indent=2, default=str))
            return

        answer = data.get("answer")
        if isinstance(answer, str):
            details = {
                "query_id": data.get("query_id"),
                "session_id": data.get("session_id"),
                "question_type": data.get("question_type"),
                "question": data.get("question"),
                "answer": answer,
            }
            self.results.set_text(json.dumps(details, indent=2, default=str))
        else:
            self.results.set_text(json.dumps(data, indent=2, default=str))

    def _on_operation_error(
        self,
        operation: str,
        error_type: str,
        message: str,
        _details: str,
    ) -> None:
        if operation not in {"investigate", "query"}:
            return
        self.start_btn.setEnabled(True)
        self.query_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText(f"Failed: {error_type} - {message}")

    def _on_operation_cancelled(self, operation: str) -> None:
        if operation not in {"investigate", "query"}:
            return
        self.start_btn.setEnabled(True)
        self.query_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"{operation} cancelled")

