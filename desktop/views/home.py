"""Home view for the desktop GUI."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtWidgets

from desktop.widgets import HintPanel, PageScaffold, SectionHeader, apply_accessible


class HomeView(QtWidgets.QWidget):
    """Landing page with project selection and recent investigations."""

    navigate_requested = QtCore.Signal(str)
    path_selected = QtCore.Signal(str)
    open_investigation_requested = QtCore.Signal(str)
    refresh_requested = QtCore.Signal()
    resume_last_requested = QtCore.Signal()
    quick_action_requested = QtCore.Signal(str)
    layout_splitter_ratio_changed = QtCore.Signal(float)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._action_controls: list[QtWidgets.QWidget] = []
        self._hints_enabled = True
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.page_scaffold = PageScaffold(default_ratio=0.46, narrow_breakpoint=1280)
        self.page_scaffold.splitter_ratio_changed.connect(
            self.layout_splitter_ratio_changed.emit
        )
        layout.addWidget(self.page_scaffold)

        header = SectionHeader(
            "CodeMarshal",
            "Desktop Investigation Workspace",
        )
        self.page_scaffold.set_header_widget(header)

        form_layout = self.page_scaffold.form_layout
        results_layout = self.page_scaffold.results_layout

        self.start_hint = HintPanel(
            "Start Here",
            (
                "1) Choose a project path.\n"
                "2) Run Investigate to create a session.\n"
                "3) Ask questions, scan patterns, and export results."
            ),
        )
        self.start_hint.setVisible(True)
        form_layout.addWidget(self.start_hint)

        path_group = QtWidgets.QGroupBox("Project")
        path_layout = QtWidgets.QHBoxLayout(path_group)
        self.path_input = QtWidgets.QLineEdit()
        self.path_input.setPlaceholderText("Select a file or directory")
        apply_accessible(
            self.path_input,
            name="Project path input",
            description="Path to the file or directory to analyze.",
        )
        self.browse_btn = QtWidgets.QPushButton("Browse")
        self.browse_btn.clicked.connect(self._on_browse)
        self.use_btn = QtWidgets.QPushButton("Use Path")
        self.use_btn.clicked.connect(self._emit_path)
        apply_accessible(self.browse_btn, name="Browse project path")
        apply_accessible(self.use_btn, name="Use project path")
        self._action_controls.extend([self.browse_btn, self.use_btn])
        path_layout.addWidget(self.path_input, stretch=1)
        path_layout.addWidget(self.browse_btn)
        path_layout.addWidget(self.use_btn)
        form_layout.addWidget(path_group)

        workflow_group = QtWidgets.QGroupBox("Workflows")
        workflow_layout = QtWidgets.QGridLayout(workflow_group)
        workflow_layout.setHorizontalSpacing(8)
        workflow_layout.setVerticalSpacing(8)
        self.nav_buttons: dict[str, QtWidgets.QPushButton] = {}
        for index, (label, target) in enumerate(
            [
                ("Observe", "observe"),
                ("Investigate", "investigate"),
                ("Knowledge", "knowledge"),
                ("Patterns", "patterns"),
                ("Export", "export"),
            ]
        ):
            btn = QtWidgets.QPushButton(label)
            if target == "investigate":
                btn.setProperty("variant", "primary")
            btn.clicked.connect(lambda _checked=False, name=target: self.navigate_requested.emit(name))
            apply_accessible(btn, name=f"Open {label} view")
            self._action_controls.append(btn)
            workflow_layout.addWidget(btn, index // 2, index % 2)
            self.nav_buttons[target] = btn
        form_layout.addWidget(workflow_group)

        quick_group = QtWidgets.QGroupBox("Quick Start")
        quick_layout = QtWidgets.QGridLayout(quick_group)
        quick_layout.setHorizontalSpacing(8)
        quick_layout.setVerticalSpacing(8)
        quick_defs = [
            ("Observe Current Path", "quick_observe"),
            ("Investigate Current Path", "quick_investigate"),
            ("Pattern Scan Current Path", "quick_patterns"),
        ]
        self.quick_buttons: dict[str, QtWidgets.QPushButton] = {}
        for index, (label, action) in enumerate(quick_defs):
            button = QtWidgets.QPushButton(label)
            button.setToolTip(f"Open {label.lower()} and run immediately.")
            button.clicked.connect(
                lambda _checked=False, value=action: self.quick_action_requested.emit(value)
            )
            apply_accessible(
                button,
                name=label,
                description="Open workflow and execute primary action immediately.",
            )
            self._action_controls.append(button)
            quick_layout.addWidget(button, index, 0)
            self.quick_buttons[action] = button
        form_layout.addWidget(quick_group)
        form_layout.addStretch(1)

        paths_group = QtWidgets.QGroupBox("Recent Paths")
        paths_layout = QtWidgets.QVBoxLayout(paths_group)
        self.recent_paths = QtWidgets.QListWidget()
        self.recent_paths.itemDoubleClicked.connect(self._open_selected_path)
        self.recent_paths.itemActivated.connect(self._open_selected_path)
        apply_accessible(
            self.recent_paths,
            name="Recent paths list",
            description="Previously used project paths. Press Enter to use selected path.",
        )
        paths_layout.addWidget(self.recent_paths)
        self.paths_empty = QtWidgets.QLabel("No recent paths yet. Use Browse to pick your first project.")
        self.paths_empty.setObjectName("subtitle")
        self.paths_empty.setWordWrap(True)
        paths_layout.addWidget(self.paths_empty)
        path_buttons = QtWidgets.QHBoxLayout()
        self.open_path_btn = QtWidgets.QPushButton("Use Selected Path")
        self.open_path_btn.clicked.connect(self._open_selected_path)
        apply_accessible(self.open_path_btn, name="Use selected recent path")
        self._action_controls.append(self.open_path_btn)
        path_buttons.addWidget(self.open_path_btn)
        path_buttons.addStretch(1)
        paths_layout.addLayout(path_buttons)
        results_layout.addWidget(paths_group)

        recent_group = QtWidgets.QGroupBox("Recent Investigations")
        recent_layout = QtWidgets.QVBoxLayout(recent_group)
        self.recent_table = QtWidgets.QTreeWidget()
        self.recent_table.setHeaderLabels(["Name", "Session", "Path", "Updated"])
        self.recent_table.setRootIsDecorated(False)
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.itemDoubleClicked.connect(self._open_selected_session)
        self.recent_table.itemActivated.connect(self._open_selected_session)
        apply_accessible(
            self.recent_table,
            name="Recent investigations table",
            description="Recent investigation sessions. Press Enter to open selected session.",
        )
        recent_layout.addWidget(self.recent_table)
        self.recent_empty = QtWidgets.QLabel(
            "No recent sessions yet. Start an investigation to populate this list."
        )
        self.recent_empty.setObjectName("subtitle")
        self.recent_empty.setWordWrap(True)
        recent_layout.addWidget(self.recent_empty)

        controls = QtWidgets.QHBoxLayout()
        self.open_btn = QtWidgets.QPushButton("Open Selected")
        self.open_btn.clicked.connect(self._open_selected_session)
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.resume_btn = QtWidgets.QPushButton("Resume Last Session")
        self.resume_btn.clicked.connect(self.resume_last_requested.emit)
        apply_accessible(self.open_btn, name="Open selected investigation")
        apply_accessible(self.resume_btn, name="Resume last investigation session")
        apply_accessible(self.refresh_btn, name="Refresh recent investigations")
        self._action_controls.extend([self.open_btn, self.refresh_btn, self.resume_btn])
        controls.addWidget(self.open_btn)
        controls.addWidget(self.resume_btn)
        controls.addWidget(self.refresh_btn)
        controls.addStretch(1)
        recent_layout.addLayout(controls)
        results_layout.addWidget(recent_group, stretch=1)

        # Keyboard-first flow.
        self.setTabOrder(self.path_input, self.browse_btn)
        self.setTabOrder(self.browse_btn, self.use_btn)
        self.setTabOrder(self.use_btn, self.nav_buttons["investigate"])
        self.setTabOrder(self.nav_buttons["investigate"], self.quick_buttons["quick_investigate"])
        self.setTabOrder(self.quick_buttons["quick_investigate"], self.recent_paths)
        self.setTabOrder(self.recent_paths, self.open_path_btn)
        self.setTabOrder(self.open_path_btn, self.recent_table)
        self.setTabOrder(self.recent_table, self.open_btn)
        self.setTabOrder(self.open_btn, self.resume_btn)
        self.setTabOrder(self.resume_btn, self.refresh_btn)

    def set_layout_splitter_ratio(self, ratio: float) -> None:
        self.page_scaffold.set_splitter_ratio(ratio)

    def _on_browse(self) -> None:
        start = self.path_input.text().strip() or str(Path(".").resolve())
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose Project", start)
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
            self.path_selected.emit(path)

    def _emit_path(self) -> None:
        path = self.path_input.text().strip()
        if path:
            self.path_selected.emit(path)

    def _open_selected_path(self, *_args: object) -> None:
        item = self.recent_paths.currentItem()
        if item is None:
            return
        path = item.text().strip()
        if path:
            self.path_input.setText(path)
            self.path_selected.emit(path)

    def _open_selected_session(self, *_args: object) -> None:
        session_id = self.selected_session_id()
        if session_id:
            self.open_investigation_requested.emit(session_id)

    def selected_session_id(self) -> str | None:
        item = self.recent_table.currentItem()
        if item is None:
            return None
        value = item.data(0, QtCore.Qt.UserRole)
        return str(value) if value else None

    def set_current_path(self, path: str | Path) -> None:
        self.path_input.setText(str(path))

    def set_recent_paths(self, paths: list[str]) -> None:
        self.recent_paths.clear()
        for value in paths:
            text = str(value)
            item = QtWidgets.QListWidgetItem(text)
            if not Path(text).exists():
                item.setForeground(QtCore.Qt.darkYellow)
            self.recent_paths.addItem(item)
        self.paths_empty.setVisible(len(paths) == 0)

    def set_recent_investigations(self, sessions: list[dict[str, Any]]) -> None:
        self.recent_table.clear()
        for session in sessions:
            session_id = str(session.get("session_id") or session.get("id") or "")
            if not session_id:
                continue
            name = str(session.get("name") or session_id)
            path = str(session.get("path") or "")
            updated = self._format_timestamp(
                session.get("modified_at")
                or session.get("saved_at")
                or session.get("created_at")
            )
            item = QtWidgets.QTreeWidgetItem([name, session_id, path, updated])
            item.setData(0, QtCore.Qt.UserRole, session_id)
            self.recent_table.addTopLevelItem(item)

        for idx, width in enumerate((180, 180, 460, 150)):
            self.recent_table.setColumnWidth(idx, width)
        self.recent_empty.setVisible(self.recent_table.topLevelItemCount() == 0)

    def _format_timestamp(self, value: Any) -> str:
        if not value:
            return "unknown"
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return str(value)

    def set_busy(self, is_busy: bool) -> None:
        for widget in self._action_controls:
            widget.setEnabled(not is_busy)

    def trigger_primary_action(self) -> None:
        self.quick_action_requested.emit("quick_investigate")

    def set_hints_enabled(self, enabled: bool) -> None:
        self._hints_enabled = bool(enabled)
        self.start_hint.setVisible(self._hints_enabled)
