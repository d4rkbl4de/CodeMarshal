"""Patterns workflow view."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtWidgets

from desktop.widgets import (
    ErrorDialog,
    HintPanel,
    ResultsViewer,
    apply_accessible,
    clear_invalid,
    mark_invalid,
)


class PatternsView(QtWidgets.QWidget):
    """Browse pattern library and run scans."""

    navigate_requested = QtCore.Signal(str)

    def __init__(
        self,
        command_bridge: Any | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._bridge = None
        self._current_session_id: str | None = None
        self._last_scan_result: dict[str, Any] | None = None
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
        title = QtWidgets.QLabel("Patterns")
        title.setObjectName("sectionTitle")
        header.addWidget(self.back_btn)
        header.addWidget(title)
        header.addStretch(1)
        layout.addLayout(header)

        self.hint_panel = HintPanel(
            "Pattern Scan Guidance",
            (
                "Load the library first, then narrow by category and severity.\n"
                "Use smaller glob scopes on large repositories for faster scans."
            ),
        )
        layout.addWidget(self.hint_panel)

        library_group = QtWidgets.QGroupBox("Pattern Library")
        library_layout = QtWidgets.QVBoxLayout(library_group)

        controls = QtWidgets.QHBoxLayout()
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItems(
            ["all", "security", "performance", "style", "architecture"]
        )
        apply_accessible(self.category_combo, name="Pattern category filter")
        self.severity_filter = QtWidgets.QComboBox()
        self.severity_filter.addItems(["all", "critical", "warning", "info"])
        self.severity_filter.currentTextChanged.connect(self._apply_table_filters)
        apply_accessible(self.severity_filter, name="Pattern severity filter")
        self.show_disabled = QtWidgets.QCheckBox("Show disabled")
        apply_accessible(self.show_disabled, name="Show disabled patterns")
        self.load_btn = QtWidgets.QPushButton("Load Library")
        self.load_btn.clicked.connect(self._on_load_library)
        apply_accessible(self.load_btn, name="Load pattern library")
        controls.addWidget(QtWidgets.QLabel("Category:"))
        controls.addWidget(self.category_combo)
        controls.addWidget(QtWidgets.QLabel("Severity:"))
        controls.addWidget(self.severity_filter)
        controls.addWidget(self.show_disabled)
        controls.addWidget(self.load_btn)
        controls.addStretch(1)
        library_layout.addLayout(controls)

        selection_row = QtWidgets.QHBoxLayout()
        self.select_all_btn = QtWidgets.QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all_patterns)
        self.select_none_btn = QtWidgets.QPushButton("Select None")
        self.select_none_btn.clicked.connect(self._select_no_patterns)
        self.invert_btn = QtWidgets.QPushButton("Invert Selection")
        self.invert_btn.clicked.connect(self._invert_pattern_selection)
        apply_accessible(self.select_all_btn, name="Select all patterns")
        apply_accessible(self.select_none_btn, name="Clear selected patterns")
        apply_accessible(self.invert_btn, name="Invert selected patterns")
        selection_row.addWidget(self.select_all_btn)
        selection_row.addWidget(self.select_none_btn)
        selection_row.addWidget(self.invert_btn)
        selection_row.addStretch(1)
        library_layout.addLayout(selection_row)

        self.pattern_table = QtWidgets.QTableWidget(0, 6)
        self.pattern_table.setHorizontalHeaderLabels(
            ["Use", "Pattern ID", "Name", "Severity", "Tags", "Enabled"]
        )
        self.pattern_table.verticalHeader().setVisible(False)
        self.pattern_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.pattern_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.pattern_table.horizontalHeader().setStretchLastSection(True)
        apply_accessible(
            self.pattern_table,
            name="Pattern library table",
            description="List of patterns available for scanning.",
        )
        library_layout.addWidget(self.pattern_table)
        layout.addWidget(library_group, stretch=1)

        scan_group = QtWidgets.QGroupBox("Scan Configuration")
        scan_form = QtWidgets.QFormLayout(scan_group)

        path_row = QtWidgets.QHBoxLayout()
        self.path_input = QtWidgets.QLineEdit()
        self.path_input.setPlaceholderText("Target path for scan")
        self.path_input.textChanged.connect(self._clear_validation)
        apply_accessible(self.path_input, name="Pattern scan target path")
        self.browse_btn = QtWidgets.QPushButton("Browse")
        self.browse_btn.clicked.connect(self._on_browse)
        apply_accessible(self.browse_btn, name="Browse pattern scan target")
        path_row.addWidget(self.path_input, stretch=1)
        path_row.addWidget(self.browse_btn)
        scan_form.addRow("Path:", path_row)

        self.session_combo = QtWidgets.QComboBox()
        self.session_combo.setEditable(True)
        self.session_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        apply_accessible(self.session_combo, name="Pattern scan session selector")
        scan_form.addRow("Session ID:", self.session_combo)

        self.glob_input = QtWidgets.QLineEdit("*.py")
        apply_accessible(self.glob_input, name="Pattern scan glob filter")
        scan_form.addRow("Glob:", self.glob_input)

        self.max_files_spin = QtWidgets.QSpinBox()
        self.max_files_spin.setRange(1, 200000)
        self.max_files_spin.setValue(10000)
        apply_accessible(self.max_files_spin, name="Pattern scan max files")
        scan_form.addRow("Max Files:", self.max_files_spin)

        self.changed_files_only = QtWidgets.QCheckBox("Scan changed files only")
        self.changed_files_only.setEnabled(False)
        self.changed_files_only.setToolTip(
            "Will be enabled when VCS file-diff integration is available."
        )
        apply_accessible(
            self.changed_files_only,
            name="Scan changed files only",
            description="Disabled until VCS diff integration is available.",
        )
        scan_form.addRow("", self.changed_files_only)
        layout.addWidget(scan_group)

        actions = QtWidgets.QHBoxLayout()
        self.scan_btn = QtWidgets.QPushButton("Run Pattern Scan")
        self.scan_btn.setProperty("variant", "primary")
        self.scan_btn.clicked.connect(self._on_run_scan)
        apply_accessible(self.scan_btn, name="Run pattern scan")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel)
        apply_accessible(self.cancel_btn, name="Cancel pattern operation")
        actions.addWidget(self.scan_btn)
        actions.addWidget(self.cancel_btn)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.validation_label = QtWidgets.QLabel("")
        self.validation_label.setObjectName("validationError")
        self.validation_label.setWordWrap(True)
        self.validation_label.setVisible(False)
        apply_accessible(self.validation_label, name="Pattern validation message")
        layout.addWidget(self.validation_label)

        progress_row = QtWidgets.QHBoxLayout()
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label = QtWidgets.QLabel("Idle")
        apply_accessible(self.progress_label, name="Pattern progress status")
        progress_row.addWidget(self.progress_bar, stretch=1)
        progress_row.addWidget(self.progress_label)
        layout.addLayout(progress_row)

        self.summary_label = QtWidgets.QLabel("No scan results yet.")
        self.summary_label.setObjectName("subtitle")
        apply_accessible(self.summary_label, name="Pattern scan summary")
        layout.addWidget(self.summary_label)

        results_group = QtWidgets.QGroupBox("Scan Results")
        results_layout = QtWidgets.QVBoxLayout(results_group)
        self.results = ResultsViewer()
        results_layout.addWidget(self.results)
        layout.addWidget(results_group, stretch=1)

        self.setTabOrder(self.category_combo, self.severity_filter)
        self.setTabOrder(self.severity_filter, self.show_disabled)
        self.setTabOrder(self.show_disabled, self.load_btn)
        self.setTabOrder(self.load_btn, self.pattern_table)
        self.setTabOrder(self.pattern_table, self.path_input)
        self.setTabOrder(self.path_input, self.browse_btn)
        self.setTabOrder(self.browse_btn, self.session_combo)
        self.setTabOrder(self.session_combo, self.glob_input)
        self.setTabOrder(self.glob_input, self.max_files_spin)
        self.setTabOrder(self.max_files_spin, self.scan_btn)
        self.setTabOrder(self.scan_btn, self.cancel_btn)

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

    def _on_browse(self) -> None:
        start = self.path_input.text().strip() or str(Path(".").resolve())
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose Target", start)
        if path:
            self.path_input.setText(path)

    def _on_load_library(self) -> None:
        if self._bridge is None:
            ErrorDialog.show_error(self, "Unavailable", "Command bridge is not initialized.")
            return

        category = self.category_combo.currentText().strip().lower()
        try:
            self._bridge.pattern_list(
                category=None if category == "all" else category,
                show_disabled=self.show_disabled.isChecked(),
            )
        except RuntimeError as exc:
            ErrorDialog.show_error(
                self,
                "Library Load Already Running",
                str(exc),
            )

    def _on_run_scan(self) -> None:
        if self._bridge is None:
            ErrorDialog.show_error(self, "Unavailable", "Command bridge is not initialized.")
            return

        path_value = self.path_input.text().strip()
        if not path_value:
            self._set_validation("Select a path to scan.", self.path_input)
            return
        if not Path(path_value).exists():
            self._set_validation(f"Path does not exist: {path_value}", self.path_input)
            return
        self._clear_validation()

        selected_patterns = self._selected_pattern_ids()
        category = self.category_combo.currentText().strip().lower()
        session_id = self.session_combo.currentText().strip() or self._current_session_id
        try:
            self._bridge.pattern_scan(
                path=path_value,
                category=None if category == "all" else category,
                pattern_ids=selected_patterns or None,
                glob=self.glob_input.text().strip() or "*",
                max_files=int(self.max_files_spin.value()),
                session_id=session_id,
            )
        except RuntimeError as exc:
            ErrorDialog.show_error(
                self,
                "Pattern Scan Already Running",
                str(exc),
                suggestion="Wait for completion or cancel the active scan.",
            )

    def _selected_pattern_ids(self) -> list[str]:
        selected: list[str] = []
        for row in range(self.pattern_table.rowCount()):
            check_item = self.pattern_table.item(row, 0)
            id_item = self.pattern_table.item(row, 1)
            if check_item and id_item and check_item.checkState() == QtCore.Qt.Checked:
                pattern_id = id_item.text().strip()
                if pattern_id:
                    selected.append(pattern_id)
        return selected

    def _on_cancel(self) -> None:
        if self._bridge is not None:
            self._bridge.cancel_operation("pattern_list")
            self._bridge.cancel_operation("pattern_scan")

    def _on_operation_started(self, operation: str) -> None:
        if operation not in {"pattern_list", "pattern_scan"}:
            return
        self.cancel_btn.setEnabled(True)
        if operation == "pattern_scan":
            self.scan_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"{operation} started")

    def _on_operation_progress(
        self,
        operation: str,
        current: int,
        total: int,
        message: str,
    ) -> None:
        if operation not in {"pattern_list", "pattern_scan"}:
            return
        value = int((current / max(total, 1)) * 100)
        self.progress_bar.setValue(max(0, min(100, value)))
        self.progress_label.setText(message or f"{operation}: {current}/{total}")

    def _on_operation_finished(self, operation: str, payload: object) -> None:
        if operation not in {"pattern_list", "pattern_scan"}:
            return
        self.scan_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(100)

        data = payload if isinstance(payload, dict) else {"result": payload}
        if operation == "pattern_list":
            self.progress_label.setText("Pattern library loaded")
            self._populate_pattern_table(data.get("patterns", []))
            self.results.set_sections(
                f"Loaded {len(data.get('patterns', []))} patterns.",
                json.dumps(data, indent=2, default=str),
            )
            return

        self.progress_label.setText("Pattern scan completed")
        self._last_scan_result = data
        summary = {
            "patterns_scanned": data.get("patterns_scanned"),
            "files_scanned": data.get("files_scanned"),
            "matches_found": data.get("matches_found"),
            "scan_time_ms": data.get("scan_time_ms"),
            "errors": data.get("errors", []),
            "matches_preview": data.get("matches", [])[:100],
        }
        self.summary_label.setText(
            f"Matches: {int(data.get('matches_found') or 0)} | "
            f"Files: {int(data.get('files_scanned') or 0)}"
        )
        self.results.set_sections(
            json.dumps(
                {
                    "patterns_scanned": summary["patterns_scanned"],
                    "files_scanned": summary["files_scanned"],
                    "matches_found": summary["matches_found"],
                },
                indent=2,
                default=str,
            ),
            json.dumps(summary, indent=2, default=str),
        )

    def _populate_pattern_table(self, patterns: list[dict[str, Any]]) -> None:
        self.pattern_table.setRowCount(0)
        for row, pattern in enumerate(patterns):
            self.pattern_table.insertRow(row)

            check_item = QtWidgets.QTableWidgetItem()
            check_item.setFlags(
                QtCore.Qt.ItemIsEnabled
                | QtCore.Qt.ItemIsSelectable
                | QtCore.Qt.ItemIsUserCheckable
            )
            check_item.setCheckState(QtCore.Qt.Checked)
            self.pattern_table.setItem(row, 0, check_item)

            pattern_id = str(pattern.get("id") or "")
            name = str(pattern.get("name") or "")
            severity = str(pattern.get("severity") or "unknown")
            tags = ", ".join(str(tag) for tag in pattern.get("tags", [])[:4])
            enabled = str(bool(pattern.get("enabled", True)))

            self.pattern_table.setItem(row, 1, QtWidgets.QTableWidgetItem(pattern_id))
            self.pattern_table.setItem(row, 2, QtWidgets.QTableWidgetItem(name))
            self.pattern_table.setItem(row, 3, QtWidgets.QTableWidgetItem(severity))
            self.pattern_table.setItem(row, 4, QtWidgets.QTableWidgetItem(tags))
            self.pattern_table.setItem(row, 5, QtWidgets.QTableWidgetItem(enabled))

        self.pattern_table.resizeColumnsToContents()
        self._apply_table_filters()

    def _on_operation_error(
        self,
        operation: str,
        error_type: str,
        message: str,
        _details: str,
    ) -> None:
        if operation not in {"pattern_list", "pattern_scan"}:
            return
        self.scan_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText(f"Failed: {error_type} - {message}")

    def _on_operation_cancelled(self, operation: str) -> None:
        if operation not in {"pattern_list", "pattern_scan"}:
            return
        self.scan_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"{operation} cancelled")

    def _select_all_patterns(self) -> None:
        for row in range(self.pattern_table.rowCount()):
            item = self.pattern_table.item(row, 0)
            if item:
                item.setCheckState(QtCore.Qt.Checked)

    def _select_no_patterns(self) -> None:
        for row in range(self.pattern_table.rowCount()):
            item = self.pattern_table.item(row, 0)
            if item:
                item.setCheckState(QtCore.Qt.Unchecked)

    def _invert_pattern_selection(self) -> None:
        for row in range(self.pattern_table.rowCount()):
            item = self.pattern_table.item(row, 0)
            if item:
                item.setCheckState(
                    QtCore.Qt.Unchecked
                    if item.checkState() == QtCore.Qt.Checked
                    else QtCore.Qt.Checked
                )

    def _apply_table_filters(self) -> None:
        selected_severity = self.severity_filter.currentText().strip().lower()
        for row in range(self.pattern_table.rowCount()):
            severity_item = self.pattern_table.item(row, 3)
            severity = (severity_item.text().strip().lower() if severity_item else "")
            hidden = selected_severity != "all" and severity != selected_severity
            self.pattern_table.setRowHidden(row, hidden)

    def set_busy(self, is_busy: bool) -> None:
        if is_busy:
            self.scan_btn.setEnabled(False)
        else:
            self.scan_btn.setEnabled(True)

    def trigger_primary_action(self) -> None:
        if self.scan_btn.isEnabled():
            self._on_run_scan()

    def set_hints_enabled(self, enabled: bool) -> None:
        self._hints_enabled = bool(enabled)
        self.hint_panel.setVisible(self._hints_enabled)

    def _set_validation(self, message: str, widget: QtWidgets.QWidget | None = None) -> None:
        mark_invalid(widget, self.validation_label, message)

    def _clear_validation(self, *_args: object) -> None:
        clear_invalid((self.path_input,), self.validation_label)
