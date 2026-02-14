"""Desktop GUI application entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from .core import GUICommandBridge, RuntimeFacade, SessionManager, ViewStateBinder
from .theme import build_stylesheet
from .views import ExportView, HomeView, InvestigateView, ObserveView, PatternsView
from .widgets import ErrorDialog


class MainWindow(QtWidgets.QMainWindow):
    """Primary application window hosting desktop investigation views."""

    AUTOSAVE_INTERVAL_MS = 30_000

    def __init__(self, start_path: Path | None = None) -> None:
        super().__init__()
        self._start_path = (start_path or Path(".")).resolve()
        self.setWindowTitle("CodeMarshal")
        self.resize(1220, 820)

        self._session_manager = SessionManager()
        self._runtime_facade = RuntimeFacade()
        self._view_state = ViewStateBinder()
        if GUICommandBridge is None:
            raise RuntimeError("GUICommandBridge unavailable. Ensure PySide6 is installed.")
        self._bridge = GUICommandBridge(facade=self._runtime_facade)

        self._stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self._stack)
        self.statusBar().showMessage("Ready")

        self._views = {
            "home": HomeView(),
            "observe": ObserveView(command_bridge=self._bridge),
            "investigate": InvestigateView(command_bridge=self._bridge),
            "patterns": PatternsView(command_bridge=self._bridge),
            "export": ExportView(command_bridge=self._bridge),
        }
        for view in self._views.values():
            self._stack.addWidget(view)
            self._view_state.register(view)

        self._wire_navigation()
        self._wire_bridge_signals()
        self._register_shortcuts()

        self._set_current_path(self._start_path)
        self._sync_recent_sessions()
        self._apply_settings()
        self._restore_window_state()
        self._restore_recovery_state()

        self._autosave_timer = QtCore.QTimer(self)
        self._autosave_timer.setInterval(self.AUTOSAVE_INTERVAL_MS)
        self._autosave_timer.timeout.connect(self._autosave_recovery_state)
        self._autosave_timer.start()

        last_view = self._session_manager.get_last_view()
        self._navigate(last_view if last_view in self._views else "home")

    def _wire_navigation(self) -> None:
        home = self._views["home"]
        home.navigate_requested.connect(self._navigate)
        home.path_selected.connect(self._set_current_path)
        home.refresh_requested.connect(self._sync_recent_sessions)
        home.open_investigation_requested.connect(self._open_session)
        home.resume_last_requested.connect(self._resume_last_session)
        home.quick_action_requested.connect(self._handle_quick_action)

        for name in ("observe", "investigate", "patterns", "export"):
            view = self._views[name]
            view.navigate_requested.connect(self._navigate)
            if hasattr(view, "preset_changed"):
                view.preset_changed.connect(
                    lambda preset: self._session_manager.update_settings(
                        {"observe_preset": preset}
                    )
                )

    def _wire_bridge_signals(self) -> None:
        self._bridge.operation_started.connect(self._on_operation_started)
        self._bridge.operation_progress.connect(self._on_operation_progress)
        self._bridge.operation_finished.connect(self._on_operation_finished)
        self._bridge.operation_error.connect(self._on_operation_error)
        self._bridge.operation_cancelled.connect(self._on_operation_cancelled)
        self._bridge.busy_changed.connect(self._on_busy_changed)

    def _register_shortcuts(self) -> None:
        shortcuts = [
            ("Ctrl+1", lambda: self._navigate("home")),
            ("Ctrl+2", lambda: self._navigate("observe")),
            ("Ctrl+3", lambda: self._navigate("investigate")),
            ("Ctrl+4", lambda: self._navigate("patterns")),
            ("Ctrl+5", lambda: self._navigate("export")),
            ("Ctrl+Return", self._trigger_primary_action),
            ("Esc", self._bridge.cancel_all),
        ]
        for key, handler in shortcuts:
            shortcut = QtGui.QShortcut(QtGui.QKeySequence(key), self)
            shortcut.activated.connect(handler)

    def _navigate(self, name: str) -> None:
        if name not in self._views:
            return
        self._stack.setCurrentWidget(self._views[name])
        self._session_manager.set_last_view(name)

    def _set_current_path(self, path: str | Path) -> None:
        resolved = Path(path).resolve()
        self._session_manager.set_last_path(str(resolved))
        self._view_state.set_path(str(resolved))
        self._views["home"].set_recent_paths(self._session_manager.get_recent_paths(limit=10))

    def _set_current_session(self, session_id: str | None) -> None:
        self._view_state.set_session(session_id)

    def _sync_recent_sessions(self) -> None:
        sessions = self._bridge.list_recent_investigations(limit=10)
        self._session_manager.merge_recent_investigations(sessions)
        merged = self._session_manager.get_recent_investigations(limit=10)
        self._view_state.set_sessions(merged)
        self._views["home"].set_recent_investigations(merged)

        recent_paths = self._runtime_facade.list_recent_paths(limit=10)
        for value in recent_paths:
            self._session_manager.add_recent_path(value)
        self._views["home"].set_recent_paths(self._session_manager.get_recent_paths(limit=10))

    def _apply_settings(self) -> None:
        settings = self._session_manager.get_settings()
        self._views["export"].set_default_export_format(
            str(settings.get("default_export_format") or "json")
        )
        preset = str(settings.get("observe_preset") or "")
        if preset:
            self._views["observe"].set_preset(preset)

    def _restore_window_state(self) -> None:
        geometry_hex = self._session_manager.get_window_geometry()
        if geometry_hex:
            self.restoreGeometry(QtCore.QByteArray.fromHex(geometry_hex.encode("ascii")))
        state_hex = self._session_manager.get_window_state()
        if state_hex:
            self.restoreState(QtCore.QByteArray.fromHex(state_hex.encode("ascii")))

    def _restore_recovery_state(self) -> None:
        recovery = self._session_manager.get_recovery_state()
        if not recovery:
            return
        session_id = str(recovery.get("session_id") or "")
        if not session_id:
            return

        question = (
            "A previous session may have been interrupted.\n\n"
            f"Session ID: {session_id}\n\n"
            "Do you want to restore this session now?"
        )
        answer = QtWidgets.QMessageBox.question(
            self,
            "Recover Previous Session",
            question,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.Yes,
        )
        if answer == QtWidgets.QMessageBox.Yes:
            if recovery.get("path"):
                self._set_current_path(str(recovery["path"]))
            self._open_session(session_id)
        else:
            self._session_manager.clear_recovery_state()

    def _open_session(self, session_id: str) -> None:
        metadata = self._bridge.load_session_metadata(session_id)
        if not metadata:
            ErrorDialog.show_error(
                self,
                "Session Not Found",
                f"Could not load session '{session_id}'.",
                suggestion="Refresh recent sessions and try again.",
            )
            return

        self._set_current_session(session_id)
        self._views["investigate"].set_session_metadata(metadata)
        if metadata.get("path"):
            self._set_current_path(str(metadata["path"]))
        self._navigate("investigate")

    def _resume_last_session(self) -> None:
        recent = self._session_manager.get_recent_investigations(limit=1)
        if not recent:
            self.statusBar().showMessage("No recent sessions to resume", 3000)
            return
        session_id = str(recent[0].get("session_id") or "")
        if session_id:
            self._open_session(session_id)

    def _handle_quick_action(self, action: str) -> None:
        if action == "quick_observe":
            self._navigate("observe")
            self._views["observe"].trigger_primary_action()
            return
        if action == "quick_investigate":
            self._navigate("investigate")
            self._views["investigate"].trigger_primary_action()
            return
        if action == "quick_patterns":
            self._navigate("patterns")
            self._views["patterns"].trigger_primary_action()
            return

    def _trigger_primary_action(self) -> None:
        current = self._stack.currentWidget()
        if current is None:
            return
        if hasattr(current, "trigger_primary_action"):
            current.trigger_primary_action()

    def _autosave_recovery_state(self) -> None:
        session_id = self._runtime_facade.current_investigation_id
        current_path = self._runtime_facade.current_path
        if session_id and current_path:
            self._session_manager.save_recovery_state(session_id, str(current_path))

    def _on_operation_started(self, operation: str) -> None:
        self.statusBar().showMessage(f"{operation} started")
        self._session_manager.mark_dirty(True, self._runtime_facade.current_investigation_id)

    def _on_operation_progress(
        self,
        operation: str,
        current: int,
        total: int,
        message: str,
    ) -> None:
        text = message or f"{current}/{total}"
        self.statusBar().showMessage(f"{operation}: {text}")

    def _on_operation_finished(self, operation: str, payload: object) -> None:
        self.statusBar().showMessage(f"{operation} completed", 5000)
        data = payload if isinstance(payload, dict) else {"result": payload}

        session_id = str(
            data.get("session_id")
            or data.get("investigation_id")
            or self._runtime_facade.current_investigation_id
            or ""
        )
        if session_id:
            self._set_current_session(session_id)
            metadata = self._bridge.load_session_metadata(session_id)
            if metadata:
                self._session_manager.add_recent_investigation(metadata)
                if metadata.get("path"):
                    self._session_manager.add_recent_path(str(metadata["path"]))

        if operation == "export" and isinstance(data, dict):
            self._session_manager.set_default_export_format(
                str(data.get("format") or self._views["export"].format_combo.currentText())
            )

        self._sync_recent_sessions()
        self._session_manager.mark_dirty(False, session_id or None)

    def _on_operation_error(
        self,
        operation: str,
        error_type: str,
        message: str,
        details: str,
    ) -> None:
        self.statusBar().showMessage(f"{operation} failed: {message}", 8000)
        ErrorDialog.show_error(
            self,
            f"{operation} failed",
            f"{error_type}: {message}",
            context=f"Operation: {operation}",
            suggestion="Review the details, fix input values, and retry.",
            details=details,
        )
        self._session_manager.mark_dirty(True, self._runtime_facade.current_investigation_id)

    def _on_operation_cancelled(self, operation: str) -> None:
        self.statusBar().showMessage(f"{operation} cancelled", 5000)
        self._session_manager.mark_dirty(False, self._runtime_facade.current_investigation_id)

    def _on_busy_changed(self, is_busy: bool) -> None:
        self._view_state.set_busy(is_busy)
        if is_busy:
            self.statusBar().showMessage("Operation running...")
        else:
            self.statusBar().showMessage("Ready", 2000)

    def closeEvent(self, event: QtCore.QEvent) -> None:  # noqa: N802
        self._autosave_timer.stop()
        self._bridge.cancel_all()
        self._session_manager.set_window_geometry(
            bytes(self.saveGeometry().toHex()).decode("ascii")
        )
        self._session_manager.set_window_state(
            bytes(self.saveState().toHex()).decode("ascii")
        )
        self._session_manager.clear_recovery_state()
        super().closeEvent(event)


def main(argv: list[str] | None = None, start_path: Path | None = None) -> int:
    """Launch the desktop GUI."""
    argv = argv if argv is not None else sys.argv
    app = QtWidgets.QApplication(argv)
    app.setStyleSheet(build_stylesheet())

    window = MainWindow(start_path=start_path)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
