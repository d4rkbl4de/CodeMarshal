"""Export workflow view."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets

from desktop.widgets import (
    ErrorDialog,
    HintPanel,
    ResultsViewer,
    apply_accessible,
    clear_invalid,
    mark_invalid,
)


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
        self._last_preview_request: dict[str, Any] | None = None
        self._hints_enabled = True
        self._build_ui()
        if command_bridge is not None:
            self.set_command_bridge(command_bridge)

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)

        header = QtWidgets.QHBoxLayout()
        self.back_btn = QtWidgets.QPushButton("Home")
        self.back_btn.clicked.connect(lambda: self.navigate_requested.emit("home"))
        apply_accessible(self.back_btn, name="Return to Home view")
        title = QtWidgets.QLabel("Export")
        title.setObjectName("sectionTitle")
        header.addWidget(self.back_btn)
        header.addWidget(title)
        header.addStretch(1)
        layout.addLayout(header)

        self.hint_panel = HintPanel(
            "Export Tips",
            (
                "Use Preview before Export on large sessions.\n"
                "If preview is truncated, use Load Full Preview before writing files."
            ),
        )
        layout.addWidget(self.hint_panel)

        config_group = QtWidgets.QGroupBox("Export Configuration")
        config_form = QtWidgets.QFormLayout(config_group)

        self.session_combo = QtWidgets.QComboBox()
        self.session_combo.setEditable(True)
        self.session_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        self.session_combo.currentTextChanged.connect(self._suggest_output_path)
        self.session_combo.currentTextChanged.connect(self._clear_validation)
        apply_accessible(
            self.session_combo,
            name="Export session selector",
            description="Select investigation session to export.",
        )
        config_form.addRow("Session:", self.session_combo)

        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItems(
            ["json", "markdown", "html", "plain", "csv", "jupyter", "pdf", "svg"]
        )
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        apply_accessible(self.format_combo, name="Export format selector")
        config_form.addRow("Format:", self.format_combo)

        include_row = QtWidgets.QHBoxLayout()
        self.include_notes = QtWidgets.QCheckBox("Notes")
        self.include_patterns = QtWidgets.QCheckBox("Patterns")
        self.include_evidence = QtWidgets.QCheckBox("Evidence")
        self.include_evidence.setChecked(True)
        apply_accessible(self.include_notes, name="Include notes in export")
        apply_accessible(self.include_patterns, name="Include patterns in export")
        apply_accessible(self.include_evidence, name="Include evidence in export")
        include_row.addWidget(self.include_notes)
        include_row.addWidget(self.include_patterns)
        include_row.addWidget(self.include_evidence)
        include_row.addStretch(1)
        config_form.addRow("Include:", include_row)

        output_row = QtWidgets.QHBoxLayout()
        self.output_input = QtWidgets.QLineEdit()
        self.output_input.setPlaceholderText("Output file path")
        self.output_input.textChanged.connect(self._clear_validation)
        apply_accessible(self.output_input, name="Export output file path")
        self.browse_btn = QtWidgets.QPushButton("Browse")
        self.browse_btn.clicked.connect(self._on_browse_output)
        apply_accessible(self.browse_btn, name="Browse export output path")
        output_row.addWidget(self.output_input, stretch=1)
        output_row.addWidget(self.browse_btn)
        config_form.addRow("Output:", output_row)
        layout.addWidget(config_group)

        actions = QtWidgets.QHBoxLayout()
        self.preview_btn = QtWidgets.QPushButton("Preview")
        self.preview_btn.clicked.connect(self._on_preview)
        apply_accessible(self.preview_btn, name="Preview export output")
        self.full_preview_btn = QtWidgets.QPushButton("Load Full Preview")
        self.full_preview_btn.setEnabled(False)
        self.full_preview_btn.clicked.connect(self._on_load_full_preview)
        apply_accessible(self.full_preview_btn, name="Load full export preview")
        self.export_btn = QtWidgets.QPushButton("Export")
        self.export_btn.setProperty("variant", "primary")
        self.export_btn.clicked.connect(self._on_export)
        apply_accessible(self.export_btn, name="Run export")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel)
        apply_accessible(self.cancel_btn, name="Cancel export operation")
        self.open_folder_btn = QtWidgets.QPushButton("Open Folder")
        self.open_folder_btn.setEnabled(False)
        self.open_folder_btn.clicked.connect(self._open_export_folder)
        apply_accessible(self.open_folder_btn, name="Open exported file folder")
        self.copy_path_btn = QtWidgets.QPushButton("Copy Path")
        self.copy_path_btn.setEnabled(False)
        self.copy_path_btn.clicked.connect(self._copy_output_path)
        apply_accessible(self.copy_path_btn, name="Copy export output path")
        actions.addWidget(self.preview_btn)
        actions.addWidget(self.full_preview_btn)
        actions.addWidget(self.export_btn)
        actions.addWidget(self.open_folder_btn)
        actions.addWidget(self.copy_path_btn)
        actions.addWidget(self.cancel_btn)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.validation_label = QtWidgets.QLabel("")
        self.validation_label.setObjectName("validationError")
        self.validation_label.setWordWrap(True)
        self.validation_label.setVisible(False)
        apply_accessible(self.validation_label, name="Export validation message")
        layout.addWidget(self.validation_label)

        progress_row = QtWidgets.QHBoxLayout()
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label = QtWidgets.QLabel("Idle")
        apply_accessible(self.progress_label, name="Export progress status")
        progress_row.addWidget(self.progress_bar, stretch=1)
        progress_row.addWidget(self.progress_label)
        layout.addLayout(progress_row)

        preview_group = QtWidgets.QGroupBox("Export Preview")
        preview_layout = QtWidgets.QVBoxLayout(preview_group)
        self.preview_viewer = ResultsViewer()
        preview_layout.addWidget(self.preview_viewer)
        layout.addWidget(preview_group, stretch=1)

        self.setTabOrder(self.session_combo, self.format_combo)
        self.setTabOrder(self.format_combo, self.include_notes)
        self.setTabOrder(self.include_notes, self.include_patterns)
        self.setTabOrder(self.include_patterns, self.include_evidence)
        self.setTabOrder(self.include_evidence, self.output_input)
        self.setTabOrder(self.output_input, self.browse_btn)
        self.setTabOrder(self.browse_btn, self.preview_btn)
        self.setTabOrder(self.preview_btn, self.full_preview_btn)
        self.setTabOrder(self.full_preview_btn, self.export_btn)
        self.setTabOrder(self.export_btn, self.open_folder_btn)
        self.setTabOrder(self.open_folder_btn, self.copy_path_btn)
        self.setTabOrder(self.copy_path_btn, self.cancel_btn)

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
            self._set_validation("Choose a session for preview.", self.session_combo)
            return
        self._clear_validation()

        try:
            self._last_preview_request = {
                "session_id": session_id,
                "format_name": self.format_combo.currentText().strip().lower(),
                "include_notes": self.include_notes.isChecked(),
                "include_patterns": self.include_patterns.isChecked(),
            }
            self._bridge.preview_export(
                session_id=session_id,
                format_name=self.format_combo.currentText().strip().lower(),
                include_notes=self.include_notes.isChecked(),
                include_patterns=self.include_patterns.isChecked(),
                preview_limit=4000,
            )
        except RuntimeError as exc:
            ErrorDialog.show_error(
                self,
                "Preview Already Running",
                str(exc),
            )

    def _on_load_full_preview(self) -> None:
        if self._bridge is None or not self._last_preview_request:
            return
        try:
            self._bridge.preview_export(
                **self._last_preview_request,
                preview_limit=None,
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
            self._set_validation("Choose a session before export.", self.session_combo)
            return

        output_path = self.output_input.text().strip()
        if not output_path:
            self._set_validation("Choose an output path.", self.output_input)
            return
        output_parent = Path(output_path).resolve().parent
        if not output_parent.exists():
            self._set_validation(
                f"Output directory does not exist: {output_parent}",
                self.output_input,
            )
            return
        self._clear_validation()
        output_file = Path(output_path).resolve()
        if output_file.exists():
            answer = QtWidgets.QMessageBox.question(
                self,
                "Overwrite Existing File",
                f"Output file already exists:\n{output_file}\n\nOverwrite?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if answer != QtWidgets.QMessageBox.Yes:
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
        self.open_folder_btn.setEnabled(False)
        self.copy_path_btn.setEnabled(False)
        self.full_preview_btn.setEnabled(False)
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
                "preview_truncated": bool(data.get("preview_truncated")),
            }
            self.full_preview_btn.setEnabled(bool(data.get("preview_truncated")))
            self.preview_viewer.set_sections(
                json.dumps(summary, indent=2, default=str),
                preview_text,
            )
            return

        self.progress_label.setText("Export completed")
        self.preview_viewer.set_sections(
            f"Exported to: {data.get('path', 'unknown')}",
            json.dumps(data, indent=2, default=str),
        )
        self.open_folder_btn.setEnabled(True)
        self.copy_path_btn.setEnabled(True)

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
        self.full_preview_btn.setEnabled(False)
        self.progress_label.setText(f"Failed: {error_type} - {message}")

    def _on_operation_cancelled(self, operation: str) -> None:
        if operation not in {"export_preview", "export"}:
            return
        self.cancel_btn.setEnabled(False)
        self.export_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.full_preview_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"{operation} cancelled")

    def _suggest_output_path(self, _value: str | None = None) -> None:
        session_id = self.session_combo.currentText().strip() or self._current_session_id
        if not session_id:
            return
        format_name = self.format_combo.currentText().strip().lower()
        if self._bridge is not None and hasattr(self._bridge, "facade"):
            try:
                suggested = self._bridge.facade.resolve_default_export_path(
                    session_id, format_name
                )
            except Exception:
                suggested = str(
                    Path("exports")
                    / f"{session_id}.{self._extension_for_format(format_name)}"
                )
        else:
            suggested = str(
                Path("exports") / f"{session_id}.{self._extension_for_format(format_name)}"
            )
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

    def _open_export_folder(self) -> None:
        path_value = self.output_input.text().strip()
        if not path_value:
            return
        output = Path(path_value).resolve()
        target = output.parent if output.suffix else output
        url = QtCore.QUrl.fromLocalFile(str(target))
        QtGui.QDesktopServices.openUrl(url)

    def _copy_output_path(self) -> None:
        path_value = self.output_input.text().strip()
        if not path_value:
            return
        QtWidgets.QApplication.clipboard().setText(str(Path(path_value).resolve()))

    def set_busy(self, is_busy: bool) -> None:
        if is_busy:
            self.preview_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
        else:
            self.preview_btn.setEnabled(True)
            self.export_btn.setEnabled(True)

    def trigger_primary_action(self) -> None:
        if self.export_btn.isEnabled():
            self._on_export()

    def set_hints_enabled(self, enabled: bool) -> None:
        self._hints_enabled = bool(enabled)
        self.hint_panel.setVisible(self._hints_enabled)

    def _set_validation(self, message: str, widget: QtWidgets.QWidget | None = None) -> None:
        mark_invalid(widget, self.validation_label, message)

    def _clear_validation(self, *_args: object) -> None:
        clear_invalid((self.output_input, self.session_combo), self.validation_label)
