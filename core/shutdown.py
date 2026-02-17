"""
Truth-Safe Termination for CodeMarshal.

Constitutional Basis:
- Article 14: Graceful Degradation
- Article 15: Session Integrity

Production Responsibility:
Guarantee truth survival under all exit conditions.

This includes:
- Normal exit
- User interrupt
- Crash
- Constitution violation

What it must do:
1. Flush pending writes
2. Run corruption checks
3. Record termination reason
4. Never throw new errors
"""

from __future__ import annotations

import datetime
import json
import logging
import signal
import sys
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any

from core.context import RuntimeContext


def _default_flush_writes() -> bool:
    """Call storage flush hook with late binding for monkeypatch compatibility."""
    from storage import atomic

    return bool(atomic.flush_pending_writes())


def _default_atomic_write(target: Path, payload: Any, indent: int = 2) -> None:
    """Call storage atomic JSON writer with late binding."""
    from storage import atomic

    atomic.atomic_write_json_compatible(target, payload, indent=indent)


class TerminationReason(Enum):
    """Reasons for system termination."""

    NORMAL = auto()  # Clean shutdown
    USER_INTERRUPT = auto()  # Ctrl+C or SIGINT
    SYSTEM_SIGNAL = auto()  # Other signals (SIGTERM, etc.)
    CONSTITUTION_VIOLATION = auto()  # Tier 1-2 violation
    SYSTEM_FAILURE = auto()  # Unhandled exception
    RESOURCE_EXHAUSTION = auto()  # Memory, disk, etc.
    TIMEOUT = auto()  # Operation timeout
    MANUAL_OVERRIDE = auto()  # Forced shutdown


class TerminationSeverity(Enum):
    """Severity levels for termination."""

    INFO = auto()  # Normal shutdown
    WARNING = auto()  # Recoverable issue
    ERROR = auto()  # System failure
    FATAL = auto()  # Truth corruption risk


@dataclass(frozen=True)
class TerminationRecord:
    """Immutable record of system termination."""

    reason: TerminationReason
    severity: TerminationSeverity
    timestamp: datetime.datetime
    context: RuntimeContext
    error_message: str | None = None
    error_traceback: str | None = None
    pending_writes_flushed: bool = False
    corruption_checks_passed: bool = False
    session_saved: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "reason": self.reason.name,
            "severity": self.severity.name,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context.to_dict(),
            "error_message": self.error_message,
            "error_traceback": self.error_traceback,
            "pending_writes_flushed": self.pending_writes_flushed,
            "corruption_checks_passed": self.corruption_checks_passed,
            "session_saved": self.session_saved,
        }


class ShutdownManager:
    """
    Manages truth-safe termination of CodeMarshal.

    Constitutional Guarantees:
    1. Attempts to flush all pending writes before exit
    2. Runs corruption checks on stored evidence
    3. Records termination reason for audit trail
    4. Never throws new errors (catches and logs instead)
    5. Preserves session state when possible
    """

    def __init__(
        self,
        context: RuntimeContext,
        flush_writes_func: Callable[[], bool] | None = None,
        atomic_write_func: Callable[..., None] | None = None,
    ) -> None:
        """
        Initialize shutdown manager.

        Args:
            context: Immutable runtime context
            flush_writes_func: Optional callable to flush pending writes.
            atomic_write_func: Optional callable to perform atomic JSON writes.
        """
        if flush_writes_func is None:
            flush_writes_func = _default_flush_writes
        if atomic_write_func is None:
            atomic_write_func = _default_atomic_write

        self._context = context
        self._logger = self._create_logger()
        self._original_signal_handlers: dict[int, Any] = {}
        self._termination_record: TerminationRecord | None = None
        self._shutdown_initiated = False
        self._flush_writes_func = flush_writes_func
        self._atomic_write_func = atomic_write_func

        self._logger.debug("Shutdown manager initialized")

    def _create_logger(self) -> logging.Logger:
        """Create isolated shutdown logger."""
        logger = logging.getLogger(f"codemarshal.shutdown.{self._context.session_id}")

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s [SHUTDOWN] %(levelname)s: %(message)s",
                    datefmt="%H:%M:%S",
                )
            )
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False

        return logger

    def install_signal_handlers(self) -> None:
        """
        Install signal handlers for graceful termination.

        Constitutional Basis: Article 14 (Graceful Degradation)
        """
        try:
            # Store original handlers
            self._original_signal_handlers[signal.SIGINT] = signal.getsignal(
                signal.SIGINT
            )
            self._original_signal_handlers[signal.SIGTERM] = signal.getsignal(
                signal.SIGTERM
            )

            # Install our handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            self._logger.debug("Signal handlers installed")

        except Exception as e:
            self._logger.warning(f"Failed to install signal handlers: {e}")

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """
        Handle termination signals.

        Constitutional Basis: Article 14 (Graceful Degradation)
        """
        reason_mapping: dict[int, TerminationReason] = {
            signal.SIGINT: TerminationReason.USER_INTERRUPT,
            signal.SIGTERM: TerminationReason.SYSTEM_SIGNAL,
        }

        reason: TerminationReason = reason_mapping.get(
            signum, TerminationReason.SYSTEM_SIGNAL
        )
        self._logger.info(f"Received signal {signum}, initiating graceful shutdown")

        self.shutdown(
            reason=reason,
            severity=TerminationSeverity.WARNING,
            error_message=f"Signal {signum} received",
        )

        # Restore original handler and re-raise signal
        original_handler = self._original_signal_handlers.get(signum)
        if original_handler and callable(original_handler):
            signal.signal(signum, original_handler)
            signal.raise_signal(signum)

    def shutdown(
        self,
        reason: TerminationReason,
        severity: TerminationSeverity = TerminationSeverity.INFO,
        error_message: str | None = None,
        exception: Exception | None = None,
    ) -> TerminationRecord:
        """
        Execute truth-safe shutdown sequence.

        Constitutional Basis: Article 15 (Session Integrity)

        Args:
            reason: Why the system is shutting down
            severity: How severe the termination is
            error_message: Optional human-readable error
            exception: Optional exception that caused shutdown

        Returns:
            Termination record for audit trail
        """
        # Prevent multiple shutdowns
        if self._shutdown_initiated:
            self._logger.warning("Shutdown already initiated, ignoring duplicate call")
            return self._termination_record or self._create_minimal_record(
                reason, severity, error_message
            )

        self._shutdown_initiated = True
        self._logger.info(f"Initiating shutdown: {reason.name} ({severity.name})")

        try:
            # Step 1: Flush pending writes (with error suppression)
            pending_writes_flushed = self._flush_pending_writes()

            # Step 2: Run corruption checks (with error suppression)
            corruption_checks_passed = self._run_corruption_checks()

            # Step 3: Save session state if possible
            session_saved = self._save_session_state()

            # Step 4: Create termination record
            self._termination_record = TerminationRecord(
                reason=reason,
                severity=severity,
                timestamp=datetime.datetime.now(datetime.UTC),
                context=self._context,
                error_message=error_message or str(exception) if exception else None,
                error_traceback=traceback.format_exc() if exception else None,
                pending_writes_flushed=pending_writes_flushed,
                corruption_checks_passed=corruption_checks_passed,
                session_saved=session_saved,
            )

            # Step 5: Log termination
            self._log_termination()

            self._logger.info(f"Shutdown completed: {reason.name}")

            return self._termination_record

        except Exception as shutdown_error:
            # Article 14: Never throw new errors during shutdown
            self._logger.critical(
                f"Shutdown procedure failed: {shutdown_error}\n"
                f"Original termination reason: {reason.name}"
            )

            # Create minimal record as last resort
            self._termination_record = self._create_minimal_record(
                reason=reason,
                severity=TerminationSeverity.FATAL,
                error_message=f"Shutdown failed: {shutdown_error}. Original: {error_message}",
            )

            return self._termination_record

    def _flush_pending_writes(self) -> bool:
        """
        Flush all pending writes to storage.

        Constitutional Basis: Article 15 (Session Integrity)
        Returns True if successful, False otherwise (but never raises).
        """
        try:
            self._logger.debug("Flushing pending writes...")
            flushed = self._flush_writes_func()
            if not flushed:
                self._logger.warning("Pending writes flush reported failure")
                return False

            self._logger.info("Pending writes flushed")
            return True

        except Exception as e:
            self._logger.error(f"Failed to flush pending writes: {e}")
            return False

    def _run_corruption_checks(self) -> bool:
        """
        Run corruption checks on stored evidence.

        Constitutional Basis: Article 15 (Session Integrity)
        Returns True if checks pass, False otherwise (but never raises).
        """
        try:
            self._logger.debug("Running corruption checks...")

            from observations.record.snapshot import load_snapshot
            from storage.corruption import detect_corruption

            snapshot = load_snapshot()
            if snapshot is None:
                return True

            if hasattr(snapshot, "to_dict"):
                payload: Any = snapshot.to_dict()
            elif isinstance(snapshot, dict):
                payload = snapshot
            else:
                payload = dict(snapshot)

            snapshot_bytes = json.dumps(payload, default=str, sort_keys=True).encode(
                "utf-8"
            )
            corruption = detect_corruption(snapshot_bytes, "session_context")
            if corruption:
                corruption_type = (
                    corruption.get("corruption_type")
                    if isinstance(corruption, dict)
                    else getattr(corruption, "corruption_type", "unknown")
                )
                self._logger.error(f"Corruption detected: {corruption_type}")
                return False

            self._logger.info("Corruption checks passed")
            return True
        except FileNotFoundError:
            self._logger.info("No snapshot found; corruption checks skipped")
            return True
        except Exception as e:
            self._logger.error(f"Corruption checks failed: {e}")
            return False

    def _save_session_state(self) -> bool:
        """
        Save session state for possible recovery.

        Constitutional Basis: Article 15 (Session Integrity)
        Returns True if saved, False otherwise (but never raises).
        """
        try:
            self._logger.debug("Saving session state...")
            from core.state import get_current_state

            current_state = get_current_state()
            state_payload = (
                current_state.to_dict()
                if hasattr(current_state, "to_dict")
                else dict(current_state)
            )

            session_dir = Path(".codemarshal") / "session_state"
            session_dir.mkdir(parents=True, exist_ok=True)
            target = session_dir / f"{self._context.session_id_str}.json"
            try:
                self._atomic_write_func(target, state_payload, indent=2)
            except TypeError:
                try:
                    self._atomic_write_func(target, state_payload, 2)
                except TypeError:
                    self._atomic_write_func(target, state_payload)

            self._logger.info("Session state saved")
            return True

        except Exception as e:
            self._logger.warning(f"Failed to save session state: {e}")
            return False

    def _log_termination(self) -> None:
        """Log termination details for audit trail."""
        if not self._termination_record:
            return

        record = self._termination_record
        log_method = {
            TerminationSeverity.INFO: self._logger.info,
            TerminationSeverity.WARNING: self._logger.warning,
            TerminationSeverity.ERROR: self._logger.error,
            TerminationSeverity.FATAL: self._logger.critical,
        }.get(record.severity, self._logger.info)

        message = f"Termination: {record.reason.name} ({record.severity.name})"
        if record.error_message:
            message += f" - {record.error_message}"

        log_method(message)

        # Log context for debugging
        self._logger.debug(f"Termination context: {self._context}")

    def _create_minimal_record(
        self,
        reason: TerminationReason,
        severity: TerminationSeverity,
        error_message: str | None = None,
    ) -> TerminationRecord:
        """Create minimal termination record when everything else fails."""
        return TerminationRecord(
            reason=reason,
            severity=severity,
            timestamp=datetime.datetime.now(datetime.UTC),
            context=self._context,
            error_message=error_message or "Emergency shutdown",
            pending_writes_flushed=False,
            corruption_checks_passed=False,
            session_saved=False,
        )

    def get_termination_record(self) -> TerminationRecord | None:
        """Get the termination record if shutdown has occurred."""
        return self._termination_record

    def is_shutdown_initiated(self) -> bool:
        """Check if shutdown has been initiated."""
        return self._shutdown_initiated

    def __repr__(self) -> str:
        """Machine-readable representation."""
        status = "active"
        if self._shutdown_initiated:
            status = "shutting_down"
        if self._termination_record:
            status = "terminated"

        return f"ShutdownManager(status={status}, context={self._context.session_id_str[:8]})"


# Module-level shutdown manager singleton
_SHUTDOWN_MANAGER: ShutdownManager | None = None


def initialize_shutdown(
    context: RuntimeContext,
    flush_writes_func: Callable[[], bool],
    atomic_write_func: Callable[[Path, Any, int], None],
) -> None:
    """
    Initialize the shutdown system with a runtime context and injected dependencies.

    Args:
        context: The runtime context for shutdown operations.
        flush_writes_func: Callable to flush pending writes.
        atomic_write_func: Callable to perform atomic JSON writes.
    """
    global _SHUTDOWN_MANAGER
    _SHUTDOWN_MANAGER = ShutdownManager(context, flush_writes_func, atomic_write_func)
    _SHUTDOWN_MANAGER.install_signal_handlers()


def shutdown(
    reason: TerminationReason,
    exit_code: int = 0,
    error_info: tuple[Exception, str] | None = None,
) -> None:
    """
    Initiate system shutdown.

    Args:
        reason: The termination reason
        exit_code: Exit code for the process
        error_info: Optional tuple of (exception, traceback_string)
    """
    global _SHUTDOWN_MANAGER

    if _SHUTDOWN_MANAGER is None:
        # Emergency shutdown - no manager initialized
        if error_info:
            print(f"Emergency shutdown: {error_info[0]}", file=sys.stderr)
        sys.exit(exit_code)

    # Map reason to severity
    severity_map = {
        TerminationReason.NORMAL: TerminationSeverity.INFO,
        TerminationReason.USER_INTERRUPT: TerminationSeverity.WARNING,
        TerminationReason.SYSTEM_SIGNAL: TerminationSeverity.WARNING,
        TerminationReason.CONSTITUTION_VIOLATION: TerminationSeverity.ERROR,
        TerminationReason.SYSTEM_FAILURE: TerminationSeverity.ERROR,
        TerminationReason.RESOURCE_EXHAUSTION: TerminationSeverity.ERROR,
        TerminationReason.TIMEOUT: TerminationSeverity.WARNING,
        TerminationReason.MANUAL_OVERRIDE: TerminationSeverity.WARNING,
    }

    severity = severity_map.get(reason, TerminationSeverity.ERROR)
    error_message = None
    exception = None

    if error_info:
        exception, error_message = error_info[0], str(error_info[0])

    _SHUTDOWN_MANAGER.shutdown(
        reason=reason,
        severity=severity,
        error_message=error_message,
        exception=exception,
    )

    sys.exit(exit_code)


def emergency_shutdown(message: str = "Emergency shutdown", exit_code: int = 1) -> None:
    """
    Emergency shutdown without a manager - use when normal shutdown is unavailable.

    Args:
        message: Error message to display
        exit_code: Exit code for the process
    """
    print(f"[EMERGENCY SHUTDOWN] {message}", file=sys.stderr)
    sys.exit(exit_code)
