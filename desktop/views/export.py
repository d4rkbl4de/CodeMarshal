"""Export workflow view."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtWidgets

from desktop.widgets import ErrorDialog, ResultsViewer


class ExportView(QtWidgets.QWidget):
    """Preview and export investigation outputs."""

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
        title = QtWidgets.QLabel("Export")
        title.setObjectName("sectionTitle")
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch(1)
        layout.addLayout(header)

        config_group = QtWidgets.QGroupBox("Export Configuration")
        config_form = QtWidgets.QFormLayout(config_group)

        self.session_combo = QtWidgets.QComboBox()
        self.session_combo.setEditable(True)
        self.session_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        config_form.addRow("Session:", self.session_combo)

        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItems(
            ["json", "markdown", "html", "plain", "csv", "jupyter", "pdf", "svg"]
        )
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        config_form.addRow("Format:", self.format_combo)

        include_row = QtWidgets.QHBoxLayout()
        self.include_notes = QtWidgets.QCheckBox("Notes")
        self.include_patterns = QtWidgets.QCheckBox("Patterns")
        self.include_evidence = QtWidgets.QCheckBox("Evidence")
        self.include_evidence.setChecked(True)
        include_row.addWidget(self.include_notes)
        include_row.addWidget(self.include_patterns)
        include_row.addWidget(self.include_evidence)
        include_row.addStretch(1)
        config_form.addRow("Include:", include_row)

        output_row = QtWidgets.QHBoxLayout()
        self.output_input = QtWidgets.QLineEdit()
        self.output_input.setPlaceholderText("Output file path")
        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.clicked.connect(self._on_browse_output)
        output_row.addWidget(self.output_input, stretch=1)
        output_row.addWidget(browse_btn)
        config_form.addRow("Output:", output_row)
        layout.addWidget(config_group)

        actions = QtWidgets.QHBoxLayout()
        self.preview_btn = QtWidgets.QPushButton("Preview")
        self.preview_btn.clicked.connect(self._on_preview)
        self.export_btn = QtWidgets.QPushButton("Export")
        self.export_btn.clicked.connect(self._on_export)
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel)
        actions.addWidget(self.preview_btn)
        actions.addWidget(self.export_btn)
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

        preview_group = QtWidgets.QGroupBox("Export Preview")
        preview_layout = QtWidgets.QVBoxLayout(preview_group)
        self.preview_viewer = ResultsViewer()
        preview_layout.addWidget(self.preview_viewer)
        layout.addWidget(preview_group, stretch=1)

    def set_command_bridge(self, command_bridge: Any) -> None:
        if self._bridge is command_bridge:
            return
        self._bridge = command_bridge
        self._bridge.operation_started.connect(self._on_operation_started)
        self._bridge.operation_progress.connect(self._on_operation_progress)
        self._bridge.operation_finished.connect(self._on_operation_finished)
        self._bridge.operation_error.connect(self._on_operation_error)
        self._bridge.operation_cancelled.connect(self._on_operation_cancelled)

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

    def set_current_session(self, session_id: str | None) -> None:
        self._current_session_id = session_id
        if session_id:
            self.session_combo.setCurrentText(session_id)
            self._suggest_output_path()

    def set_default_export_format(self, format_name: str) -> None:
        idx = self.format_combo.findText(format_name)
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)

    def _on_format_changed(self) -> None:
        self._suggest_output_path()

    def _on_browse_output(self) -> None:
        extension = self._extension_for_format(self.format_combo.currentText().strip())
        start = self.output_input.text().strip() or str(Path(".").resolve())
        file_path, _filter = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Choose Export Output",
            start,
            f"*.{extension};;All Files (*.*)",
        )
        if file_path:
            self.output_input.setText(file_path)

    def _on_preview(self) -> None:
        if self._bridge is None:
            ErrorDialog.show_error(self, "Unavailable", "Command bridge is not initialized.")
            return

        session_id = self.session_combo.currentText().strip() or self._current_session_id
        if not session_id:
            ErrorDialog.show_error(self, "Missing Session", "Choose a session for preview.")
            return

        try:
            self._bridge.preview_export(
                session_id=session_id,
                format_name=self.format_combo.currentText().strip().lower(),
                include_notes=self.include_notes.isChecked(),
                include_patterns=self.include_patterns.isChecked(),
            )
        except RuntimeError as exc:
            ErrorDialog.show_error(
                self,
                "Preview Already Running",
                str(exc),
            )

    def _on_export(self) -> None:
        if self._bridge is None:
            ErrorDialog.show_error(self, "Unavailable", "Command bridge is not initialized.")
            return

        session_id = self.session_combo.currentText().strip() or self._current_session_id
        if not session_id:
            ErrorDialog.show_error(self, "Missing Session", "Choose a session before export.")
            return

        output_path = self.output_input.text().strip()
        if not output_path:
            ErrorDialog.show_error(self, "Missing Output", "Choose an output path.")
            return

        try:
            self._bridge.export(
                session_id=session_id,
                format_name=self.format_combo.currentText().strip().lower(),
                output_path=output_path,
                include_notes=self.include_notes.isChecked(),
                include_patterns=self.include_patterns.isChecked(),
                include_evidence=self.include_evidence.isChecked(),
            )
        except RuntimeError as exc:
            ErrorDialog.show_error(
                self,
                "Export Already Running",
                str(exc),
            )

    def _on_cancel(self) -> None:
        if self._bridge is not None:
            self._bridge.cancel_operation("export_preview")
            self._bridge.cancel_operation("export")

    def _on_operation_started(self, operation: str) -> None:
        if operation not in {"export_preview", "export"}:
            return
        self.cancel_btn.setEnabled(True)
        if operation == "export":
            self.export_btn.setEnabled(False)
        if operation == "export_preview":
            self.preview_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"{operation} started")

    def _on_operation_progress(
        self,
        operation: str,
        current: int,
        total: int,
        message: str,
    ) -> None:
        if operation not in {"export_preview", "export"}:
            return
        value = int((current / max(total, 1)) * 100)
        self.progress_bar.setValue(max(0, min(100, value)))
        self.progress_label.setText(message or f"{operation}: {current}/{total}")

    def _on_operation_finished(self, operation: str, payload: object) -> None:
        if operation not in {"export_preview", "export"}:
            return
        self.cancel_btn.setEnabled(False)
        self.export_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.progress_bar.setValue(100)

        data = payload if isinstance(payload, dict) else {"result": payload}
        if operation == "export_preview":
            self.progress_label.setText("Preview ready")
            preview_text = str(data.get("preview") or "")
            summary = {
                "session_id": data.get("session_id"),
                "format": data.get("format"),
                "observations_count": data.get("observations_count"),
            }
            self.preview_viewer.set_text(
                json.dumps(summary, indent=2, default=str)
                + "\n\n"
                + preview_text
            )
            return

        self.progress_label.setText("Export completed")
        self.preview_viewer.set_text(json.dumps(data, indent=2, default=str))

    def _on_operation_error(
        self,
        operation: str,
        error_type: str,
        message: str,
        _details: str,
    ) -> None:
        if operation not in {"export_preview", "export"}:
            return
        self.cancel_btn.setEnabled(False)
        self.export_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.progress_label.setText(f"Failed: {error_type} - {message}")

    def _on_operation_cancelled(self, operation: str) -> None:
        if operation not in {"export_preview", "export"}:
            return
        self.cancel_btn.setEnabled(False)
        self.export_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"{operation} cancelled")

    def _suggest_output_path(self) -> None:
        current = self.output_input.text().strip()
        if current:
            return
        session_id = self.session_combo.currentText().strip() or self._current_session_id
        if not session_id:
            return
        format_name = self.format_combo.currentText().strip().lower()
        extension = self._extension_for_format(format_name)
        suggested = Path("exports") / f"{session_id}.{extension}"
        self.output_input.setText(str(suggested))

    def _extension_for_format(self, format_name: str) -> str:
        mapping = {
            "json": "json",
            "markdown": "md",
            "html": "html",
            "plain": "txt",
            "csv": "csv",
            "jupyter": "ipynb",
            "pdf": "pdf",
            "svg": "svg",
        }
        return mapping.get(format_name, "txt")

