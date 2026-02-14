"""Qt bridge for running facade operations on worker threads."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from PySide6 import QtCore

from .runtime_facade import RuntimeFacade
from .worker import BridgeWorker


class GUICommandBridge(QtCore.QObject):
    """Dispatch desktop operations asynchronously with progress signals."""

    operation_started = QtCore.Signal(str)
    operation_progress = QtCore.Signal(str, int, int, str)
    operation_finished = QtCore.Signal(str, object)
    operation_error = QtCore.Signal(str, str, str, str)
    operation_cancelled = QtCore.Signal(str)
    busy_changed = QtCore.Signal(bool)

    def __init__(
        self,
        facade: RuntimeFacade | None = None,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._facade = facade or RuntimeFacade()
        self._thread_pool = QtCore.QThreadPool.globalInstance()
        self._active_workers: dict[str, BridgeWorker] = {}
        self._lock = threading.RLock()

    @property
    def facade(self) -> RuntimeFacade:
        return self._facade

    @property
    def is_busy(self) -> bool:
        with self._lock:
            return bool(self._active_workers)

    def cancel_operation(self, operation: str) -> bool:
        """Request cancellation for a running operation."""
        with self._lock:
            worker = self._active_workers.get(operation)
        if not worker:
            return False
        worker.cancel()
        return True

    def cancel_all(self) -> None:
        """Request cancellation for all active operations."""
        with self._lock:
            workers = list(self._active_workers.values())
        for worker in workers:
            worker.cancel()

    def resolve_session_id(self, session_id: str | None = None) -> str | None:
        return self._facade.resolve_session_id(session_id)

    def list_recent_investigations(self, limit: int = 10) -> list[dict[str, Any]]:
        return self._facade.list_recent_investigations(limit=limit)

    def load_session_metadata(self, session_id: str) -> dict[str, Any] | None:
        return self._facade.load_session_metadata(session_id)

    def _start_worker(self, operation: str, fn: Any, **kwargs: Any) -> None:
        with self._lock:
            if operation in self._active_workers:
                raise RuntimeError(f"Operation already running: {operation}")

            worker = BridgeWorker(operation=operation, fn=fn, **kwargs)
            self._active_workers[operation] = worker
            if len(self._active_workers) == 1:
                self.busy_changed.emit(True)

        worker.signals.started.connect(self.operation_started.emit)
        worker.signals.progress.connect(self.operation_progress.emit)
        worker.signals.finished.connect(self._on_finished)
        worker.signals.error.connect(self._on_error)
        worker.signals.cancelled.connect(self._on_cancelled)
        self._thread_pool.start(worker)

    def _finalize_operation(self, operation: str) -> None:
        with self._lock:
            self._active_workers.pop(operation, None)
            idle = not self._active_workers
        if idle:
            self.busy_changed.emit(False)

    @QtCore.Slot(str, object)
    def _on_finished(self, operation: str, payload: object) -> None:
        self._finalize_operation(operation)
        self.operation_finished.emit(operation, payload)

    @QtCore.Slot(str, str, str, str)
    def _on_error(
        self,
        operation: str,
        error_type: str,
        message: str,
        details: str,
    ) -> None:
        self._finalize_operation(operation)
        self.operation_error.emit(operation, error_type, message, details)

    @QtCore.Slot(str)
    def _on_cancelled(self, operation: str) -> None:
        self._finalize_operation(operation)
        self.operation_cancelled.emit(operation)

    def investigate(
        self,
        path: str | Path,
        scope: str,
        intent: str,
        name: str = "",
        notes: str = "",
    ) -> None:
        self._start_worker(
            "investigate",
            self._facade.run_investigation,
            path=path,
            scope=scope,
            intent=intent,
            name=name,
            notes=notes,
        )

    def observe(
        self,
        path: str | Path,
        eye_types: list[str],
        session_id: str | None = None,
    ) -> None:
        self._start_worker(
            "observe",
            self._facade.run_observation,
            path=path,
            eye_types=eye_types,
            session_id=session_id,
        )

    def query(
        self,
        question: str,
        question_type: str,
        focus: str | None = None,
        limit: int = 25,
        session_id: str | None = None,
    ) -> None:
        self._start_worker(
            "query",
            self._facade.run_query,
            question=question,
            question_type=question_type,
            focus=focus,
            limit=limit,
            session_id=session_id,
        )

    def pattern_list(
        self,
        category: str | None = None,
        show_disabled: bool = False,
    ) -> None:
        self._start_worker(
            "pattern_list",
            self._facade.run_pattern_list,
            category=category,
            show_disabled=show_disabled,
        )

    def pattern_scan(
        self,
        path: str | Path,
        category: str | None = None,
        pattern_ids: list[str] | None = None,
        glob: str = "*",
        max_files: int = 10000,
        session_id: str | None = None,
    ) -> None:
        self._start_worker(
            "pattern_scan",
            self._facade.run_pattern_scan,
            path=path,
            category=category,
            pattern_ids=pattern_ids,
            glob=glob,
            max_files=max_files,
            session_id=session_id,
        )

    def preview_export(
        self,
        session_id: str,
        format_name: str,
        include_notes: bool,
        include_patterns: bool,
        preview_limit: int | None = 4000,
    ) -> None:
        self._start_worker(
            "export_preview",
            self._facade.preview_export,
            session_id=session_id,
            format_name=format_name,
            include_notes=include_notes,
            include_patterns=include_patterns,
            preview_limit=preview_limit,
        )

    def export(
        self,
        session_id: str,
        format_name: str,
        output_path: str | Path,
        include_notes: bool,
        include_patterns: bool,
        include_evidence: bool,
    ) -> None:
        self._start_worker(
            "export",
            self._facade.run_export,
            session_id=session_id,
            format_name=format_name,
            output_path=output_path,
            include_notes=include_notes,
            include_patterns=include_patterns,
            include_evidence=include_evidence,
        )
