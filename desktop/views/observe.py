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
    preset_changed = QtCore.Signal(str)

    def __init__(
        self,
        command_bridge: Any | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._bridge = None
        self._busy = False
        self._last_request: dict[str, Any] | None = None
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

        self.preset_combo = QtWidgets.QComboBox()
        self.preset_combo.addItems(
            ["Fast Scan", "Dependency Focus", "Full Trace", "Custom"]
        )
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        form.addRow("Preset:", self.preset_combo)

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
            box.toggled.connect(self._on_eye_toggled)
            self._eye_boxes[value] = box
            eyes_layout.addWidget(box, index // 2, index % 2)
        form.addRow("Eyes:", eyes_layout)
        layout.addWidget(config)

        actions = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Run Observation")
        self.start_btn.clicked.connect(self._on_start)
        self.retry_btn = QtWidgets.QPushButton("Retry Last")
        self.retry_btn.setEnabled(False)
        self.retry_btn.clicked.connect(self._on_retry)
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel)
        actions.addWidget(self.start_btn)
        actions.addWidget(self.retry_btn)
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

    def set_preset(self, preset_name: str) -> None:
        if not preset_name:
            return
        if self.preset_combo.findText(preset_name) < 0:
            return
        self.preset_combo.setCurrentText(preset_name)

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
            self._last_request = {
                "path": path_value,
                "eye_types": list(eyes),
                "session_id": session_id,
            }
            self._bridge.observe(path=path_value, eye_types=eyes, session_id=session_id)
        except RuntimeError as exc:
            ErrorDialog.show_error(
                self,
                "Observe Already Running",
                str(exc),
                suggestion="Wait for completion or cancel the active operation.",
            )

    def _on_retry(self) -> None:
        if self._bridge is None or not self._last_request:
            return
        try:
            self._bridge.observe(**self._last_request)
        except RuntimeError as exc:
            ErrorDialog.show_error(
                self,
                "Observe Already Running",
                str(exc),
                suggestion="Wait for completion or cancel the active operation.",
            )

    def _on_preset_changed(self, preset_name: str) -> None:
        presets = {
            "Fast Scan": {"file_sight", "boundary_sight"},
            "Dependency Focus": {"import_sight", "export_sight", "boundary_sight"},
            "Full Trace": set(self._eye_boxes.keys()),
        }
        selected = presets.get(preset_name)
        if selected is None:
            return
        for key, box in self._eye_boxes.items():
            box.blockSignals(True)
            box.setChecked(key in selected)
            box.blockSignals(False)
        self.preset_changed.emit(preset_name)

    def _on_eye_toggled(self) -> None:
        selected = {name for name, box in self._eye_boxes.items() if box.isChecked()}
        preset = "Custom"
        if selected == {"file_sight", "boundary_sight"}:
            preset = "Fast Scan"
        elif selected == {"import_sight", "export_sight", "boundary_sight"}:
            preset = "Dependency Focus"
        elif selected == set(self._eye_boxes.keys()):
            preset = "Full Trace"

        if self.preset_combo.currentText() != preset:
            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentText(preset)
            self.preset_combo.blockSignals(False)

    def _on_cancel(self) -> None:
        if self._bridge is not None:
            self._bridge.cancel_operation("observe")

    def _on_operation_started(self, operation: str) -> None:
        if operation != "observe":
            return
        self.start_btn.setEnabled(False)
        self.retry_btn.setEnabled(False)
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
        self.retry_btn.setEnabled(self._last_request is not None)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        self.progress_label.setText("Observation completed")
        data = payload if isinstance(payload, dict) else {"result": payload}
        summary = {
            "session_id": data.get("session_id"),
            "observations_count": data.get("observations_count"),
            "observation_id": data.get("observation_id"),
            "status": data.get("status"),
        }
        self.results.set_sections(
            json.dumps(summary, indent=2, default=str),
            json.dumps(data, indent=2, default=str),
        )
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
        self.retry_btn.setEnabled(self._last_request is not None)
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText(f"Failed: {error_type} - {message}")

    def _on_operation_cancelled(self, operation: str) -> None:
        if operation != "observe":
            return
        self.start_btn.setEnabled(True)
        self.retry_btn.setEnabled(self._last_request is not None)
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText("Observation cancelled")
        self.progress_bar.setValue(0)

    def set_busy(self, is_busy: bool) -> None:
        self._busy = bool(is_busy)
        if is_busy:
            self.start_btn.setEnabled(False)
        else:
            self.start_btn.setEnabled(True)
            self.retry_btn.setEnabled(self._last_request is not None)

    def trigger_primary_action(self) -> None:
        if self.start_btn.isEnabled():
            self._on_start()
