"""Worker utilities for desktop background operations."""

from __future__ import annotations

import threading
import traceback
from collections.abc import Callable
from typing import Any

from PySide6 import QtCore

from .exceptions import OperationCancelledError


class WorkerSignals(QtCore.QObject):
    """Signals emitted by background workers."""

    started = QtCore.Signal(str)
    progress = QtCore.Signal(str, int, int, str)
    finished = QtCore.Signal(str, object)
    error = QtCore.Signal(str, str, str, str)
    cancelled = QtCore.Signal(str)


class BridgeWorker(QtCore.QRunnable):
    """QRunnable wrapper for facade operations."""

    def __init__(self, operation: str, fn: Callable[..., Any], **kwargs: Any) -> None:
        super().__init__()
        self.operation = operation
        self.fn = fn
        self.kwargs = dict(kwargs)
        self.signals = WorkerSignals()
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        """Request cancellation for this worker."""
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        """Return True if cancellation was requested."""
        return self._cancel_event.is_set()

    def run(self) -> None:
        """Execute the wrapped callable."""
        self.signals.started.emit(self.operation)

        def _progress(current: int, total: int, message: str = "") -> None:
            self.signals.progress.emit(self.operation, current, total, message)

        try:
            result = self.fn(
                progress_callback=_progress,
                cancel_event=self._cancel_event,
                **self.kwargs,
            )
            if self._cancel_event.is_set():
                self.signals.cancelled.emit(self.operation)
                return
            self.signals.finished.emit(self.operation, result)
        except OperationCancelledError:
            self.signals.cancelled.emit(self.operation)
        except Exception as exc:  # pragma: no cover - defensive
            self.signals.error.emit(
                self.operation,
                exc.__class__.__name__,
                str(exc),
                traceback.format_exc(limit=12),
            )
