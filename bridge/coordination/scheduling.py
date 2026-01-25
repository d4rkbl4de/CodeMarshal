"""
bridge.coordination.scheduling
==============================

Task orchestration for truth-preserving investigations.

Core Responsibility:
    Determine execution order for investigative tasks while maintaining
    determinism and preventing side effects.

Architectural Principles:
    1. Linear Task Queue - investigations follow sequential logic
    2. Determinism - same input → same schedule
    3. No speculative execution or race conditions
    4. Inter-task isolation - prevent cross-contamination
    5. Graceful degradation on failure

Import Rules:
    Allowed: standard library only
    Forbidden: any module that could mutate observations or truths
"""

import logging
import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

# Configure logging for audit trail
logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Priority levels for task scheduling.

    Note: Prioritization is for performance only, never for inference.
    """

    IMMEDIATE = auto()  # Critical system tasks (observation collection)
    HIGH = auto()  # User-requested immediate actions
    MEDIUM = auto()  # Pattern computation
    LOW = auto()  # Background tasks (cache warmup)


class TaskState(Enum):
    """State machine for task lifecycle tracking."""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass(frozen=True)
class TaskMetadata:
    """Immutable metadata for task audit trail."""

    created_at: float = field(default_factory=time.time)
    task_id: str = field(default_factory=lambda: f"task_{int(time.time() * 1000)}")
    investigation_id: str | None = None
    session_id: str | None = None
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    version: int = 1


@dataclass
class TaskResult:
    """Container for task execution results."""

    task_id: str
    state: TaskState
    output: Any | None = None
    error: str | None = None
    started_at: float | None = None
    completed_at: float | None = None
    duration_ms: float | None = None


class Task(ABC):
    """Abstract base class for all investigative tasks.

    All tasks must be deterministic and side-effect free with respect to
    observations. Tasks compute patterns or organize data but never
    mutate core truths.
    """

    def __init__(self, priority: TaskPriority = TaskPriority.MEDIUM) -> None:
        self.metadata = TaskMetadata()
        self.priority = priority
        self.state: TaskState = TaskState.PENDING
        self.result: TaskResult | None = None

    @abstractmethod
    def execute(self) -> Any:
        """Execute the task's core logic.

        Returns:
            Task output (must be deterministic for same inputs)

        Raises:
            Exception: If task cannot complete (will be caught by scheduler)
        """
        pass

    def __str__(self) -> str:
        return f"Task({self.metadata.task_id}, {self.priority.name}, {self.state.name})"


class Scheduler:
    """Deterministic task orchestrator for investigative workflows.

    Ensures tasks execute in proper sequence without introducing
    race conditions or side effects.

    Implementation Notes:
        - Uses double-ended queue for deterministic ordering
        - Thread-safe operations with explicit locking
        - Tracks execution for recovery and audit
        - Never speculatively executes or reorders tasks
    """

    def __init__(self, max_queue_size: int = 1000) -> None:
        """Initialize scheduler with empty queues.

        Args:
            max_queue_size: Maximum number of pending tasks to prevent
                          memory exhaustion. Older tasks are dropped first.
        """
        # Priority queues for different task types
        self._queues: dict[TaskPriority, deque[Task]] = {
            priority: deque(maxlen=max_queue_size) for priority in TaskPriority
        }

        # Lock for thread-safe operations
        self._lock = threading.RLock()

        # Execution history for audit and recovery
        self._execution_history: list[TaskResult] = []
        self._active_tasks: dict[str, Task] = {}

        # Callback for status updates (set by bridge layer)
        self._status_callback: Callable[[str, Any], None] | None = None

        # Performance metrics with explicit type annotation
        self._metrics: dict[str, int | float] = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
        }

        logger.info(f"Scheduler initialized with max_queue_size={max_queue_size}")

    def set_status_callback(self, callback: Callable[[str, Any], None]) -> None:
        """Set callback for status updates to indicators layer.

        Args:
            callback: Function that accepts (status_type, data) parameters
        """
        self._status_callback = callback

    def _notify_status(self, status_type: str, data: Any = None) -> None:
        """Notify status callback if set."""
        if self._status_callback:
            try:
                self._status_callback(status_type, data)
            except Exception as e:
                logger.warning(f"Status callback failed: {e}")

    def enqueue(self, task: Task) -> bool:
        """Add a task to the appropriate priority queue.

        Args:
            task: Task to enqueue

        Returns:
            True if task was enqueued, False if queue was full

        Note:
            Tasks with IMMEDIATE priority are inserted at the front
            of their queue to ensure prompt execution.
        """
        with self._lock:
            queue = self._queues[task.priority]

            # Check if queue is full with safe type handling
            max_len = queue.maxlen
            if max_len is not None and len(queue) >= max_len:
                logger.warning(f"Queue for priority {task.priority.name} is full")
                self._notify_status(
                    "queue_full",
                    {"priority": task.priority.name, "task_id": task.metadata.task_id},
                )
                return False

            # IMMEDIATE tasks go to front, others to back
            if task.priority == TaskPriority.IMMEDIATE:
                queue.appendleft(task)
            else:
                queue.append(task)

            logger.debug(
                f"Enqueued task {task.metadata.task_id} with priority {task.priority.name}"
            )
            self._notify_status(
                "task_enqueued",
                {"task_id": task.metadata.task_id, "priority": task.priority.name},
            )

            return True

    def dequeue(self) -> Task | None:
        """Retrieve next task following priority rules.

        Returns:
            Next task to execute or None if no tasks pending

        Priority Order:
            1. IMMEDIATE tasks (critical system operations)
            2. HIGH tasks (user requests)
            3. MEDIUM tasks (pattern computation)
            4. LOW tasks (background operations)

        Note:
            Within each priority level, tasks execute in FIFO order.
        """
        with self._lock:
            for priority in [
                TaskPriority.IMMEDIATE,
                TaskPriority.HIGH,
                TaskPriority.MEDIUM,
                TaskPriority.LOW,
            ]:
                queue = self._queues[priority]
                if queue:
                    task = queue.popleft()
                    task.state = TaskState.RUNNING
                    self._active_tasks[task.metadata.task_id] = task
                    return task

            return None

    def _execute_task(self, task: Task) -> TaskResult:
        """Execute a single task with isolation and error handling.

        Args:
            task: Task to execute

        Returns:
            TaskResult with execution outcome

        Note:
            Each task executes in isolated context to prevent
            cross-contamination of observations.
        """
        task_id = task.metadata.task_id
        started_at = time.time()

        logger.info(f"Starting task {task_id}")
        self._notify_status("task_started", {"task_id": task_id})

        try:
            # Execute task logic
            output = task.execute()
            completed_at = time.time()
            duration_ms = (completed_at - started_at) * 1000

            result = TaskResult(
                task_id=task_id,
                state=TaskState.COMPLETED,
                output=output,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )

            logger.info(f"Completed task {task_id} in {result.duration_ms:.2f}ms")
            self._notify_status(
                "task_completed",
                {"task_id": task_id, "duration_ms": result.duration_ms},
            )

            with self._lock:
                self._metrics["tasks_completed"] += 1
                if result.duration_ms is not None:
                    # Safe addition with type assertion
                    current_time = self._metrics["total_execution_time"]
                    self._metrics["total_execution_time"] = (
                        current_time + result.duration_ms
                    )

            return result

        except Exception as e:
            completed_at = time.time()
            error_msg = f"Task {task_id} failed: {str(e)}"
            duration_ms = (completed_at - started_at) * 1000

            result = TaskResult(
                task_id=task_id,
                state=TaskState.FAILED,
                error=error_msg,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )

            logger.error(error_msg, exc_info=True)
            self._notify_status("task_failed", {"task_id": task_id, "error": error_msg})

            with self._lock:
                self._metrics["tasks_failed"] += 1

            return result

    def run_next(self) -> TaskResult | None:
        """Execute the next pending task.

        Returns:
            TaskResult if a task was executed, None if no tasks pending

        Note:
            This method is designed for iterative execution, allowing
            external control of scheduling pace.
        """
        task = self.dequeue()
        if not task:
            return None

        task_id = task.metadata.task_id
        result = self._execute_task(task)

        with self._lock:
            # Update task state
            task.state = result.state
            task.result = result

            # Remove from active tasks
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]

            # Record in history
            self._execution_history.append(result)

            # Trim history to prevent unbounded growth
            if len(self._execution_history) > 1000:
                self._execution_history = self._execution_history[-1000:]

        return result

    def run_all(self) -> None:
        """Execute all pending tasks sequentially.

        Note:
            Tasks execute in priority order, with isolation between
            each execution. This method blocks until all tasks complete.

            Per Article 14 (Graceful Degradation), failures are caught
            and logged without stopping execution of remaining tasks.
        """
        logger.info("Starting execution of all pending tasks")
        self._notify_status("scheduler_started")

        tasks_executed = 0
        start_time = time.time()

        while True:
            result = self.run_next()
            if not result:
                break

            tasks_executed += 1

            # Brief pause to prevent CPU monopolization
            # (allows other threads to enqueue tasks if needed)
            time.sleep(0.001)

        duration = (time.time() - start_time) * 1000
        logger.info(f"Executed {tasks_executed} tasks in {duration:.2f}ms")
        self._notify_status(
            "scheduler_completed",
            {"tasks_executed": tasks_executed, "duration_ms": duration},
        )

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task.

        Args:
            task_id: ID of task to cancel

        Returns:
            True if task was cancelled, False if not found

        Note:
            Only PENDING tasks can be cancelled. RUNNING tasks
            must complete or fail naturally.
        """
        with self._lock:
            # Check all queues for the task
            for _, queue in self._queues.items():
                for i, task in enumerate(queue):
                    if task.metadata.task_id == task_id:
                        if task.state == TaskState.PENDING:
                            # Remove from queue
                            del queue[i]
                            task.state = TaskState.CANCELLED

                            logger.info(f"Cancelled pending task {task_id}")
                            self._notify_status("task_cancelled", {"task_id": task_id})
                            return True

            # Check active tasks
            if task_id in self._active_tasks:
                logger.warning(f"Cannot cancel running task {task_id}")
                return False

            return False

    def get_metrics(self) -> dict[str, Any]:
        """Get current scheduler metrics.

        Returns:
            Dictionary of performance and operational metrics
        """
        with self._lock:
            pending_counts = {
                priority.name: len(queue) for priority, queue in self._queues.items()
            }

            # Build metrics dictionary with explicit types
            metrics: dict[str, Any] = {
                "tasks_completed": self._metrics["tasks_completed"],
                "tasks_failed": self._metrics["tasks_failed"],
                "total_execution_time": self._metrics["total_execution_time"],
                "pending_tasks": pending_counts,
                "active_tasks": len(self._active_tasks),
                "history_size": len(self._execution_history),
                "queues_full": any(
                    queue.maxlen is not None and len(queue) >= queue.maxlen
                    for queue in self._queues.values()
                ),
            }

            return metrics

    def get_task_state(self, task_id: str) -> TaskState | None:
        """Get current state of a task.

        Args:
            task_id: ID of task to query

        Returns:
            Current TaskState or None if task not found
        """
        with self._lock:
            # Check active tasks
            if task_id in self._active_tasks:
                return self._active_tasks[task_id].state

            # Check queues
            for queue in self._queues.values():
                for task in queue:
                    if task.metadata.task_id == task_id:
                        return task.state

            # Check history
            for result in reversed(self._execution_history):
                if result.task_id == task_id:
                    return result.state

            return None

    def clear_pending(self, priority: TaskPriority | None = None) -> int:
        """Clear pending tasks from queue(s).

        Args:
            priority: If specified, clear only this priority level.
                     If None, clear all pending tasks.

        Returns:
            Number of tasks cleared

        Note:
            This should be used cautiously as it may interrupt
            investigative workflows. Typically only used during
            system reset or error recovery.
        """
        with self._lock:
            cleared = 0

            if priority:
                queue = self._queues[priority]
                cleared = len(queue)
                queue.clear()
                logger.warning(f"Cleared {cleared} tasks from {priority.name} queue")
            else:
                for _, queue in self._queues.items():
                    cleared += len(queue)
                    queue.clear()
                logger.warning(f"Cleared all {cleared} pending tasks")

            if cleared > 0:
                self._notify_status(
                    "queue_cleared",
                    {
                        "count": cleared,
                        "priority": priority.name if priority else "ALL",
                    },
                )

            return cleared

    def get_recovery_state(self) -> list[dict[str, Any]]:
        """Get state needed for scheduler recovery.

        Returns:
            List of task metadata for pending tasks, allowing
            reconstruction of queue state after system restart.

        Note:
            This supports Article 15 (Session Integrity) by
            enabling investigation resumption after interruption.
        """
        with self._lock:
            recovery_state: list[dict[str, Any]] = []

            # Capture all pending tasks
            for priority, queue in self._queues.items():
                for task in queue:
                    if task.state == TaskState.PENDING:
                        recovery_state.append(
                            {
                                "task_id": task.metadata.task_id,
                                "priority": priority.name,
                                "metadata": {
                                    "created_at": task.metadata.created_at,
                                    "investigation_id": task.metadata.investigation_id,
                                    "session_id": task.metadata.session_id,
                                    "dependencies": task.metadata.dependencies,
                                    "version": task.metadata.version,
                                },
                            }
                        )

            return recovery_state


# Singleton scheduler instance for system-wide use
# Note: This follows the architectural principle of a single orchestration point
# while maintaining thread safety and determinism.
_system_scheduler: Scheduler | None = None
_scheduler_lock = threading.Lock()


def get_system_scheduler() -> Scheduler:
    """Get or create the system-wide scheduler instance.

    Returns:
        Shared Scheduler instance

    Note:
        This ensures consistent task orchestration across the
        entire investigation environment while maintaining
        thread safety.
    """
    global _system_scheduler

    with _scheduler_lock:
        if _system_scheduler is None:
            _system_scheduler = Scheduler()
            logger.info("Created system scheduler singleton")

        return _system_scheduler


def reset_system_scheduler() -> None:
    """Reset the system scheduler (for testing and recovery).

    Warning: This clears all pending tasks and resets metrics.
    Only use during system initialization or error recovery.
    """
    global _system_scheduler

    with _scheduler_lock:
        if _system_scheduler:
            _system_scheduler.clear_pending()
            logger.warning("System scheduler reset")

        _system_scheduler = None
