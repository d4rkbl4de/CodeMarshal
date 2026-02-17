"""
change_storage.py - Change tracking storage for real-time investigations.

Purpose:
    Store and manage file system changes, diff history, and incremental
    investigation data.

Constitutional Basis:
    - Article 9: Immutable Observations (change records are immutable)
    - Article 15: Checkpoints (each change is a checkpoint)
    - Article 18: Explicit Limitations (storage limitations declared)

Features:
    - Store file system changes with timestamps
    - Track diff history
    - Support incremental queries
    - Change context awareness
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ChangeRecord:
    """Immutable record of a file system change."""

    path: str
    change_type: str
    timestamp: datetime
    is_directory: bool = False
    old_path: str | None = None
    file_hash: str | None = None
    investigation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": self.path,
            "change_type": self.change_type,
            "timestamp": self.timestamp.isoformat(),
            "is_directory": self.is_directory,
            "old_path": self.old_path,
            "file_hash": self.file_hash,
            "investigation_id": self.investigation_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChangeRecord":
        """Create from dictionary."""
        return cls(
            path=data["path"],
            change_type=data["change_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            is_directory=data.get("is_directory", False),
            old_path=data.get("old_path"),
            file_hash=data.get("file_hash"),
            investigation_id=data.get("investigation_id"),
        )


@dataclass
class InvestigationSnapshot:
    """Snapshot of investigation state at a point in time."""

    investigation_id: str
    timestamp: datetime
    path: str
    file_count: int
    changes_since_last: list[ChangeRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "investigation_id": self.investigation_id,
            "timestamp": self.timestamp.isoformat(),
            "path": self.path,
            "file_count": self.file_count,
            "changes_since_last": [c.to_dict() for c in self.changes_since_last],
            "metadata": self.metadata,
        }


class ChangeTrackingStorage:
    """
    Storage for file system changes and investigation snapshots.

    Features:
    - Persistent storage of change records
    - Investigation snapshots
    - Incremental query support
    - Change context awareness
    """

    def __init__(self, storage_dir: Path | str | None = None):
        """
        Initialize change tracking storage.

        Args:
            storage_dir: Directory for change storage (default: storage/changes)
        """
        if storage_dir is None:
            storage_dir = Path("storage/changes")

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self._change_cache: list[ChangeRecord] = []
        self._max_cache_size = 1000

    def record_change(
        self,
        path: Path | str,
        change_type: str,
        is_directory: bool = False,
        old_path: Path | str | None = None,
        file_hash: str | None = None,
        investigation_id: str | None = None,
    ) -> ChangeRecord:
        """
        Record a file system change.

        Args:
            path: Path that changed
            change_type: Type of change (created, modified, deleted, moved)
            is_directory: Whether the path is a directory
            old_path: Previous path (for moved files)
            file_hash: Hash of file content
            investigation_id: Associated investigation ID

        Returns:
            The created ChangeRecord
        """
        record = ChangeRecord(
            path=str(path),
            change_type=change_type,
            timestamp=datetime.now(UTC),
            is_directory=is_directory,
            old_path=str(old_path) if old_path else None,
            file_hash=file_hash,
            investigation_id=investigation_id,
        )

        # Add to cache
        self._change_cache.append(record)

        # Trim cache if needed
        if len(self._change_cache) > self._max_cache_size:
            self._persist_cache()
            self._change_cache = self._change_cache[-self._max_cache_size // 2 :]

        # Persist immediately if important
        if change_type in ("deleted", "moved"):
            self._persist_change(record)

        return record

    def record_changes(
        self,
        changes: list[tuple],
        investigation_id: str | None = None,
    ) -> list[ChangeRecord]:
        """
        Record multiple changes at once.

        Args:
            changes: List of (path, change_type, ...) tuples
            investigation_id: Associated investigation ID

        Returns:
            List of created ChangeRecords
        """
        records = []
        for change_data in changes:
            path = change_data[0]
            change_type = change_data[1]
            is_directory = change_data[2] if len(change_data) > 2 else False
            old_path = change_data[3] if len(change_data) > 3 else None
            file_hash = change_data[4] if len(change_data) > 4 else None

            record = self.record_change(
                path=path,
                change_type=change_type,
                is_directory=is_directory,
                old_path=old_path,
                file_hash=file_hash,
                investigation_id=investigation_id,
            )
            records.append(record)

        return records

    def get_changes(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
        path_filter: str | None = None,
        change_type: str | None = None,
        investigation_id: str | None = None,
        limit: int = 100,
    ) -> list[ChangeRecord]:
        """
        Query change records with filters.

        Args:
            since: Only changes after this time
            until: Only changes before this time
            path_filter: Filter by path substring
            change_type: Filter by change type
            investigation_id: Filter by investigation
            limit: Maximum results

        Returns:
            List of matching ChangeRecords
        """
        changes = []

        # Include cached changes
        changes.extend(self._change_cache)

        # Load persisted changes if needed
        if len(changes) < limit:
            persisted = self._load_persisted_changes(
                since=since,
                until=until,
                path_filter=path_filter,
                change_type=change_type,
                investigation_id=investigation_id,
            )
            changes.extend(persisted)

        # Apply filters
        if since:
            changes = [c for c in changes if c.timestamp >= since]
        if until:
            changes = [c for c in changes if c.timestamp <= until]
        if path_filter:
            changes = [c for c in changes if path_filter in c.path]
        if change_type:
            changes = [c for c in changes if c.change_type == change_type]
        if investigation_id:
            changes = [c for c in changes if c.investigation_id == investigation_id]

        # Sort by timestamp (newest first)
        changes.sort(key=lambda c: c.timestamp, reverse=True)

        return changes[:limit]

    def create_snapshot(
        self,
        investigation_id: str,
        path: Path | str,
        file_count: int,
        metadata: dict[str, Any] | None = None,
    ) -> InvestigationSnapshot:
        """
        Create an investigation snapshot.

        Args:
            investigation_id: Investigation identifier
            path: Investigation path
            file_count: Number of files
            metadata: Additional metadata

        Returns:
            Created InvestigationSnapshot
        """
        # Get changes since last snapshot
        last_snapshot = self._get_last_snapshot(investigation_id)
        since = last_snapshot.timestamp if last_snapshot else None

        changes = self.get_changes(
            since=since,
            investigation_id=investigation_id,
            limit=1000,
        )

        snapshot = InvestigationSnapshot(
            investigation_id=investigation_id,
            timestamp=datetime.now(UTC),
            path=str(path),
            file_count=file_count,
            changes_since_last=changes,
            metadata=metadata or {},
        )

        self._persist_snapshot(snapshot)
        return snapshot

    def get_snapshot_history(
        self,
        investigation_id: str,
        limit: int = 10,
    ) -> list[InvestigationSnapshot]:
        """
        Get snapshot history for an investigation.

        Args:
            investigation_id: Investigation identifier
            limit: Maximum snapshots

        Returns:
            List of InvestigationSnapshots
        """
        snapshot_dir = self.storage_dir / "snapshots" / investigation_id
        if not snapshot_dir.exists():
            return []

        snapshots = []
        for file_path in sorted(snapshot_dir.glob("*.json"), reverse=True):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    snapshot = InvestigationSnapshot(
                        investigation_id=data["investigation_id"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        path=data["path"],
                        file_count=data["file_count"],
                        changes_since_last=[
                            ChangeRecord.from_dict(c)
                            for c in data.get("changes_since_last", [])
                        ],
                        metadata=data.get("metadata", {}),
                    )
                    snapshots.append(snapshot)
            except (OSError, json.JSONDecodeError):
                continue

        return snapshots[:limit]

    def get_change_summary(
        self,
        investigation_id: str | None = None,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get summary of changes.

        Args:
            investigation_id: Filter by investigation
            since: Only changes after this time

        Returns:
            Summary dictionary
        """
        changes = self.get_changes(
            investigation_id=investigation_id,
            since=since,
            limit=10000,
        )

        total = len(changes)
        by_type: dict[str, int] = {}
        by_directory: dict[str, int] = {}

        for change in changes:
            # Count by type
            by_type[change.change_type] = by_type.get(change.change_type, 0) + 1

            # Count by directory
            path_obj = Path(change.path)
            parent = str(path_obj.parent)
            by_directory[parent] = by_directory.get(parent, 0) + 1

        return {
            "total_changes": total,
            "by_type": by_type,
            "by_directory": by_directory,
            "time_range": {
                "start": changes[-1].timestamp.isoformat() if changes else None,
                "end": changes[0].timestamp.isoformat() if changes else None,
            },
        }

    def clear_cache(self) -> None:
        """Persist cache and clear it."""
        self._persist_cache()
        self._change_cache.clear()

    def _persist_change(self, record: ChangeRecord) -> None:
        """Persist a single change to disk."""
        change_file = (
            self.storage_dir / "changes" / f"{record.timestamp.timestamp()}.json"
        )
        change_file.parent.mkdir(parents=True, exist_ok=True)

        with open(change_file, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2)

    def _persist_cache(self) -> None:
        """Persist all cached changes."""
        if not self._change_cache:
            return

        # Group by date
        by_date: dict[str, list[ChangeRecord]] = {}
        for record in self._change_cache:
            date_str = record.timestamp.strftime("%Y-%m-%d")
            by_date.setdefault(date_str, []).append(record)

        # Write to daily files
        for date_str, records in by_date.items():
            change_file = self.storage_dir / "changes" / f"{date_str}.json"
            change_file.parent.mkdir(parents=True, exist_ok=True)

            existing = []
            if change_file.exists():
                try:
                    with open(change_file, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                except (OSError, json.JSONDecodeError):
                    pass

            existing.extend([r.to_dict() for r in records])

            with open(change_file, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)

    def _load_persisted_changes(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
        path_filter: str | None = None,
        change_type: str | None = None,
        investigation_id: str | None = None,
    ) -> list[ChangeRecord]:
        """Load persisted changes from disk."""
        changes_dir = self.storage_dir / "changes"
        if not changes_dir.exists():
            return []

        records = []

        for change_file in changes_dir.glob("*.json"):
            try:
                with open(change_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list):
                    for item in data:
                        record = ChangeRecord.from_dict(item)
                        records.append(record)
                else:
                    record = ChangeRecord.from_dict(data)
                    records.append(record)
            except (OSError, json.JSONDecodeError):
                continue

        return records

    def _persist_snapshot(self, snapshot: InvestigationSnapshot) -> None:
        """Persist an investigation snapshot."""
        snapshot_dir = self.storage_dir / "snapshots" / snapshot.investigation_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = snapshot.timestamp.strftime("%Y%m%d_%H%M%S")
        snapshot_file = snapshot_dir / f"{timestamp_str}.json"

        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(snapshot.to_dict(), f, indent=2)

    def _get_last_snapshot(
        self,
        investigation_id: str,
    ) -> InvestigationSnapshot | None:
        """Get the most recent snapshot for an investigation."""
        snapshots = self.get_snapshot_history(investigation_id, limit=1)
        return snapshots[0] if snapshots else None


def create_change_storage(
    storage_dir: Path | str | None = None,
) -> ChangeTrackingStorage:
    """
    Create a change tracking storage instance.

    Args:
        storage_dir: Directory for storage

    Returns:
        ChangeTrackingStorage instance
    """
    return ChangeTrackingStorage(storage_dir)
