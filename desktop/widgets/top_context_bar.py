"""Top shell context bar for route, path, and status metadata."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtWidgets

from .a11y import apply_accessible
from .metric_pill import MetricPill


class TopContextBar(QtWidgets.QFrame):
    """Displays current route context and high-level status."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("topContextBar")
        self._pulse_timer = QtCore.QTimer(self)
        self._pulse_timer.setSingleShot(True)
        self._pulse_timer.timeout.connect(self._clear_pulse)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        route_block = QtWidgets.QVBoxLayout()
        route_block.setSpacing(2)
        self.route_title = QtWidgets.QLabel("Home")
        self.route_title.setObjectName("contextRouteTitle")
        self.route_caption = QtWidgets.QLabel("Desktop workspace")
        self.route_caption.setObjectName("contextRouteCaption")
        route_block.addWidget(self.route_title)
        route_block.addWidget(self.route_caption)
        layout.addLayout(route_block, stretch=2)

        self.path_label = QtWidgets.QLabel("Path: not selected")
        self.path_label.setObjectName("contextPathLabel")
        self.path_label.setToolTip("Current project path")
        self.path_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        apply_accessible(self.path_label, name="Current project path")
        layout.addWidget(self.path_label, stretch=3)

        self.session_label = QtWidgets.QLabel("Session: none")
        self.session_label.setObjectName("contextSessionLabel")
        self.session_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        apply_accessible(self.session_label, name="Current session status")
        layout.addWidget(self.session_label, stretch=2)

        self.paths_metric = MetricPill("Paths", "0")
        self.sessions_metric = MetricPill("Sessions", "0")
        layout.addWidget(self.paths_metric)
        layout.addWidget(self.sessions_metric)

        self.operation_label = QtWidgets.QLabel("Idle")
        self.operation_label.setObjectName("contextOperationLabel")
        self.operation_label.setProperty("state", "idle")
        self.operation_label.setAlignment(QtCore.Qt.AlignCenter)
        apply_accessible(self.operation_label, name="Current operation breadcrumb")
        layout.addWidget(self.operation_label)

        self.busy_chip = QtWidgets.QLabel("Idle")
        self.busy_chip.setObjectName("contextBusyChip")
        self.busy_chip.setProperty("state", "idle")
        self.busy_chip.setAlignment(QtCore.Qt.AlignCenter)
        self.busy_chip.setMinimumWidth(88)
        apply_accessible(self.busy_chip, name="Application busy status")
        layout.addWidget(self.busy_chip)

    def set_route(self, title: str, caption: str = "") -> None:
        self.route_title.setText(str(title or "Home"))
        self.route_caption.setText(str(caption or "Desktop workspace"))

    def set_path(self, path: str | Path | None) -> None:
        text = str(path).strip() if path else ""
        if not text:
            self.path_label.setText("Path: not selected")
            self.path_label.setToolTip("Current project path")
            return
        resolved = str(Path(text).resolve())
        basename = Path(resolved).name or resolved
        self.path_label.setText(f"Path: {basename}")
        self.path_label.setToolTip(resolved)

    def set_session(self, session_id: str | None) -> None:
        self.session_label.setText(f"Session: {session_id or 'none'}")

    def set_busy(self, is_busy: bool) -> None:
        self.busy_chip.setText("Running" if is_busy else "Idle")
        self.busy_chip.setProperty("state", "busy" if is_busy else "idle")
        self.busy_chip.style().unpolish(self.busy_chip)
        self.busy_chip.style().polish(self.busy_chip)

    def set_metrics(self, recent_paths: int, recent_sessions: int) -> None:
        paths_value = max(int(recent_paths), 0)
        session_value = max(int(recent_sessions), 0)
        self.paths_metric.set_value(paths_value)
        self.sessions_metric.set_value(session_value)
        self.paths_metric.set_state("warn" if paths_value == 0 else "ok")
        self.sessions_metric.set_state("warn" if session_value == 0 else "ok")

    def set_operation(self, text: str, level: str = "idle", pulse: bool = False) -> None:
        normalized = str(level or "idle").strip().lower()
        if normalized not in {"idle", "running", "error"}:
            normalized = "idle"
        self.operation_label.setText(str(text or "Idle"))
        self.operation_label.setProperty("state", normalized)
        self.operation_label.style().unpolish(self.operation_label)
        self.operation_label.style().polish(self.operation_label)
        if pulse:
            self.busy_chip.setProperty("pulse", True)
            self.busy_chip.style().unpolish(self.busy_chip)
            self.busy_chip.style().polish(self.busy_chip)
            self._pulse_timer.start(320)

    def _clear_pulse(self) -> None:
        self.busy_chip.setProperty("pulse", False)
        self.busy_chip.style().unpolish(self.busy_chip)
        self.busy_chip.style().polish(self.busy_chip)
