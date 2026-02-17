"""
watcher.py - Real-time file system watcher for CodeMarshal.

Purpose:
    Monitor file system changes (additions, modifications, deletions) in real-time
    and trigger investigation updates.

Constitutional Basis:
    - Article 1: Observation Purity (only reports actual changes)
    - Article 13: Deterministic Operation (consistent change detection)
    - Article 15: Checkpoints (each change is a checkpoint)

Architecture:
    - Uses watchdog library for cross-platform file system events
    - Debounces rapid changes to avoid noise
    - Supports recursive directory watching
    - Configurable ignore patterns
"""

from __future__ import annotations

import hashlib
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable

# Try to import watchdog for file system monitoring
try:
    from watchdog.events import (
        DirCreatedEvent,
        DirDeletedEvent,
        DirModifiedEvent,
        DirMovedEvent,
        FileCreatedEvent,
        FileDeletedEvent,
        FileModifiedEvent,
        FileMovedEvent,
        FileSystemEvent,
        FileSystemEventHandler,
    )
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    FileSystemEventHandler = object


class ChangeType(Enum):
    """Type of file system change."""

    CREATED = auto()
    MODIFIED = auto()
    DELETED = auto()
    MOVED = auto()


@dataclass(frozen=True)
class FileChange:
    """Immutable record of a file system change."""

    path: Path
    change_type: ChangeType
    timestamp: datetime
    is_directory: bool = False
    old_path: Path | None = None  # For moved files
    file_hash: str | None = None  # For modified files

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": str(self.path),
            "change_type": self.change_type.name,
            "timestamp": self.timestamp.isoformat(),
            "is_directory": self.is_directory,
            "old_path": str(self.old_path) if self.old_path else None,
            "file_hash": self.file_hash,
        }


@dataclass
class WatcherConfig:
    """Configuration for file system watcher."""

    recursive: bool = True
    watch_depth: int | None = None  # None = unlimited
    ignore_patterns: list[str] = field(default_factory=list)
    debounce_seconds: float = 0.5
    follow_symlinks: bool = False

    def __post_init__(self):
        # Default ignore patterns
        if not self.ignore_patterns:
            self.ignore_patterns = [
                "*.pyc",
                "__pycache__",
                ".git",
                ".venv",
                "venv",
                "node_modules",
                ".idea",
                ".vscode",
                "*.tmp",
                "*.swp",
                "*.swo",
                ".DS_Store",
                "Thumbs.db",
            ]


class FileSystemWatcher(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    """
    Real-time file system watcher with debouncing and change tracking.

    Features:
    - Cross-platform file system monitoring
    - Debounced change events
    - Recursive directory watching
    - Ignore pattern support
    - Thread-safe change queue
    """

    def __init__(
        self,
        watch_path: Path,
        config: WatcherConfig | None = None,
        on_change: Callable[[FileChange], None] | None = None,
    ):
        """
        Initialize file system watcher.

        Args:
            watch_path: Directory to watch
            config: Watcher configuration
            on_change: Callback for change events
        """
        if not WATCHDOG_AVAILABLE:
            raise ImportError(
                "watchdog library required for file system watching. "
                "Install with: pip install watchdog"
            )

        self.watch_path = Path(watch_path).resolve()
        self.config = config or WatcherConfig()
        self.on_change = on_change

        # Thread-safe change tracking
        self._changes: list[FileChange] = []
        self._changes_lock = threading.Lock()

        # Debouncing
        self._pending_changes: dict[Path, FileChange] = {}
        self._pending_lock = threading.Lock()
        self._debounce_timer: threading.Timer | None = None

        # Watchdog observer
        self._observer: Observer | None = None
        self._running = False

    def start(self) -> None:
        """Start watching the file system."""
        if self._running:
            return

        self._observer = Observer()
        self._observer.schedule(
            self, str(self.watch_path), recursive=self.config.recursive
        )
        self._observer.start()
        self._running = True

    def stop(self) -> None:
        """Stop watching the file system."""
        if not self._running:
            return

        self._running = False

        if self._debounce_timer:
            self._debounce_timer.cancel()

        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None

    def get_changes(self, since: datetime | None = None) -> list[FileChange]:
        """
        Get recorded changes.

        Args:
            since: Only return changes after this timestamp

        Returns:
            List of file changes
        """
        with self._changes_lock:
            changes = self._changes.copy()

        if since:
            changes = [c for c in changes if c.timestamp > since]

        return changes

    def clear_changes(self) -> None:
        """Clear recorded changes."""
        with self._changes_lock:
            self._changes.clear()

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file/directory creation."""
        if self._should_ignore(event.src_path):
            return

        change = FileChange(
            path=Path(event.src_path),
            change_type=ChangeType.CREATED,
            timestamp=datetime.now(UTC),
            is_directory=event.is_directory,
        )
        self._queue_change(change)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file/directory modification."""
        if self._should_ignore(event.src_path):
            return

        # Calculate file hash for content verification
        file_hash = None
        if not event.is_directory:
            try:
                file_hash = self._calculate_file_hash(event.src_path)
            except (OSError, IOError):
                pass

        change = FileChange(
            path=Path(event.src_path),
            change_type=ChangeType.MODIFIED,
            timestamp=datetime.now(UTC),
            is_directory=event.is_directory,
            file_hash=file_hash,
        )
        self._queue_change(change)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file/directory deletion."""
        if self._should_ignore(event.src_path):
            return

        change = FileChange(
            path=Path(event.src_path),
            change_type=ChangeType.DELETED,
            timestamp=datetime.now(UTC),
            is_directory=event.is_directory,
        )
        self._queue_change(change)

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file/directory move/rename."""
        if self._should_ignore(event.src_path):
            return

        change = FileChange(
            path=Path(event.dest_path),
            change_type=ChangeType.MOVED,
            timestamp=datetime.now(UTC),
            is_directory=event.is_directory,
            old_path=Path(event.src_path),
        )
        self._queue_change(change)

    def _should_ignore(self, path: str) -> bool:
        """Check if path should be ignored based on patterns."""
        path_str = str(path)
        path_obj = Path(path)

        # Check depth if configured
        if self.config.watch_depth is not None:
            try:
                rel_parts = path_obj.relative_to(self.watch_path).parts
                if len(rel_parts) > self.config.watch_depth:
                    return True
            except ValueError:
                pass

        # Check ignore patterns
        for pattern in self.config.ignore_patterns:
            if pattern in path_str:
                return True
            if path_obj.match(pattern):
                return True

        return False

    def _queue_change(self, change: FileChange) -> None:
        """Queue a change with debouncing."""
        with self._pending_lock:
            self._pending_changes[change.path] = change

        # Reset debounce timer
        if self._debounce_timer:
            self._debounce_timer.cancel()

        self._debounce_timer = threading.Timer(
            self.config.debounce_seconds, self._flush_pending_changes
        )
        self._debounce_timer.start()

    def _flush_pending_changes(self) -> None:
        """Flush pending changes to the main change list."""
        with self._pending_lock:
            changes = list(self._pending_changes.values())
            self._pending_changes.clear()

        with self._changes_lock:
            self._changes.extend(changes)

        # Call change handler if provided
        if self.on_change:
            for change in changes:
                try:
                    self.on_change(change)
                except Exception:
                    # Don't let callback errors break the watcher
                    pass

    def _calculate_file_hash(self, filepath: str) -> str | None:
        """Calculate hash of file contents."""
        try:
            sha256 = hashlib.sha256()
            with open(filepath, "rb") as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except (OSError, IOError):
            return None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def create_watcher(
    watch_path: Path,
    recursive: bool = True,
    ignore_patterns: list[str] | None = None,
    on_change: Callable[[FileChange], None] | None = None,
) -> FileSystemWatcher:
    """
    Create and start a file system watcher.

    Args:
        watch_path: Directory to watch
        recursive: Watch subdirectories
        ignore_patterns: List of patterns to ignore
        on_change: Callback for change events

    Returns:
        Started FileSystemWatcher instance

    Example:
        >>> with create_watcher(Path("./src")) as watcher:
        ...     time.sleep(10)  # Watch for 10 seconds
        ...     changes = watcher.get_changes()
        ...     print(f"Detected {len(changes)} changes")
    """
    config = WatcherConfig(
        recursive=recursive,
        ignore_patterns=ignore_patterns or [],
    )
    watcher = FileSystemWatcher(watch_path, config, on_change)
    watcher.start()
    return watcher
