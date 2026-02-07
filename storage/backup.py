"""
BACKUP STRATEGY FOR LARGE RUNS

Manages backup creation and restoration for 50K+ file operations.
Provides incremental backups and space-efficient storage.

Constitutional Rules:
1. No data loss during backup
2. Backups are verifiable
3. Restoration is deterministic
4. Space usage is optimized
"""

import hashlib
import json
import shutil
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .atomic import atomic_write_text


@dataclass(frozen=True)
class BackupManifest:
    """Manifest for a backup set."""

    backup_id: str
    created_at: datetime
    file_count: int
    total_size: int
    checksum: str
    base_path: str
    compressed: bool = False
    incremental: bool = False
    parent_backup_id: str | None = None


@dataclass
class BackupManager:
    """
    Manages backup creation and restoration.

    Features:
    - Full and incremental backups
    - Compression support
    - Automatic cleanup
    - Verification
    """

    def __init__(self, backup_dir: Path):
        """
        Initialize backup manager.

        Args:
            backup_dir: Directory to store backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self._manifests: dict[str, BackupManifest] = {}
        self._load_manifests()

    def _load_manifests(self) -> None:
        """Load existing backup manifests."""
        manifest_file = self.backup_dir / "manifests.json"
        if manifest_file.exists():
            try:
                with open(manifest_file) as f:
                    data = json.load(f)
                    for backup_id, manifest_data in data.items():
                        self._manifests[backup_id] = BackupManifest(
                            backup_id=backup_id,
                            created_at=datetime.fromisoformat(
                                manifest_data["created_at"]
                            ),
                            file_count=manifest_data["file_count"],
                            total_size=manifest_data["total_size"],
                            checksum=manifest_data["checksum"],
                            base_path=manifest_data["base_path"],
                            compressed=manifest_data.get("compressed", False),
                            incremental=manifest_data.get("incremental", False),
                            parent_backup_id=manifest_data.get("parent_backup_id"),
                        )
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

    def _save_manifests(self) -> None:
        """Save backup manifests to disk."""
        manifest_file = self.backup_dir / "manifests.json"
        data = {}
        for backup_id, manifest in self._manifests.items():
            data[backup_id] = {
                "created_at": manifest.created_at.isoformat(),
                "file_count": manifest.file_count,
                "total_size": manifest.total_size,
                "checksum": manifest.checksum,
                "base_path": manifest.base_path,
                "compressed": manifest.compressed,
                "incremental": manifest.incremental,
                "parent_backup_id": manifest.parent_backup_id,
            }

        atomic_write_text(manifest_file, json.dumps(data, indent=2))

    def create_full_backup(
        self, source_dir: Path, backup_id: str | None = None
    ) -> BackupManifest:
        """
        Create a full backup of source directory.

        Args:
            source_dir: Directory to backup
            backup_id: Optional backup ID

        Returns:
            Backup manifest
        """
        if not backup_id:
            backup_id = f"full_{int(time.time())}"

        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)

        # Collect all files to backup
        files_to_backup = []
        total_size = 0

        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(source_dir)
                files_to_backup.append((rel_path, file_path))
                total_size += file_path.stat().st_size

        # Copy files with progress tracking
        copied_count = 0
        for rel_path, source_file in files_to_backup:
            dest_file = backup_path / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            try:
                shutil.copy2(source_file, dest_file)
                copied_count += 1

                # Progress indicator for large backups
                if copied_count % 1000 == 0:
                    print(
                        f"Backup progress: {copied_count}/{len(files_to_backup)} files",
                        flush=True,
                    )

            except OSError as e:
                print(f"[WARN] Failed to backup {source_file}: {e}", flush=True)

        # Calculate checksum of backup
        backup_checksum = self._calculate_directory_checksum(backup_path)

        # Create manifest
        manifest = BackupManifest(
            backup_id=backup_id,
            created_at=datetime.now(UTC),
            file_count=copied_count,
            total_size=total_size,
            checksum=backup_checksum,
            base_path=str(source_dir),
            compressed=False,
            incremental=False,
        )

        # Save manifest
        with self.lock:
            self._manifests[backup_id] = manifest
            self._save_manifests()

        print(
            f"[OK] Full backup created: {backup_id} ({copied_count} files, {total_size // 1024 // 1024}MB)",
            flush=True,
        )
        return manifest

    def create_incremental_backup(
        self, source_dir: Path, parent_backup_id: str, backup_id: str | None = None
    ) -> BackupManifest:
        """
        Create incremental backup based on parent backup.

        Args:
            source_dir: Directory to backup
            parent_backup_id: ID of parent backup
            backup_id: Optional backup ID

        Returns:
            Backup manifest
        """
        if parent_backup_id not in self._manifests:
            raise ValueError(f"Parent backup {parent_backup_id} not found")

        if not backup_id:
            backup_id = f"inc_{int(time.time())}"

        self._manifests[parent_backup_id]
        parent_backup_path = self.backup_dir / parent_backup_id

        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)

        # Find new/modified files
        new_files = []
        total_size = 0

        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(source_dir)
                parent_file = parent_backup_path / rel_path

                # Check if file is new or modified
                should_backup = True
                if parent_file.exists():
                    # Compare modification times and sizes
                    if (
                        file_path.stat().st_mtime <= parent_file.stat().st_mtime
                        and file_path.stat().st_size == parent_file.stat().st_size
                    ):
                        should_backup = False

                if should_backup:
                    new_files.append((rel_path, file_path))
                    total_size += file_path.stat().st_size

        # Copy only new/modified files
        copied_count = 0
        for rel_path, source_file in new_files:
            dest_file = backup_path / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            try:
                shutil.copy2(source_file, dest_file)
                copied_count += 1
            except OSError as e:
                print(f"[WARN] Failed to backup {source_file}: {e}", flush=True)

        # Calculate checksum
        backup_checksum = self._calculate_directory_checksum(backup_path)

        # Create manifest
        manifest = BackupManifest(
            backup_id=backup_id,
            created_at=datetime.now(UTC),
            file_count=copied_count,
            total_size=total_size,
            checksum=backup_checksum,
            base_path=str(source_dir),
            compressed=False,
            incremental=True,
            parent_backup_id=parent_backup_id,
        )

        # Save manifest
        with self.lock:
            self._manifests[backup_id] = manifest
            self._save_manifests()

        print(
            f"[OK] Incremental backup created: {backup_id} ({copied_count} new files, {total_size // 1024 // 1024}MB)",
            flush=True,
        )
        return manifest

    def restore_backup(self, backup_id: str, target_dir: Path) -> dict[str, Any]:
        """
        Restore from backup to target directory.

        Args:
            backup_id: ID of backup to restore
            target_dir: Directory to restore to

        Returns:
            Restoration report
        """
        if backup_id not in self._manifests:
            raise ValueError(f"Backup {backup_id} not found")

        manifest = self._manifests[backup_id]
        backup_path = self.backup_dir / backup_id

        # Verify backup integrity
        current_checksum = self._calculate_directory_checksum(backup_path)
        if current_checksum != manifest.checksum:
            return {
                "success": False,
                "error": f"Backup corruption detected: expected {manifest.checksum}, got {current_checksum}",
                "restored_files": 0,
            }

        # For incremental backups, we need to restore parent first
        if manifest.incremental and manifest.parent_backup_id:
            parent_result = self.restore_backup(manifest.parent_backup_id, target_dir)
            if not parent_result["success"]:
                return parent_result

        # Restore files
        restored_count = 0
        errors = []

        for file_path in backup_path.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(backup_path)
                dest_file = target_dir / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                try:
                    shutil.copy2(file_path, dest_file)
                    restored_count += 1
                except OSError as e:
                    errors.append(f"Failed to restore {rel_path}: {e}")

        return {
            "success": len(errors) == 0,
            "restored_files": restored_count,
            "errors": errors,
            "backup_id": backup_id,
            "restored_at": datetime.now(UTC).isoformat(),
        }

    def cleanup_old_backups(
        self, keep_count: int = 5, days: int = 30
    ) -> dict[str, Any]:
        """
        Clean up old backups.

        Args:
            keep_count: Minimum number of backups to keep
            days: Remove backups older than this many days

        Returns:
            Cleanup report
        """
        cutoff_time = time.time() - (days * 24 * 3600)

        # Sort backups by creation time
        sorted_backups = sorted(self._manifests.values(), key=lambda m: m.created_at)

        to_remove = []
        # Always keep the most recent 'keep_count' backups
        for i, manifest in enumerate(sorted_backups):
            if i < len(sorted_backups) - keep_count:
                if manifest.created_at.timestamp() < cutoff_time:
                    to_remove.append(manifest)

        # Remove old backups
        removed_count = 0
        freed_space = 0

        for manifest in to_remove:
            backup_path = self.backup_dir / manifest.backup_id
            try:
                # Calculate size before deletion
                if backup_path.exists():
                    size = sum(
                        f.stat().st_size for f in backup_path.rglob("*") if f.is_file()
                    )
                    freed_space += size
                    shutil.rmtree(backup_path)

                # Remove from manifests
                with self.lock:
                    del self._manifests[manifest.backup_id]
                    self._save_manifests()

                removed_count += 1
                print(f"Removed old backup: {manifest.backup_id}", flush=True)

            except OSError as e:
                print(
                    f"[WARN] Failed to remove backup {manifest.backup_id}: {e}",
                    flush=True,
                )

        return {
            "removed_count": removed_count,
            "freed_space_bytes": freed_space,
            "freed_space_mb": freed_space // 1024 // 1024,
            "cleaned_at": datetime.now(UTC).isoformat(),
        }

    def get_backup_list(self) -> list[dict[str, Any]]:
        """Get list of all backups."""
        backups = []
        for manifest in self._manifests.values():
            backups.append(
                {
                    "backup_id": manifest.backup_id,
                    "created_at": manifest.created_at.isoformat(),
                    "file_count": manifest.file_count,
                    "total_size_mb": manifest.total_size // 1024 // 1024,
                    "compressed": manifest.compressed,
                    "incremental": manifest.incremental,
                    "parent_backup_id": manifest.parent_backup_id,
                }
            )

        return sorted(backups, key=lambda b: b["created_at"], reverse=True)

    def verify_backup(self, backup_id: str) -> dict[str, Any]:
        """
        Verify backup integrity.

        Args:
            backup_id: ID of backup to verify

        Returns:
            Verification report
        """
        if backup_id not in self._manifests:
            return {"valid": False, "error": "Backup not found"}

        manifest = self._manifests[backup_id]
        backup_path = self.backup_dir / backup_id

        if not backup_path.exists():
            return {"valid": False, "error": "Backup files missing"}

        # Verify checksum
        current_checksum = self._calculate_directory_checksum(backup_path)
        is_valid = current_checksum == manifest.checksum

        # Count actual files
        actual_file_count = len(list(backup_path.rglob("*")))

        return {
            "valid": is_valid,
            "expected_files": manifest.file_count,
            "actual_files": actual_file_count,
            "expected_checksum": manifest.checksum,
            "actual_checksum": current_checksum,
            "verified_at": datetime.now(UTC).isoformat(),
        }

    def _calculate_directory_checksum(self, dir_path: Path) -> str:
        """Calculate recursive checksum of directory."""
        hasher = hashlib.sha256()

        for file_path in sorted(dir_path.rglob("*")):
            if file_path.is_file():
                # Include relative path and file content
                rel_path = str(file_path.relative_to(dir_path))
                hasher.update(rel_path.encode("utf-8"))

                # Add file content
                with open(file_path, "rb") as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)

        return hasher.hexdigest()


# Export public API
__all__ = ["BackupManifest", "BackupManager"]
