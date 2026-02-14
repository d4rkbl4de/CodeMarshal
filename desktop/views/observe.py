"""Observe workflow view."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtWidgets

from desktop.widgets import ErrorDialog, ResultsViewer


class ObserveView(QtWidgets.QWidget):
    """Run observation commands with selected eye types."""

    navigate_requested = QtCore.Signal(str)

    def __init__(
        self,
        command_bridge: Any | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._bridge = None
        self._build_ui()
        if command_bridge is not None:
            self.set_command_bridge(command_bridge)

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)

        header = QtWidgets.QHBoxLayout()
        back_btn = QtWidgets.QPushButton("Home")
        back_btn.clicked.connect(lambda: self.navigate_requested.emit("home"))
        title = QtWidgets.QLabel("Observe")
        title.setObjectName("sectionTitle")
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch(1)
        layout.addLayout(header)

        config = QtWidgets.QGroupBox("Observation Configuration")
        form = QtWidgets.QFormLayout(config)

        path_row = QtWidgets.QHBoxLayout()
        self.path_input = QtWidgets.QLineEdit()
        self.path_input.setPlaceholderText("Path to observe")
        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.clicked.connect(self._on_browse)
        path_row.addWidget(self.path_input, stretch=1)
        path_row.addWidget(browse_btn)
        form.addRow("Target Path:", path_row)

        self.session_combo = QtWidgets.QComboBox()
        self.session_combo.setEditable(True)
        self.session_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        form.addRow("Session ID:", self.session_combo)

        eyes_layout = QtWidgets.QGridLayout()
        self._eye_boxes: dict[str, QtWidgets.QCheckBox] = {}
        eye_defs = [
            ("file_sight", "File Sight"),
            ("import_sight", "Import Sight"),
            ("export_sight", "Export Sight"),
            ("boundary_sight", "Boundary Sight"),
            ("encoding_sight", "Encoding Sight"),
        ]
        for index, (value, label) in enumerate(eye_defs):
            box = QtWidgets.QCheckBox(label)
            box.setChecked(value != "encoding_sight")
            self._eye_boxes[value] = box
            eyes_layout.addWidget(box, index // 2, index % 2)
        form.addRow("Eyes:", eyes_layout)
        layout.addWidget(config)

        actions = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Run Observation")
        self.start_btn.clicked.connect(self._on_start)
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel)
        actions.addWidget(self.start_btn)
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

        results_group = QtWidgets.QGroupBox("Observation Results")
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

    def set_known_sessions(self, sessions: list[dict[str, Any]]) -> None:
        current = self.session_combo.currentText()
        self.session_combo.blockSignals(True)
        self.session_combo.clear()
        self.session_combo.addItem("")
        for session in sessions:
            session_id = str(session.get("session_id") or session.get("id") or "")
            if session_id:
                self.session_combo.addItem(session_id)
        self.session_combo.setCurrentText(current)
        self.session_combo.blockSignals(False)

    def set_current_session(self, session_id: str | None) -> None:
        self.session_combo.setCurrentText(session_id or "")

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

    def _on_start(self) -> None:
        if self._bridge is None:
            ErrorDialog.show_error(
                self,
                "Observe Unavailable",
                "Command bridge is not initialized.",
            )
            return

        path_value = self.path_input.text().strip()
        if not path_value:
            ErrorDialog.show_error(self, "Missing Path", "Select a path to observe.")
            return
        if not Path(path_value).exists():
            ErrorDialog.show_error(self, "Invalid Path", f"Path does not exist: {path_value}")
            return

        eyes = [name for name, box in self._eye_boxes.items() if box.isChecked()]
        if not eyes:
            ErrorDialog.show_error(
                self,
                "No Eyes Selected",
                "Select at least one observation eye before running.",
            )
            return

        session_id = self.session_combo.currentText().strip() or None
        try:
            self._bridge.observe(path=path_value, eye_types=eyes, session_id=session_id)
        except RuntimeError as exc:
            ErrorDialog.show_error(
                self,
                "Observe Already Running",
                str(exc),
                suggestion="Wait for completion or cancel the active operation.",
            )

    def _on_cancel(self) -> None:
        if self._bridge is not None:
            self._bridge.cancel_operation("observe")

    def _on_operation_started(self, operation: str) -> None:
        if operation != "observe":
            return
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting observation...")

    def _on_operation_progress(
        self,
        operation: str,
        current: int,
        total: int,
        message: str,
    ) -> None:
        if operation != "observe":
            return
        value = int((current / max(total, 1)) * 100)
        self.progress_bar.setValue(max(0, min(100, value)))
        self.progress_label.setText(message or f"{current}/{total}")

    def _on_operation_finished(self, operation: str, payload: object) -> None:
        if operation != "observe":
            return
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        self.progress_label.setText("Observation completed")
        data = payload if isinstance(payload, dict) else {"result": payload}
        self.results.set_text(json.dumps(data, indent=2, default=str))
        session_id = str(data.get("session_id") or "")
        if session_id:
            self.session_combo.setCurrentText(session_id)

    def _on_operation_error(
        self,
        operation: str,
        error_type: str,
        message: str,
        _details: str,
    ) -> None:
        if operation != "observe":
            return
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText(f"Failed: {error_type} - {message}")

    def _on_operation_cancelled(self, operation: str) -> None:
        if operation != "observe":
            return
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText("Observation cancelled")
        self.progress_bar.setValue(0)

