"""Desktop GUI application entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from .core import GUICommandBridge, RuntimeFacade, SessionManager
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

        self._wire_navigation()
        self._wire_bridge_signals()

        self._set_current_path(self._start_path)
        self._sync_recent_sessions()
        self._apply_settings()
        self._restore_recovery_state()

        self._autosave_timer = QtCore.QTimer(self)
        self._autosave_timer.setInterval(self.AUTOSAVE_INTERVAL_MS)
        self._autosave_timer.timeout.connect(self._autosave_recovery_state)
        self._autosave_timer.start()

        self._navigate("home")

    def _wire_navigation(self) -> None:
        home = self._views["home"]
        home.navigate_requested.connect(self._navigate)
        home.path_selected.connect(self._set_current_path)
        home.refresh_requested.connect(self._sync_recent_sessions)
        home.open_investigation_requested.connect(self._open_session)

        for name in ("observe", "investigate", "patterns", "export"):
            view = self._views[name]
            view.navigate_requested.connect(self._navigate)

    def _wire_bridge_signals(self) -> None:
        self._bridge.operation_started.connect(self._on_operation_started)
        self._bridge.operation_progress.connect(self._on_operation_progress)
        self._bridge.operation_finished.connect(self._on_operation_finished)
        self._bridge.operation_error.connect(self._on_operation_error)
        self._bridge.operation_cancelled.connect(self._on_operation_cancelled)

    def _navigate(self, name: str) -> None:
        if name not in self._views:
            return
        self._stack.setCurrentWidget(self._views[name])

    def _set_current_path(self, path: str | Path) -> None:
        resolved = Path(path).resolve()
        self._session_manager.set_last_path(str(resolved))
        self._views["home"].set_current_path(str(resolved))
        self._views["observe"].set_current_path(str(resolved))
        self._views["investigate"].set_current_path(str(resolved))
        self._views["patterns"].set_current_path(str(resolved))

    def _set_current_session(self, session_id: str | None) -> None:
        self._views["observe"].set_current_session(session_id)
        self._views["investigate"].set_current_session(session_id)
        self._views["patterns"].set_current_session(session_id)
        self._views["export"].set_current_session(session_id)

    def _sync_recent_sessions(self) -> None:
        sessions = self._bridge.list_recent_investigations(limit=10)
        self._session_manager.merge_recent_investigations(sessions)
        merged = self._session_manager.get_recent_investigations(limit=10)
        self._views["home"].set_recent_investigations(merged)
        self._views["observe"].set_known_sessions(merged)
        self._views["investigate"].set_known_sessions(merged)
        self._views["patterns"].set_known_sessions(merged)
        self._views["export"].set_known_sessions(merged)

    def _apply_settings(self) -> None:
        self._views["export"].set_default_export_format(
            self._session_manager.get_default_export_format()
        )

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

    def closeEvent(self, event: QtCore.QEvent) -> None:  # noqa: N802
        self._autosave_timer.stop()
        self._bridge.cancel_all()
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

