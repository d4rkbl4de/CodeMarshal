"""
Error monitoring for CodeMarshal's truth-preserving operations.

Purpose:
    Detect, log, and classify runtime errors or failures in truth-preserving operations.
    Ensure transparency when parts of the system fail (aligning with Tier 4: Graceful Degradation).

Constitutional Constraints:
    Article 3: Truth Preservation - Never obscure, distort, or invent error information
    Article 8: Honest Performance - Explain why something cannot be computed
    Article 14: Graceful Degradation - Show available observations even when some fail
    Article 17: Minimal Decoration - Error reporting must be simple and truthful
"""

import traceback
import sys
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, asdict, field
from pathlib import Path
import json
import threading
import warnings
from contextlib import contextmanager

# Core imports
from core.context import RuntimeContext
from core.state import InvestigationState

# Type aliases for clarity
from typing import TypedDict


class ErrorSeverity(Enum):
    """
    Error severity levels aligned with constitutional truth preservation.
    
    Levels:
        CRITICAL: System cannot continue, constitutional violation
        ERROR: Operation failed, but system can continue
        WARNING: Potential issue, but operation succeeded
        INFO: Informational message about system behavior
        UNCERTAINTY: Explicit uncertainty (⚠️) as per Article 3
    """
    CRITICAL = auto()    # Tier 1-2 constitutional violations
    ERROR = auto()       # Tier 3-4 issues requiring attention
    WARNING = auto()     # Performance or minor issues
    INFO = auto()        # Informational messages
    UNCERTAINTY = auto() # Explicit uncertainty markers


class ErrorCategory(Enum):
    """
    Categorization of error types for structured analysis.
    """
    # Observation layer errors
    OBSERVATION_FAILED = auto()      # Cannot observe what exists
    SNAPSHOT_CORRUPTED = auto()      # Stored observation corrupted
    VALIDATION_FAILED = auto()       # Observation validation failed
    
    # Inquiry layer errors
    PATTERN_FAILED = auto()          # Pattern detection failed
    QUERY_FAILED = auto()            # Human question cannot be answered
    NOTEBOOK_CORRUPTED = auto()      # Human thinking corrupted
    
    # Interface layer errors
    RENDER_FAILED = auto()           # Cannot render interface
    NAVIGATION_FAILED = auto()       # Navigation operation failed
    
    # System errors
    PERMISSION_DENIED = auto()       # Filesystem permission issues
    RESOURCE_EXHAUSTED = auto()      # Memory, disk, or CPU limits
    INTEGRITY_VIOLATION = auto()     # Constitutional violation detected
    UNEXPECTED_ERROR = auto()        # Unknown or unclassified error
    
    # Performance errors
    TIMEOUT = auto()                 # Operation timed out
    SLOW_PERFORMANCE = auto()        # Performance below threshold


class ErrorRecordDict(TypedDict):
    """Type-safe dictionary for error records."""
    error_id: str
    timestamp: str
    severity: str
    category: str
    message: str
    module: str
    function: str
    investigation_id: str
    traceback: Optional[str]
    context: Dict[str, Any]
    resolved: bool
    resolution: Optional[str]


@dataclass(frozen=True)
class ErrorRecord:
    """
    Immutable error record for audit trail and recovery.
    
    Frozen to prevent modification after creation, ensuring
    truth preservation (Article 3) and immutability (Article 9).
    """
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    module: str
    function: str
    investigation_id: str
    traceback: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution: Optional[str] = None
    
    def to_dict(self) -> ErrorRecordDict:
        """Convert to dictionary for serialization."""
        return ErrorRecordDict(
            error_id=self.error_id,
            timestamp=self.timestamp.isoformat(),
            severity=self.severity.name,
            category=self.category.name,
            message=self.message,
            module=self.module,
            function=self.function,
            investigation_id=self.investigation_id,
            traceback=self.traceback,
            context=self.context.copy(),
            resolved=self.resolved,
            resolution=self.resolution
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorRecord':
        """Create from dictionary with validation."""
        return cls(
            error_id=str(data['error_id']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            severity=ErrorSeverity[data['severity']],
            category=ErrorCategory[data['category']],
            message=str(data['message']),
            module=str(data['module']),
            function=str(data['function']),
            investigation_id=str(data['investigation_id']),
            traceback=str(data['traceback']) if data.get('traceback') else None,
            context=dict(data.get('context', {})),
            resolved=bool(data.get('resolved', False)),
            resolution=str(data['resolution']) if data.get('resolution') else None
        )
    
    def with_resolution(self, resolution: str) -> 'ErrorRecord':
        """
        Create a new error record with resolution.
        
        Returns a new instance (immutable), does not modify self.
        """
        return ErrorRecord(
            error_id=self.error_id,
            timestamp=self.timestamp,
            severity=self.severity,
            category=self.category,
            message=self.message,
            module=self.module,
            function=self.function,
            investigation_id=self.investigation_id,
            traceback=self.traceback,
            context=self.context.copy(),
            resolved=True,
            resolution=resolution
        )
    
    def get_truth_preserving_message(self) -> str:
        """
        Generate a truth-preserving error message per constitutional rules.
        
        Article 3: When truth is uncertain, show uncertainty clearly (⚠️).
        Article 3: When truth is unknown, say "I cannot see this."
        """
        if self.severity == ErrorSeverity.UNCERTAINTY:
            return f"⚠️ {self.message}"
        elif self.category == ErrorCategory.OBSERVATION_FAILED:
            return f"I cannot see this: {self.message}"
        else:
            # Include category and severity for clarity
            return f"[{self.severity.name}] {self.category.name}: {self.message}"


class ErrorMonitor:
    """
    Thread-safe error monitoring system.
    
    Design Principles:
    1. Never silence errors (Article 3: Truth Preservation)
    2. Provide structured context for recovery
    3. Allow graceful degradation when parts fail
    4. Immutable error records for audit trail
    """
    
    def __init__(self, context: RuntimeContext):
        """
        Initialize error monitor.
        
        Args:
            context: Current runtime context for investigation ID
        """
        self.context: RuntimeContext = context
        self._errors: List[ErrorRecord] = []
        self._lock: threading.RLock = threading.RLock()
        self._error_handlers: List[Callable[[ErrorRecord], None]] = []
        self._error_id_counter: int = 0
        
        # Register default handlers
        self._register_default_handlers()
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID."""
        with self._lock:
            self._error_id_counter += 1
            return f"ERR-{self.context.investigation_id}-{self._error_id_counter:08d}"
    
    def _register_default_handlers(self) -> None:
        """Register default error handlers."""
        # Critical errors trigger immediate attention
        self.register_handler(self._handle_critical_errors)
        # All errors get logged to stderr for transparency
        self.register_handler(self._log_error_to_stderr)
    
    def _handle_critical_errors(self, error: ErrorRecord) -> None:
        """Handle critical errors (constitutional violations)."""
        if error.severity == ErrorSeverity.CRITICAL:
            # Critical errors should be very rare and serious
            print(
                f"\n🚨 CRITICAL ERROR - Constitutional Violation\n"
                f"   {error.message}\n"
                f"   Module: {error.module}.{error.function}\n"
                f"   Error ID: {error.error_id}\n",
                file=sys.stderr
            )
    
    def _log_error_to_stderr(self, error: ErrorRecord) -> None:
        """Log all errors to stderr for transparency."""
        msg = error.get_truth_preserving_message()
        print(f"[{error.timestamp.isoformat()}] {msg}", file=sys.stderr)
        if error.traceback:
            print(f"Traceback:\n{error.traceback}", file=sys.stderr)
    
    def register_handler(self, handler: Callable[[ErrorRecord], None]) -> None:
        """Register a custom error handler."""
        with self._lock:
            self._error_handlers.append(handler)
    
    def record_error(self,
                     severity: ErrorSeverity,
                     category: ErrorCategory,
                     message: str,
                     module: str,
                     function: str,
                     exception: Optional[Exception] = None,
                     **context: Any) -> ErrorRecord:
        """
        Record an error with full context.
        
        Args:
            severity: Error severity level
            category: Error category
            message: Human-readable error message
            module: Module where error occurred
            function: Function where error occurred
            exception: Optional exception object
            **context: Additional context for debugging
            
        Returns:
            ErrorRecord that was created
        """
        error_id = self._generate_error_id()
        timestamp = datetime.now(timezone.utc)
        
        # Capture traceback if exception provided
        traceback_str = None
        if exception:
            traceback_str = ''.join(traceback.format_exception(
                type(exception), exception, exception.__traceback__
            ))
        elif severity in [ErrorSeverity.CRITICAL, ErrorSeverity.ERROR]:
            # For critical errors without exception, capture current traceback
            traceback_str = ''.join(traceback.format_stack())
        
        # Create error record
        error = ErrorRecord(
            error_id=error_id,
            timestamp=timestamp,
            severity=severity,
            category=category,
            message=message,
            module=module,
            function=function,
            investigation_id=self.context.investigation_id,
            traceback=traceback_str,
            context=context,
            resolved=False
        )
        
        # Store error
        with self._lock:
            self._errors.append(error)
        
        # Call all registered handlers
        for handler in self._error_handlers:
            try:
                handler(error)
            except Exception as e:
                # Don't let handler errors break the monitoring system
                print(f"Error handler failed: {e}", file=sys.stderr)
        
        return error
    
    @contextmanager
    def capture_errors(self,
                       severity: ErrorSeverity,
                       category: ErrorCategory,
                       module: str,
                       function: str,
                       **context: Any):
        """
        Context manager for capturing errors in a block of code.
        
        Usage:
            with monitor.capture_errors(
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.OBSERVATION_FAILED,
                module="observations.eyes",
                function="file_sight.observe_file"
            ):
                # Code that might fail
        """
        try:
            yield
        except Exception as e:
            self.record_error(
                severity=severity,
                category=category,
                message=str(e),
                module=module,
                function=function,
                exception=e,
                **context
            )
            raise
    
    def record_uncertainty(self,
                           message: str,
                           module: str,
                           function: str,
                           **context: Any) -> ErrorRecord:
        """
        Record explicit uncertainty (⚠️) as per Article 3.
        
        Args:
            message: Uncertainty description
            module: Module where uncertainty occurs
            function: Function where uncertainty occurs
            **context: Additional context
            
        Returns:
            ErrorRecord with UNCERTAINTY severity
        """
        return self.record_error(
            severity=ErrorSeverity.UNCERTAINTY,
            category=ErrorCategory.UNEXPECTED_ERROR,
            message=message,
            module=module,
            function=function,
            exception=None,
            **context
        )
    
    def get_errors(self,
                   severity: Optional[ErrorSeverity] = None,
                   category: Optional[ErrorCategory] = None,
                   resolved: Optional[bool] = None,
                   module: Optional[str] = None,
                   limit: int = 1000) -> List[ErrorRecord]:
        """
        Get errors with optional filtering.
        
        Args:
            severity: Filter by severity level
            category: Filter by category
            resolved: Filter by resolution status
            module: Filter by module name
            limit: Maximum number of errors to return
            
        Returns:
            List of matching error records (newest first)
        """
        with self._lock:
            errors = self._errors.copy()
        
        # Filter errors
        filtered_errors = []
        for error in reversed(errors):  # Newest first
            if severity is not None and error.severity != severity:
                continue
            if category is not None and error.category != category:
                continue
            if resolved is not None and error.resolved != resolved:
                continue
            if module is not None and error.module != module:
                continue
            
            filtered_errors.append(error)
            if len(filtered_errors) >= limit:
                break
        
        return filtered_errors
    
    def mark_resolved(self, error_id: str, resolution: str) -> bool:
        """
        Mark an error as resolved.
        
        Args:
            error_id: Error ID to resolve
            resolution: Resolution description
            
        Returns:
            True if error was found and marked, False otherwise
        """
        with self._lock:
            for i, error in enumerate(self._errors):
                if error.error_id == error_id:
                    # Replace with resolved version
                    resolved_error = error.with_resolution(resolution)
                    self._errors[i] = resolved_error
                    return True
        
        return False
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Generate summary statistics for error monitoring.
        
        Returns:
            Dictionary with error statistics and health indicators
        """
        with self._lock:
            errors = self._errors.copy()
        
        if not errors:
            return {
                "total_errors": 0,
                "unresolved_errors": 0,
                "health_status": "HEALTHY",
                "severity_distribution": {},
                "category_distribution": {},
                "recent_errors": [],
                "warnings": []
            }
        
        # Count statistics
        total_errors = len(errors)
        unresolved_errors = sum(1 for e in errors if not e.resolved)
        
        severity_distribution: Dict[str, int] = {}
        category_distribution: Dict[str, int] = {}
        
        for error in errors:
            sev_name = error.severity.name
            cat_name = error.category.name
            
            severity_distribution[sev_name] = severity_distribution.get(sev_name, 0) + 1
            category_distribution[cat_name] = category_distribution.get(cat_name, 0) + 1
        
        # Determine health status
        critical_count = severity_distribution.get("CRITICAL", 0)
        error_count = severity_distribution.get("ERROR", 0)
        
        if critical_count > 0:
            health_status = "CRITICAL"
        elif error_count > 5:
            health_status = "DEGRADED"
        elif unresolved_errors > 10:
            health_status = "UNSTABLE"
        else:
            health_status = "HEALTHY"
        
        # Get recent errors (last 10)
        recent_errors = [
            {
                "id": e.error_id,
                "timestamp": e.timestamp.isoformat(),
                "severity": e.severity.name,
                "message": e.message[:100] + "..." if len(e.message) > 100 else e.message,
                "resolved": e.resolved
            }
            for e in sorted(errors, key=lambda x: x.timestamp, reverse=True)[:10]
        ]
        
        # Generate warnings based on error patterns
        warning_messages = []
        if critical_count > 0:
            warning_messages.append("🚨 Critical errors detected - constitutional violations may exist")
        if unresolved_errors > 20:
            warning_messages.append(f"⚠️ High number of unresolved errors: {unresolved_errors}")
        if ErrorCategory.INTEGRITY_VIOLATION.name in category_distribution:
            warning_messages.append("⚠️ Integrity violations detected - system may not be preserving truth")
        
        return {
            "total_errors": total_errors,
            "unresolved_errors": unresolved_errors,
            "health_status": health_status,
            "severity_distribution": severity_distribution,
            "category_distribution": category_distribution,
            "recent_errors": recent_errors,
            "warnings": warning_messages,
            "investigation_id": self.context.investigation_id,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def save_to_disk(self, path: Optional[Path] = None) -> Path:
        """
        Save error records to disk for audit trail.
        
        Args:
            path: Optional custom path, defaults to investigation directory
            
        Returns:
            Path where errors were saved
        """
        from storage.layout import get_investigation_path
        
        if path is None:
            inv_path = get_investigation_path(self.context.investigation_id)
            path = inv_path / "errors" / f"errors_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            errors_data = [e.to_dict() for e in self._errors]
            summary = self.get_summary()
        
        data = {
            "errors": errors_data,
            "summary": summary,
            "metadata": {
                "investigation_id": self.context.investigation_id,
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "error_count": len(errors_data)
            }
        }
        
        # Atomic write
        temp_path = path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        temp_path.rename(path)
        
        return path
    
    def load_from_disk(self, path: Path) -> int:
        """
        Load error records from disk.
        
        Args:
            path: Path to error records file
            
        Returns:
            Number of errors loaded
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            loaded_errors = []
            for error_data in data.get('errors', []):
                try:
                    error = ErrorRecord.from_dict(error_data)
                    loaded_errors.append(error)
                except (KeyError, ValueError) as e:
                    # Log but skip invalid records
                    print(f"Failed to load error record: {e}", file=sys.stderr)
            
            with self._lock:
                self._errors.extend(loaded_errors)
            
            return len(loaded_errors)
            
        except Exception as e:
            # Record the loading error
            self.record_error(
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.SNAPSHOT_CORRUPTED,
                message=f"Failed to load error records: {str(e)}",
                module="integrity.monitoring.errors",
                function="load_from_disk",
                exception=e
            )
            return 0
    
    def clear_resolved(self) -> int:
        """
        Clear all resolved error records.
        
        Returns:
            Number of errors cleared
        """
        with self._lock:
            unresolved_errors = [e for e in self._errors if not e.resolved]
            cleared_count = len(self._errors) - len(unresolved_errors)
            self._errors = unresolved_errors
        
        return cleared_count


# Global error monitor instance (thread-safe singleton pattern)
_ERROR_MONITOR: Optional[ErrorMonitor] = None
_MONITOR_LOCK: threading.RLock = threading.RLock()


def get_error_monitor(context: Optional[RuntimeContext] = None) -> ErrorMonitor:
    """
    Get or create the global error monitor.
    
    Args:
        context: Runtime context (required on first call)
        
    Returns:
        ErrorMonitor instance
        
    Raises:
        ValueError: If context is None and monitor hasn't been initialized
    """
    global _ERROR_MONITOR
    
    with _MONITOR_LOCK:
        if _ERROR_MONITOR is None:
            if context is None:
                raise ValueError("RuntimeContext required for first initialization")
            _ERROR_MONITOR = ErrorMonitor(context)
        
        return _ERROR_MONITOR


def monitor_errors(context: Optional[RuntimeContext] = None) -> Dict[str, Any]:
    """
    Main function for error monitoring.
    
    Called from core/engine.py or bridge/coordination/scheduling.py.
    
    Args:
        context: Runtime context (optional, uses existing monitor if available)
        
    Returns:
        Structured error report
    """
    try:
        monitor = get_error_monitor(context)
        summary = monitor.get_summary()
        
        # Add constitutional compliance check
        if summary["health_status"] in ["CRITICAL", "DEGRADED"]:
            summary["constitutional_status"] = "VIOLATED"
        else:
            summary["constitutional_status"] = "COMPLIANT"
        
        return summary
        
    except Exception as e:
        # Even error monitoring can fail - be honest about it
        return {
            "error": f"Error monitoring failed: {type(e).__name__}: {str(e)}",
            "total_errors": 0,
            "unresolved_errors": 0,
            "health_status": "UNKNOWN",
            "constitutional_status": "UNKNOWN",
            "severity_distribution": {},
            "category_distribution": {},
            "recent_errors": [],
            "warnings": ["Error monitoring temporarily unavailable"],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }


@contextmanager
def capture_operation_errors(severity: ErrorSeverity,
                             category: ErrorCategory,
                             module: str,
                             function: str,
                             context: Optional[RuntimeContext] = None,
                             **error_context: Any):
    """
    Convenience context manager for capturing errors in any operation.
    
    Usage:
        with capture_operation_errors(
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.OBSERVATION_FAILED,
            module="my.module",
            function="my_function",
            custom_context="value"
        ):
            # operation that might fail
    """
    monitor = get_error_monitor(context)
    
    with monitor.capture_errors(
        severity=severity,
        category=category,
        module=module,
        function=function,
        **error_context
    ):
        yield


def record_uncertainty(message: str,
                       module: str,
                       function: str,
                       context: Optional[RuntimeContext] = None,
                       **context_kwargs: Any) -> ErrorRecord:
    """
    Record explicit uncertainty (⚠️) as per Article 3.
    
    Convenience function for use throughout the system.
    """
    monitor = get_error_monitor(context)
    return monitor.record_uncertainty(
        message=message,
        module=module,
        function=function,
        **context_kwargs
    )


def check_constitutional_errors(context: RuntimeContext) -> List[Dict[str, Any]]:
    """
    Check for constitutional violations in error records.
    
    Returns list of constitutional issues with severity and context.
    """
    monitor = get_error_monitor(context)
    errors = monitor.get_errors(
        severity=ErrorSeverity.CRITICAL,
        category=ErrorCategory.INTEGRITY_VIOLATION,
        resolved=False
    )
    
    issues = []
    for error in errors:
        issues.append({
            "severity": "CRITICAL",
            "type": "CONSTITUTIONAL_VIOLATION",
            "error_id": error.error_id,
            "message": error.message,
            "module": error.module,
            "function": error.function,
            "timestamp": error.timestamp.isoformat(),
            "context": error.context
        })
    
    return issues


# Test function for module validation
def test_error_monitoring() -> Dict[str, Any]:
    """
    Test the error monitoring system.
    
    Returns:
        Test results with pass/fail status
    """
    from core.context import RuntimeContext
    
    # Create test context
    test_context = RuntimeContext(
        investigation_id="test_errors",
        root_path=Path.cwd(),
        config={},
        started_at=datetime.now(timezone.utc)
    )
    
    results = {
        "module": "integrity.monitoring.errors",
        "tests_passed": 0,
        "tests_failed": 0,
        "details": []
    }
    
    try:
        # Test 1: Monitor creation
        monitor = ErrorMonitor(test_context)
        assert monitor.context.investigation_id == "test_errors"
        results["tests_passed"] += 1
        results["details"].append("Test 1: Monitor creation ✓")
        
        # Test 2: Error recording
        error = monitor.record_error(
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.OBSERVATION_FAILED,
            message="Test error message",
            module="test.module",
            function="test_function",
            exception=None,
            test_key="test_value"
        )
        
        assert error.error_id.startswith("ERR-test_errors-")
        assert error.message == "Test error message"
        assert error.severity == ErrorSeverity.ERROR
        assert error.context.get("test_key") == "test_value"
        
        results["tests_passed"] += 1
        results["details"].append("Test 2: Error recording ✓")
        
        # Test 3: Error retrieval
        errors = monitor.get_errors()
        assert len(errors) == 1
        assert errors[0].error_id == error.error_id
        
        results["tests_passed"] += 1
        results["details"].append("Test 3: Error retrieval ✓")
        
        # Test 4: Context manager error capture
        try:
            with monitor.capture_errors(
                severity=ErrorSeverity.WARNING,
                category=ErrorCategory.PERFORMANCE_FAILED,
                module="test",
                function="context_test",
                custom="data"
            ):
                raise ValueError("Test exception in context manager")
        except ValueError:
            pass
        
        captured_errors = monitor.get_errors(category=ErrorCategory.PERFORMANCE_FAILED)
        assert len(captured_errors) == 1
        assert "Test exception" in captured_errors[0].message
        assert captured_errors[0].context.get("custom") == "data"
        
        results["tests_passed"] += 1
        results["details"].append("Test 4: Context manager error capture ✓")
        
        # Test 5: Uncertainty recording
        uncertainty = monitor.record_uncertainty(
            message="Cannot determine file encoding",
            module="observations.eyes",
            function="encoding_sight.detect_encoding"
        )
        
        assert uncertainty.severity == ErrorSeverity.UNCERTAINTY
        assert "⚠️" in uncertainty.get_truth_preserving_message()
        
        results["tests_passed"] += 1
        results["details"].append("Test 5: Uncertainty recording ✓")
        
        # Test 6: Error resolution
        success = monitor.mark_resolved(error.error_id, "Test resolution")
        assert success
        
        resolved_error = monitor.get_errors(error_id=error.error_id)[0]
        assert resolved_error.resolved
        assert resolved_error.resolution == "Test resolution"
        
        results["tests_passed"] += 1
        results["details"].append("Test 6: Error resolution ✓")
        
        # Test 7: Summary generation
        summary = monitor.get_summary()
        assert "total_errors" in summary
        assert summary["total_errors"] == 3  # Error + captured + uncertainty
        assert "ERROR" in summary["severity_distribution"]
        
        results["tests_passed"] += 1
        results["details"].append("Test 7: Summary generation ✓")
        
        # Test 8: Global monitor access
        global_monitor = get_error_monitor(test_context)
        assert global_monitor is monitor
        
        results["tests_passed"] += 1
        results["details"].append("Test 8: Global monitor access ✓")
        
        # Test 9: Clear resolved
        cleared = monitor.clear_resolved()
        assert cleared >= 1  # At least the resolved test error
        
        unresolved = monitor.get_errors(resolved=False)
        assert all(not e.resolved for e in unresolved)
        
        results["tests_passed"] += 1
        results["details"].append("Test 9: Clear resolved ✓")
        
    except Exception as e:
        results["tests_failed"] += 1
        results["details"].append(f"Test failed: {type(e).__name__}: {str(e)}")
        import traceback
        results["details"].append(f"Traceback: {traceback.format_exc()}")
    
    return results


# Export public API
__all__ = [
    'ErrorSeverity',
    'ErrorCategory',
    'ErrorRecord',
    'ErrorMonitor',
    'get_error_monitor',
    'monitor_errors',
    'capture_operation_errors',
    'record_uncertainty',
    'check_constitutional_errors',
    'test_error_monitoring'
]