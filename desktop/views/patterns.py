"""Patterns workflow view."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtWidgets

from patterns.templates import PatternTemplateRegistry

from desktop.widgets import (
    ActionStrip,
    ErrorDialog,
    HintPanel,
    MarketplacePanel,
    PageScaffold,
    ResultsViewer,
    SectionHeader,
    TemplatesPanel,
    apply_accessible,
    clear_invalid,
    mark_invalid,
)


class PatternsView(QtWidgets.QWidget):
    """Browse pattern library and run scans."""

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
        self._last_scan_result: dict[str, Any] | None = None
        self._hints_enabled = True
        self._build_ui()
        if command_bridge is not None:
            self.set_command_bridge(command_bridge)

    def _template_ids(self) -> list[str]:
        try:
            registry = PatternTemplateRegistry()
            items = [template.id for template in registry.list_templates()]
            return items or ["security.keyword_assignment"]
        except Exception:
            return ["security.keyword_assignment"]

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.page_scaffold = PageScaffold(default_ratio=0.56, narrow_breakpoint=1360)
        self.page_scaffold.splitter_ratio_changed.connect(
            self.layout_splitter_ratio_changed.emit
        )
        layout.addWidget(self.page_scaffold)

        header = SectionHeader(
            "Patterns",
            "Load pattern libraries and run targeted scans.",
        )
        self.page_scaffold.set_header_widget(header)

        form_layout = self.page_scaffold.form_layout
        results_layout = self.page_scaffold.results_layout

        self.hint_panel = HintPanel(
            "Pattern Scan Guidance",
            (
                "Load the library first, then narrow by category and severity.\n"
                "Use smaller glob scopes on large repositories for faster scans."
            ),
        )
        form_layout.addWidget(self.hint_panel)

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
        form_layout.addWidget(library_group, stretch=1)

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
        form_layout.addWidget(scan_group)

        marketplace_group = QtWidgets.QGroupBox("Marketplace & Templates")
        marketplace_layout = QtWidgets.QVBoxLayout(marketplace_group)
        marketplace_layout.setContentsMargins(8, 8, 8, 8)
        marketplace_layout.setSpacing(8)

        self.marketplace_panel = MarketplacePanel()
        self.templates_panel = TemplatesPanel(template_ids=self._template_ids())
        self.marketplace_panel.search_marketplace_btn.clicked.connect(self._on_search_marketplace)
        self.marketplace_panel.apply_pattern_btn.clicked.connect(self._on_apply_pattern)
        self.marketplace_panel.share_pattern_btn.clicked.connect(self._on_share_pattern)
        self.templates_panel.create_pattern_btn.clicked.connect(self._on_create_pattern)

        marketplace_layout.addWidget(self.marketplace_panel)
        marketplace_layout.addWidget(self.templates_panel)

        # Backward-compatible attribute aliases expected by existing tests.
        self.marketplace_query_input = self.marketplace_panel.marketplace_query_input
        self.marketplace_tag_input = self.marketplace_panel.marketplace_tag_input
        self.search_marketplace_btn = self.marketplace_panel.search_marketplace_btn
        self.apply_pattern_input = self.marketplace_panel.apply_pattern_input
        self.apply_pattern_btn = self.marketplace_panel.apply_pattern_btn
        self.share_pattern_input = self.marketplace_panel.share_pattern_input
        self.share_bundle_output_input = self.marketplace_panel.share_bundle_output_input
        self.share_pattern_btn = self.marketplace_panel.share_pattern_btn
        self.template_combo = self.templates_panel.template_combo
        self.template_values_input = self.templates_panel.template_values_input
        self.create_pattern_btn = self.templates_panel.create_pattern_btn
        self.create_pattern_id_input = self.templates_panel.create_pattern_id_input
        self.create_bundle_output_input = self.templates_panel.create_bundle_output_input
        self.create_dry_run_checkbox = self.templates_panel.create_dry_run_checkbox

        form_layout.addWidget(marketplace_group)

        self.validation_label = QtWidgets.QLabel("")
        self.validation_label.setObjectName("validationError")
        self.validation_label.setWordWrap(True)
        self.validation_label.setVisible(False)
        apply_accessible(self.validation_label, name="Pattern validation message")
        form_layout.addWidget(self.validation_label)

        progress_row = QtWidgets.QHBoxLayout()
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label = QtWidgets.QLabel("Idle")
        apply_accessible(self.progress_label, name="Pattern progress status")
        progress_row.addWidget(self.progress_bar, stretch=1)
        progress_row.addWidget(self.progress_label)
        form_layout.addLayout(progress_row)

        self.action_strip = ActionStrip()
        self.action_strip.setProperty("sticky", True)
        self.scan_btn = self.action_strip.add_button(
            "Run Pattern Scan",
            self._on_run_scan,
            primary=True,
        )
        self.cancel_btn = self.action_strip.add_button("Cancel", self._on_cancel)
        self.cancel_btn.setEnabled(False)
        apply_accessible(self.scan_btn, name="Run pattern scan")
        apply_accessible(self.cancel_btn, name="Cancel pattern operation")
        self.action_strip.add_stretch(1)
        form_layout.addWidget(self.action_strip)

        results_header = SectionHeader(
            "Scan Results",
            "Summary and detailed matches for the latest scan.",
        )
        results_layout.addWidget(results_header)

        self.summary_label = QtWidgets.QLabel("No scan results yet.")
        self.summary_label.setObjectName("subtitle")
        apply_accessible(self.summary_label, name="Pattern scan summary")
        results_layout.addWidget(self.summary_label)

        self.results = ResultsViewer()
        results_layout.addWidget(self.results, stretch=1)

        self.setTabOrder(self.category_combo, self.severity_filter)
        self.setTabOrder(self.severity_filter, self.show_disabled)
        self.setTabOrder(self.show_disabled, self.load_btn)
        self.setTabOrder(self.load_btn, self.pattern_table)
        self.setTabOrder(self.pattern_table, self.path_input)
        self.setTabOrder(self.path_input, self.browse_btn)
        self.setTabOrder(self.browse_btn, self.session_combo)
        self.setTabOrder(self.session_combo, self.glob_input)
        self.setTabOrder(self.glob_input, self.max_files_spin)
        self.setTabOrder(self.max_files_spin, self.marketplace_query_input)
        self.setTabOrder(self.marketplace_query_input, self.marketplace_tag_input)
        self.setTabOrder(self.marketplace_tag_input, self.search_marketplace_btn)
        self.setTabOrder(self.search_marketplace_btn, self.apply_pattern_input)
        self.setTabOrder(self.apply_pattern_input, self.apply_pattern_btn)
        self.setTabOrder(self.apply_pattern_btn, self.template_combo)
        self.setTabOrder(self.template_combo, self.template_values_input)
        self.setTabOrder(self.template_values_input, self.create_pattern_btn)
        self.setTabOrder(self.create_pattern_btn, self.create_pattern_id_input)
        self.setTabOrder(self.create_pattern_id_input, self.create_bundle_output_input)
        self.setTabOrder(self.create_bundle_output_input, self.create_dry_run_checkbox)
        self.setTabOrder(self.create_dry_run_checkbox, self.share_pattern_input)
        self.setTabOrder(self.share_pattern_input, self.share_bundle_output_input)
        self.setTabOrder(self.share_bundle_output_input, self.share_pattern_btn)
        self.setTabOrder(self.share_pattern_btn, self.scan_btn)
        self.setTabOrder(self.scan_btn, self.cancel_btn)

    def set_layout_splitter_ratio(self, ratio: float) -> None:
        self.page_scaffold.set_splitter_ratio(ratio)

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

    def _on_search_marketplace(self) -> None:
        if self._bridge is None:
            ErrorDialog.show_error(self, "Unavailable", "Command bridge is not initialized.")
            return

        query_value = self.marketplace_query_input.text().strip()
        tag_text = self.marketplace_tag_input.text().strip()
        tags = [
            item.strip()
            for item in tag_text.replace(";", ",").split(",")
            if item.strip()
        ]
        severity_value = self.severity_filter.currentText().strip().lower()
        try:
            self._bridge.pattern_search(
                query=query_value,
                tags=tags or None,
                severity=None if severity_value == "all" else severity_value,
                limit=50,
            )
        except RuntimeError as exc:
            ErrorDialog.show_error(
                self,
                "Marketplace Search Already Running",
                str(exc),
            )

    def _on_apply_pattern(self) -> None:
        if self._bridge is None:
            ErrorDialog.show_error(self, "Unavailable", "Command bridge is not initialized.")
            return

        pattern_ref = self.apply_pattern_input.text().strip()
        if not pattern_ref:
            self._set_validation("Provide a pattern ID or bundle path.", self.apply_pattern_input)
            return

        path_value = self.path_input.text().strip()
        if not path_value:
            self._set_validation("Select a path to scan.", self.path_input)
            return
        if not Path(path_value).exists():
            self._set_validation(f"Path does not exist: {path_value}", self.path_input)
            return
        self._clear_validation()

        session_id = self.session_combo.currentText().strip() or self._current_session_id
        try:
            self._bridge.pattern_apply(
                pattern_ref=pattern_ref,
                path=path_value,
                glob=self.glob_input.text().strip() or "*",
                max_files=int(self.max_files_spin.value()),
                session_id=session_id,
            )
        except RuntimeError as exc:
            ErrorDialog.show_error(
                self,
                "Pattern Apply Already Running",
                str(exc),
            )

    def _on_create_pattern(self) -> None:
        if self._bridge is None:
            ErrorDialog.show_error(self, "Unavailable", "Command bridge is not initialized.")
            return

        template_id = self.template_combo.currentText().strip()
        if not template_id:
            self._set_validation("Select a template to create a pattern.", self.template_combo)
            return

        values_text = self.template_values_input.text().strip()
        values: dict[str, str] = {}
        if values_text:
            for token in values_text.split(","):
                pair = token.strip()
                if not pair:
                    continue
                if "=" not in pair:
                    self._set_validation(
                        f"Invalid template value '{pair}'. Use key=value pairs.",
                        self.template_values_input,
                    )
                    return
                key, value = pair.split("=", 1)
                normalized_key = key.strip()
                if not normalized_key:
                    self._set_validation(
                        f"Invalid template value '{pair}'. Key cannot be empty.",
                        self.template_values_input,
                    )
                    return
                values[normalized_key] = value.strip()
        self._clear_validation()

        output_path = self.create_bundle_output_input.text().strip() or None
        session_id = self.session_combo.currentText().strip() or self._current_session_id
        try:
            self._bridge.pattern_create(
                template_id=template_id,
                values=values,
                pattern_id=self.create_pattern_id_input.text().strip() or None,
                dry_run=self.create_dry_run_checkbox.isChecked(),
                output_path=output_path,
                session_id=session_id,
            )
        except RuntimeError as exc:
            ErrorDialog.show_error(
                self,
                "Pattern Create Already Running",
                str(exc),
            )

    def _on_share_pattern(self) -> None:
        if self._bridge is None:
            ErrorDialog.show_error(self, "Unavailable", "Command bridge is not initialized.")
            return

        pattern_id = self.share_pattern_input.text().strip()
        if not pattern_id:
            self._set_validation("Provide a pattern ID to share.", self.share_pattern_input)
            return
        self._clear_validation()

        session_id = self.session_combo.currentText().strip() or self._current_session_id
        bundle_out = self.share_bundle_output_input.text().strip() or None
        try:
            self._bridge.pattern_share(
                pattern_id=pattern_id,
                bundle_out=bundle_out,
                include_examples=False,
                session_id=session_id,
            )
        except RuntimeError as exc:
            ErrorDialog.show_error(
                self,
                "Pattern Share Already Running",
                str(exc),
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

    @staticmethod
    def _pattern_operations() -> set[str]:
        return {
            "pattern_list",
            "pattern_scan",
            "pattern_search",
            "pattern_apply",
            "pattern_create",
            "pattern_share",
        }

    def _set_action_buttons_enabled(self, enabled: bool) -> None:
        self.scan_btn.setEnabled(enabled)
        self.load_btn.setEnabled(enabled)
        self.search_marketplace_btn.setEnabled(enabled)
        self.apply_pattern_btn.setEnabled(enabled)
        self.create_pattern_btn.setEnabled(enabled)
        self.share_pattern_btn.setEnabled(enabled)

    def _on_cancel(self) -> None:
        if self._bridge is not None:
            for operation in self._pattern_operations():
                self._bridge.cancel_operation(operation)

    def _on_operation_started(self, operation: str) -> None:
        if operation not in self._pattern_operations():
            return
        self.cancel_btn.setEnabled(True)
        self._set_action_buttons_enabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"{operation} started")

    def _on_operation_progress(
        self,
        operation: str,
        current: int,
        total: int,
        message: str,
    ) -> None:
        if operation not in self._pattern_operations():
            return
        value = int((current / max(total, 1)) * 100)
        self.progress_bar.setValue(max(0, min(100, value)))
        self.progress_label.setText(message or f"{operation}: {current}/{total}")

    def _on_operation_finished(self, operation: str, payload: object) -> None:
        if operation not in self._pattern_operations():
            return
        self._set_action_buttons_enabled(True)
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
            self.results.set_metadata("Latest operation: Pattern List")
            return

        if operation in {"pattern_scan", "pattern_apply"}:
            self.progress_label.setText(
                "Pattern apply completed" if operation == "pattern_apply" else "Pattern scan completed"
            )
            self._last_scan_result = data
            summary = {
                "pattern_id": data.get("pattern_id"),
                "installed": data.get("installed"),
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
                        "pattern_id": summary["pattern_id"],
                        "installed": summary["installed"],
                        "patterns_scanned": summary["patterns_scanned"],
                        "files_scanned": summary["files_scanned"],
                        "matches_found": summary["matches_found"],
                    },
                    indent=2,
                    default=str,
                ),
                json.dumps(summary, indent=2, default=str),
            )
            self.results.set_metadata(
                "Latest operation: Pattern Apply" if operation == "pattern_apply" else "Latest operation: Pattern Scan"
            )
            return

        if operation == "pattern_search":
            self.progress_label.setText("Marketplace search completed")
            patterns = data.get("patterns", [])
            self.summary_label.setText(f"Marketplace results: {len(patterns)}")
            self.results.set_sections(
                json.dumps(
                    {"total_count": data.get("total_count"), "query": self.marketplace_query_input.text().strip()},
                    indent=2,
                    default=str,
                ),
                json.dumps({"patterns": patterns[:100]}, indent=2, default=str),
            )
            self.results.set_metadata("Latest operation: Pattern Marketplace Search")
            return

        if operation == "pattern_create":
            self.progress_label.setText("Pattern creation completed")
            self.summary_label.setText(
                f"Template create: {str(data.get('pattern_id') or 'unknown')}"
            )
            self.results.set_sections(
                json.dumps(
                    {
                        "template_id": data.get("template_id"),
                        "pattern_id": data.get("pattern_id"),
                        "created": data.get("created"),
                        "installed": data.get("installed"),
                        "dry_run": data.get("dry_run"),
                    },
                    indent=2,
                    default=str,
                ),
                json.dumps(data, indent=2, default=str),
            )
            self.results.set_metadata("Latest operation: Pattern Template Create")
            return

        if operation == "pattern_share":
            self.progress_label.setText("Pattern share bundle completed")
            self.summary_label.setText(
                f"Shared pattern: {str(data.get('pattern_id') or 'unknown')}"
            )
            self.results.set_sections(
                json.dumps(
                    {
                        "pattern_id": data.get("pattern_id"),
                        "package_id": data.get("package_id"),
                        "path": data.get("path"),
                        "version": data.get("version"),
                    },
                    indent=2,
                    default=str,
                ),
                json.dumps(data, indent=2, default=str),
            )
            self.results.set_metadata("Latest operation: Pattern Share")

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
        if operation not in self._pattern_operations():
            return
        self._set_action_buttons_enabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText(f"Failed: {error_type} - {message}")

    def _on_operation_cancelled(self, operation: str) -> None:
        if operation not in self._pattern_operations():
            return
        self._set_action_buttons_enabled(True)
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
        self._set_action_buttons_enabled(not is_busy)

    def trigger_primary_action(self) -> None:
        if self.scan_btn.isEnabled():
            self._on_run_scan()

    def set_hints_enabled(self, enabled: bool) -> None:
        self._hints_enabled = bool(enabled)
        self.hint_panel.setVisible(self._hints_enabled)

    def _set_validation(self, message: str, widget: QtWidgets.QWidget | None = None) -> None:
        mark_invalid(widget, self.validation_label, message)

    def _clear_validation(self, *_args: object) -> None:
        clear_invalid(
            (
                self.path_input,
                self.apply_pattern_input,
                self.template_combo,
                self.template_values_input,
                self.create_pattern_id_input,
                self.create_bundle_output_input,
                self.share_pattern_input,
                self.share_bundle_output_input,
            ),
            self.validation_label,
        )
