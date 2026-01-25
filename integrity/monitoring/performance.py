"""
Performance monitoring for CodeMarshal's truth-preserving operations.

Purpose:
    Measure system performance metrics without interfering with truth preservation.
    Track latency of observation recording, query execution times, and snapshot processing.

Constitutional Constraints:
    Article 8: Honest Performance - Show indicators for computation time
    Article 13: Deterministic Operation - Performance measurements should not affect timing
    Article 14: Graceful Degradation - Continue measuring even if some metrics fail
"""

import json
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# Type aliases for clarity
from typing import Any, TypedDict, cast

# Core imports
from core.context import RuntimeContext
from storage.layout import get_investigation_path


class PerformanceEventDict(TypedDict):
    """Type-safe dictionary for performance events."""

    operation: str
    start_time: str
    end_time: str
    duration_ms: float
    investigation_id: str
    module: str
    function: str
    success: bool
    error: str | None
    tags: dict[str, Any]


@dataclass(frozen=True)
class PerformanceEvent:
    """
    Immutable performance measurement event.

    Frozen to prevent modification after creation, aligning with
    Article 9: Immutable Observations.
    """

    operation: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    investigation_id: str
    module: str
    function: str
    success: bool
    error: str | None = None
    tags: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> PerformanceEventDict:
        """Convert to dictionary for serialization."""
        return cast(
            PerformanceEventDict,
            {
                "operation": self.operation,
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration_ms": round(self.duration_ms, 2),
                "investigation_id": self.investigation_id,
                "module": self.module,
                "function": self.function,
                "success": self.success,
                "error": self.error,
                "tags": self.tags.copy(),
            },
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PerformanceEvent":
        """Create from dictionary, with validation."""
        return cls(
            operation=str(data["operation"]),
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            duration_ms=float(data["duration_ms"]),
            investigation_id=str(data["investigation_id"]),
            module=str(data["module"]),
            function=str(data["function"]),
            success=bool(data["success"]),
            error=str(data["error"]) if data.get("error") else None,
            tags=dict(data.get("tags", {})),
        )


class PerformanceMonitor:
    """
    Thread-safe performance monitoring system.

    Design Principles:
    1. Non-intrusive: Does not affect observed operations
    2. Thread-safe: Can be used from multiple threads
    3. Immutable events: Once recorded, cannot be modified
    4. Honest reporting: No smoothing, no filtering
    """

    def __init__(self, context: RuntimeContext):
        """
        Initialize performance monitor.

        Args:
            context: Current runtime context for investigation ID and paths
        """
        self.context: RuntimeContext = context
        self._events: list[PerformanceEvent] = []
        self._lock: threading.RLock = threading.RLock()
        self._active_operations: dict[str, datetime] = {}

    @contextmanager
    def measure(self, operation: str, module: str, function: str, **tags: Any):
        """
        Context manager for measuring operation duration.

        Usage:
            with monitor.measure("snapshot_load", "storage", "load_snapshot", size_kb=1024):
                # operation to measure

        Args:
            operation: Name of operation being measured
            module: Module where operation occurs
            function: Function being measured
            **tags: Arbitrary tags for categorization
        """
        start_time = datetime.now(UTC)
        start_perf = time.perf_counter()
        error: str | None = None

        try:
            with self._lock:
                self._active_operations[operation] = start_time

            yield

            success = True

        except Exception as e:
            success = False
            error = f"{type(e).__name__}: {str(e)}"
            raise

        finally:
            end_time = datetime.now(UTC)
            end_perf = time.perf_counter()
            duration_ms = (end_perf - start_perf) * 1000

            event = PerformanceEvent(
                operation=operation,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                investigation_id=self.context.investigation_id,
                module=module,
                function=function,
                success=success,
                error=error,
                tags=tags,
            )

            with self._lock:
                self._events.append(event)
                self._active_operations.pop(operation, None)

    def record_event(
        self,
        operation: str,
        start_time: datetime,
        end_time: datetime,
        module: str,
        function: str,
        success: bool,
        error: str | None = None,
        **tags: Any,
    ) -> None:
        """
        Record a performance event manually.

        Use when context manager cannot be used.

        Args:
            operation: Name of operation
            start_time: When operation started (timezone-aware)
            end_time: When operation ended (timezone-aware)
            module: Module name
            function: Function name
            success: Whether operation succeeded
            error: Error message if failed
            **tags: Additional tags
        """
        if start_time.tzinfo is None:
            raise ValueError("start_time must be timezone-aware")
        if end_time.tzinfo is None:
            raise ValueError("end_time must be timezone-aware")

        duration_ms = (end_time - start_time).total_seconds() * 1000

        event = PerformanceEvent(
            operation=operation,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            investigation_id=self.context.investigation_id,
            module=module,
            function=function,
            success=success,
            error=error,
            tags=tags,
        )

        with self._lock:
            self._events.append(event)

    def get_events(
        self,
        operation: str | None = None,
        module: str | None = None,
        success: bool | None = None,
        limit: int = 1000,
    ) -> list[PerformanceEvent]:
        """
        Get performance events with optional filtering.

        Args:
            operation: Filter by operation name
            module: Filter by module name
            success: Filter by success status
            limit: Maximum number of events to return

        Returns:
            List of matching performance events (newest first)
        """
        with self._lock:
            events = self._events.copy()

        # Filter events
        filtered_events = []
        for event in reversed(events):  # Newest first
            if operation is not None and event.operation != operation:
                continue
            if module is not None and event.module != module:
                continue
            if success is not None and event.success != success:
                continue

            filtered_events.append(event)
            if len(filtered_events) >= limit:
                break

        return filtered_events

    def get_summary(self) -> dict[str, Any]:
        """
        Generate summary statistics for all recorded events.

        Returns:
            Dictionary with aggregate performance metrics
        """
        with self._lock:
            events = self._events.copy()

        if not events:
            return {
                "total_events": 0,
                "success_rate": 1.0,
                "operations": {},
                "warnings": ["No performance events recorded"],
            }

        # Group by operation
        operation_stats: dict[str, dict[str, Any]] = {}
        total_events = len(events)
        successful_events = sum(1 for e in events if e.success)

        for event in events:
            op = event.operation
            if op not in operation_stats:
                operation_stats[op] = {
                    "count": 0,
                    "success_count": 0,
                    "durations": [],
                    "modules": set(),
                    "last_event": event.start_time,
                }

            stats = operation_stats[op]
            stats["count"] += 1
            if event.success:
                stats["success_count"] += 1
            stats["durations"].append(event.duration_ms)
            stats["modules"].add(event.module)
            if event.start_time > stats["last_event"]:
                stats["last_event"] = event.start_time

        # Calculate statistics per operation
        for _op, stats in operation_stats.items():
            durations = stats["durations"]
            stats["avg_duration_ms"] = sum(durations) / len(durations)
            stats["min_duration_ms"] = min(durations)
            stats["max_duration_ms"] = max(durations)
            stats["success_rate"] = stats["success_count"] / stats["count"]
            stats["modules"] = list(stats["modules"])
            del stats["durations"]  # Remove raw data to save space

        return {
            "total_events": total_events,
            "success_rate": successful_events / total_events,
            "operations": operation_stats,
            "active_operations": list(self._active_operations.keys()),
            "investigation_id": self.context.investigation_id,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def save_to_disk(self, path: Path | None = None) -> Path:
        """
        Save performance events to disk for audit trail.

        Args:
            path: Optional custom path, defaults to investigation directory

        Returns:
            Path where events were saved
        """
        if path is None:
            inv_path = get_investigation_path(self.context.investigation_id)
            path = (
                inv_path
                / "performance"
                / f"events_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
            )

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        with self._lock:
            events_data = [e.to_dict() for e in self._events]
            summary = self.get_summary()

        data = {
            "events": events_data,
            "summary": summary,
            "metadata": {
                "investigation_id": self.context.investigation_id,
                "saved_at": datetime.now(UTC).isoformat(),
                "event_count": len(events_data),
            },
        }

        # Atomic write
        temp_path = path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        temp_path.rename(path)

        return path

    def clear(self) -> None:
        """Clear all performance events (use with caution)."""
        with self._lock:
            self._events.clear()
            self._active_operations.clear()


# Global performance monitor instance (thread-safe singleton pattern)
_PERFORMANCE_MONITOR: PerformanceMonitor | None = None
_MONITOR_LOCK: threading.RLock = threading.RLock()


def get_performance_monitor(
    context: RuntimeContext | None = None,
) -> PerformanceMonitor:
    """
    Get or create the global performance monitor.

    Args:
        context: Runtime context (required on first call)

    Returns:
        PerformanceMonitor instance

    Raises:
        ValueError: If context is None and monitor hasn't been initialized
    """
    global _PERFORMANCE_MONITOR

    with _MONITOR_LOCK:
        if _PERFORMANCE_MONITOR is None:
            if context is None:
                raise ValueError("RuntimeContext required for first initialization")
            _PERFORMANCE_MONITOR = PerformanceMonitor(context)

        return _PERFORMANCE_MONITOR


def monitor_performance(context: RuntimeContext | None = None) -> dict[str, Any]:
    """
    Main function for performance monitoring.

    Called from core/engine.py or bridge/coordination/scheduling.py.

    Args:
        context: Runtime context (optional, uses existing monitor if available)

    Returns:
        Structured performance report
    """
    try:
        monitor = get_performance_monitor(context)
        summary = monitor.get_summary()

        # Add honesty indicators (Article 8: Honest Performance)
        if "warnings" not in summary:
            summary["warnings"] = []

        # Check for slow operations
        for op, stats in summary.get("operations", {}).items():
            avg_ms = stats.get("avg_duration_ms", 0)
            if avg_ms > 1000:  # > 1 second
                summary["warnings"].append(
                    f"⚠️ Slow operation detected: {op} (avg {avg_ms:.0f}ms)"
                )

        return summary

    except Exception as e:
        # Graceful degradation (Article 14)
        return {
            "error": f"Performance monitoring failed: {type(e).__name__}: {str(e)}",
            "total_events": 0,
            "success_rate": 0.0,
            "operations": {},
            "warnings": ["Performance monitoring temporarily unavailable"],
            "generated_at": datetime.now(UTC).isoformat(),
        }


def measure_operation(operation: str, module: str, function: str, **tags: Any):
    """
    Decorator for measuring function performance.

    Usage:
        @measure_operation("snapshot_save", "storage", "save_snapshot")
        def save_snapshot(data):
            ...
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try to get context from args or create default
            context = None
            for arg in args:
                if isinstance(arg, RuntimeContext):
                    context = arg
                    break

            if context is None and "context" in kwargs:
                context = kwargs["context"]

            monitor = get_performance_monitor(context)

            with monitor.measure(operation, module, function, **tags):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Quick performance checks for critical paths
def check_critical_paths(context: RuntimeContext) -> list[dict[str, Any]]:
    """
    Check performance of known critical paths.

    Returns list of issues found with ⚠️ warnings.
    """
    monitor = get_performance_monitor(context)
    events = monitor.get_events(limit=50)

    issues = []
    threshold_ms = {
        "snapshot_load": 500,
        "snapshot_save": 1000,
        "observation_scan": 2000,
        "query_execute": 1000,
    }

    for event in events:
        if not event.success:
            issues.append(
                {
                    "severity": "error",
                    "operation": event.operation,
                    "message": f"Operation failed: {event.error}",
                    "duration_ms": event.duration_ms,
                }
            )
            continue

        threshold = threshold_ms.get(event.operation)
        if threshold and event.duration_ms > threshold:
            issues.append(
                {
                    "severity": "warning",
                    "operation": event.operation,
                    "message": f"⚠️ Slow: {event.duration_ms:.0f}ms (threshold: {threshold}ms)",
                    "duration_ms": event.duration_ms,
                }
            )

    return issues


# Test function for module validation
def test_performance_monitoring() -> dict[str, Any]:
    """
    Test the performance monitoring system.

    Returns:
        Test results with pass/fail status
    """
    from core.context import RuntimeContext

    # Create test context
    test_context = RuntimeContext(
        investigation_id="test_performance",
        root_path=Path.cwd(),
        config={},
        started_at=datetime.now(UTC),
    )

    results = {
        "module": "integrity.monitoring.performance",
        "tests_passed": 0,
        "tests_failed": 0,
        "details": [],
    }

    try:
        # Test 1: Monitor creation
        monitor = PerformanceMonitor(test_context)
        assert monitor.context.investigation_id == "test_performance"
        results["tests_passed"] += 1
        results["details"].append("Test 1: Monitor creation ✓")

        # Test 2: Context manager measurement
        with monitor.measure("test_op", "test", "test_function", test=True):
            time.sleep(0.01)  # 10ms

        events = monitor.get_events()
        assert len(events) == 1
        assert events[0].operation == "test_op"
        assert events[0].success
        assert events[0].duration_ms > 5  # Should be at least 5ms

        results["tests_passed"] += 1
        results["details"].append("Test 2: Context manager measurement ✓")

        # Test 3: Manual event recording
        start = datetime.now(UTC)
        time.sleep(0.005)
        end = datetime.now(UTC)

        monitor.record_event(
            operation="manual_op",
            start_time=start,
            end_time=end,
            module="test",
            function="manual",
            success=True,
            custom_tag="test",
        )

        events = monitor.get_events()
        assert len(events) == 2

        results["tests_passed"] += 1
        results["details"].append("Test 3: Manual event recording ✓")

        # Test 4: Summary generation
        summary = monitor.get_summary()
        assert "total_events" in summary
        assert summary["total_events"] == 2
        assert "test_op" in summary["operations"]

        results["tests_passed"] += 1
        results["details"].append("Test 4: Summary generation ✓")

        # Test 5: Global monitor access
        global_monitor = get_performance_monitor(test_context)
        assert global_monitor is monitor  # Should return same instance

        results["tests_passed"] += 1
        results["details"].append("Test 5: Global monitor access ✓")

        # Test 6: Error handling in context manager
        try:
            with monitor.measure("error_op", "test", "error_func"):
                raise ValueError("Test error")
        except ValueError:
            pass

        error_events = monitor.get_events(operation="error_op")
        assert len(error_events) == 1
        assert not error_events[0].success
        assert "ValueError" in str(error_events[0].error)

        results["tests_passed"] += 1
        results["details"].append("Test 6: Error handling ✓")

        # Test 7: Thread safety (simplified)
        import concurrent.futures

        def worker():
            with monitor.measure("concurrent_op", "test", "worker"):
                time.sleep(0.001)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker) for _ in range(10)]
            concurrent.futures.wait(futures)

        concurrent_events = monitor.get_events(operation="concurrent_op")
        assert len(concurrent_events) >= 10

        results["tests_passed"] += 1
        results["details"].append("Test 7: Thread safety ✓")

        # Clean up
        monitor.clear()

    except Exception as e:
        results["tests_failed"] += 1
        results["details"].append(f"Test failed: {type(e).__name__}: {str(e)}")

    return results


# Export public API
__all__ = [
    "PerformanceMonitor",
    "PerformanceEvent",
    "get_performance_monitor",
    "monitor_performance",
    "measure_operation",
    "check_critical_paths",
    "test_performance_monitoring",
]
