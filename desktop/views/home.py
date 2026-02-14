"""Home view for the desktop GUI."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtWidgets


class HomeView(QtWidgets.QWidget):
    """Landing page with project selection and recent investigations."""

    navigate_requested = QtCore.Signal(str)
    path_selected = QtCore.Signal(str)
    open_investigation_requested = QtCore.Signal(str)
    refresh_requested = QtCore.Signal()
    resume_last_requested = QtCore.Signal()
    quick_action_requested = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._action_controls: list[QtWidgets.QWidget] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(14)

        title = QtWidgets.QLabel("CodeMarshal")
        title.setObjectName("title")
        subtitle = QtWidgets.QLabel("Desktop Investigation Workspace")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title, alignment=QtCore.Qt.AlignHCenter)
        layout.addWidget(subtitle, alignment=QtCore.Qt.AlignHCenter)

        path_group = QtWidgets.QGroupBox("Project")
        path_layout = QtWidgets.QHBoxLayout(path_group)
        self.path_input = QtWidgets.QLineEdit()
        self.path_input.setPlaceholderText("Select a file or directory")
        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.clicked.connect(self._on_browse)
        use_btn = QtWidgets.QPushButton("Use Path")
        use_btn.clicked.connect(self._emit_path)
        self._action_controls.extend([browse_btn, use_btn])
        path_layout.addWidget(self.path_input, stretch=1)
        path_layout.addWidget(browse_btn)
        path_layout.addWidget(use_btn)
        layout.addWidget(path_group)

        actions = QtWidgets.QHBoxLayout()
        for label, target in [
            ("Observe", "observe"),
            ("Investigate", "investigate"),
            ("Patterns", "patterns"),
            ("Export", "export"),
        ]:
            btn = QtWidgets.QPushButton(label)
            btn.clicked.connect(lambda _checked=False, name=target: self.navigate_requested.emit(name))
            self._action_controls.append(btn)
            actions.addWidget(btn)
        actions.addStretch(1)
        layout.addLayout(actions)

        quick_group = QtWidgets.QGroupBox("Quick Start")
        quick_layout = QtWidgets.QHBoxLayout(quick_group)
        quick_defs = [
            ("Observe Current Path", "quick_observe"),
            ("Investigate Current Path", "quick_investigate"),
            ("Pattern Scan Current Path", "quick_patterns"),
        ]
        for label, action in quick_defs:
            button = QtWidgets.QPushButton(label)
            button.clicked.connect(
                lambda _checked=False, value=action: self.quick_action_requested.emit(value)
            )
            self._action_controls.append(button)
            quick_layout.addWidget(button)
        quick_layout.addStretch(1)
        layout.addWidget(quick_group)

        paths_group = QtWidgets.QGroupBox("Recent Paths")
        paths_layout = QtWidgets.QVBoxLayout(paths_group)
        self.recent_paths = QtWidgets.QListWidget()
        self.recent_paths.itemDoubleClicked.connect(self._open_selected_path)
        paths_layout.addWidget(self.recent_paths)
        path_buttons = QtWidgets.QHBoxLayout()
        open_path_btn = QtWidgets.QPushButton("Use Selected Path")
        open_path_btn.clicked.connect(self._open_selected_path)
        self._action_controls.append(open_path_btn)
        path_buttons.addWidget(open_path_btn)
        path_buttons.addStretch(1)
        paths_layout.addLayout(path_buttons)
        layout.addWidget(paths_group)

        recent_group = QtWidgets.QGroupBox("Recent Investigations")
        recent_layout = QtWidgets.QVBoxLayout(recent_group)
        self.recent_table = QtWidgets.QTreeWidget()
        self.recent_table.setHeaderLabels(["Name", "Session", "Path", "Updated"])
        self.recent_table.setRootIsDecorated(False)
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.itemDoubleClicked.connect(self._open_selected_session)
        recent_layout.addWidget(self.recent_table)

        controls = QtWidgets.QHBoxLayout()
        open_btn = QtWidgets.QPushButton("Open Selected")
        open_btn.clicked.connect(self._open_selected_session)
        self._action_controls.append(open_btn)
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        self._action_controls.append(refresh_btn)
        resume_btn = QtWidgets.QPushButton("Resume Last Session")
        resume_btn.clicked.connect(self.resume_last_requested.emit)
        self._action_controls.append(resume_btn)
        controls.addWidget(open_btn)
        controls.addWidget(resume_btn)
        controls.addWidget(refresh_btn)
        controls.addStretch(1)
        recent_layout.addLayout(controls)
        layout.addWidget(recent_group, stretch=1)

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

    def _open_selected_path(self) -> None:
        item = self.recent_paths.currentItem()
        if item is None:
            return
        path = item.text().strip()
        if path:
            self.path_input.setText(path)
            self.path_selected.emit(path)

    def _open_selected_session(self) -> None:
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
