"""
bridge.commands.backup - Backup/Restore CLI commands

This module provides CLI commands for managing CodeMarshal backups.
Uses storage.backup.BackupManager internally.

Commands:
- backup create: Create a new backup
- backup list: List available backups
- backup restore: Restore from a backup
- backup verify: Verify backup integrity
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from storage.backup import BackupManager


@dataclass
class BackupCreateResult:
    """Result of backup create command."""

    success: bool
    backup_id: str = ""
    file_count: int = 0
    size_mb: int = 0
    message: str = ""
    error: str | None = None


@dataclass
class BackupListResult:
    """Result of backup list command."""

    success: bool
    backups: list[dict[str, Any]] = field(default_factory=list)
    count: int = 0
    message: str = ""
    error: str | None = None


@dataclass
class BackupRestoreResult:
    """Result of backup restore command."""

    success: bool
    restored_files: int = 0
    errors: list[str] = field(default_factory=list)
    message: str = ""
    error: str | None = None


@dataclass
class BackupVerifyResult:
    """Result of backup verify command."""

    success: bool
    valid: bool = False
    expected_files: int = 0
    actual_files: int = 0
    message: str = ""
    error: str | None = None


class BackupCreateCommand:
    """Create backup command."""

    def __init__(self, backup_dir: Path | None = None):
        self.backup_dir = backup_dir or self._get_default_backup_dir()

    def execute(
        self,
        source_path: Path,
        backup_type: str = "full",
        parent_backup_id: str | None = None,
        compress: bool = False,
    ) -> BackupCreateResult:
        """
        Execute backup create command.

        Args:
            source_path: Directory to backup
            backup_type: Type of backup (full/incremental)
            parent_backup_id: Parent backup ID for incremental
            compress: Whether to compress

        Returns:
            BackupCreateResult with backup status
        """
        if not source_path.exists():
            return BackupCreateResult(
                success=False, error=f"Source path does not exist: {source_path}"
            )

        manager = BackupManager(self.backup_dir)

        try:
            if backup_type == "incremental":
                if not parent_backup_id:
                    return BackupCreateResult(
                        success=False,
                        error="Parent backup ID required for incremental backup",
                    )
                manifest = manager.create_incremental_backup(
                    source_path, parent_backup_id
                )
            else:
                manifest = manager.create_full_backup(source_path)

            return BackupCreateResult(
                success=True,
                backup_id=manifest.backup_id,
                file_count=manifest.file_count,
                size_mb=manifest.total_size // 1024 // 1024,
                message=f"Backup created: {manifest.backup_id}",
            )

        except Exception as e:
            return BackupCreateResult(
                success=False, error=f"Backup creation failed: {e}"
            )

    def _get_default_backup_dir(self) -> Path:
        """Get default backup directory."""
        return Path.home() / ".codemarshal" / "backups"


class BackupListCommand:
    """List backups command."""

    def __init__(self, backup_dir: Path | None = None):
        self.backup_dir = backup_dir or self._get_default_backup_dir()

    def execute(
        self,
        output_format: str = "table",
    ) -> BackupListResult:
        """
        Execute backup list command.

        Args:
            output_format: Output format (table/json)

        Returns:
            BackupListResult with backup list
        """
        manager = BackupManager(self.backup_dir)

        try:
            backups = manager.get_backup_list()

            return BackupListResult(
                success=True,
                backups=backups,
                count=len(backups),
                message=f"Found {len(backups)} backup(s)",
            )

        except Exception as e:
            return BackupListResult(success=False, error=f"Failed to list backups: {e}")

    def _get_default_backup_dir(self) -> Path:
        """Get default backup directory."""
        return Path.home() / ".codemarshal" / "backups"


class BackupRestoreCommand:
    """Restore backup command."""

    def __init__(self, backup_dir: Path | None = None):
        self.backup_dir = backup_dir or self._get_default_backup_dir()

    def execute(
        self,
        backup_id: str,
        target_path: Path,
        dry_run: bool = False,
    ) -> BackupRestoreResult:
        """
        Execute backup restore command.

        Args:
            backup_id: ID of backup to restore
            target_path: Directory to restore to
            dry_run: Preview restore without actually restoring

        Returns:
            BackupRestoreResult with restore status
        """
        manager = BackupManager(self.backup_dir)

        if dry_run:
            # Preview mode
            try:
                backups = manager.get_backup_list()
                backup = next((b for b in backups if b["backup_id"] == backup_id), None)
                if not backup:
                    return BackupRestoreResult(
                        success=False, error=f"Backup not found: {backup_id}"
                    )

                return BackupRestoreResult(
                    success=True,
                    message=f"Would restore {backup['file_count']} files from {backup_id} to {target_path}",
                )
            except Exception as e:
                return BackupRestoreResult(success=False, error=f"Preview failed: {e}")

        # Actual restore
        try:
            result = manager.restore_backup(backup_id, target_path)

            if result["success"]:
                return BackupRestoreResult(
                    success=True,
                    restored_files=result["restored_files"],
                    message=f"Restored {result['restored_files']} files from {backup_id}",
                )
            else:
                return BackupRestoreResult(
                    success=False,
                    error=result.get("error", "Unknown error"),
                    restored_files=result.get("restored_files", 0),
                    errors=result.get("errors", []),
                )

        except Exception as e:
            return BackupRestoreResult(success=False, error=f"Restore failed: {e}")

    def _get_default_backup_dir(self) -> Path:
        """Get default backup directory."""
        return Path.home() / ".codemarshal" / "backups"


class BackupVerifyCommand:
    """Verify backup command."""

    def __init__(self, backup_dir: Path | None = None):
        self.backup_dir = backup_dir or self._get_default_backup_dir()

    def execute(
        self,
        backup_id: str,
    ) -> BackupVerifyResult:
        """
        Execute backup verify command.

        Args:
            backup_id: ID of backup to verify

        Returns:
            BackupVerifyResult with verification status
        """
        manager = BackupManager(self.backup_dir)

        try:
            result = manager.verify_backup(backup_id)

            return BackupVerifyResult(
                success=True,
                valid=result["valid"],
                expected_files=result.get("expected_files", 0),
                actual_files=result.get("actual_files", 0),
                message="Backup is valid"
                if result["valid"]
                else f"Backup invalid: {result.get('error', 'Unknown error')}",
            )

        except Exception as e:
            return BackupVerifyResult(success=False, error=f"Verification failed: {e}")

    def _get_default_backup_dir(self) -> Path:
        """Get default backup directory."""
        return Path.home() / ".codemarshal" / "backups"


# Convenience functions for direct execution
def execute_backup_create(
    source_path: Path,
    backup_type: str = "full",
    parent_backup_id: str | None = None,
    compress: bool = False,
    backup_dir: Path | None = None,
) -> BackupCreateResult:
    """Convenience function for backup create."""
    cmd = BackupCreateCommand(backup_dir)
    return cmd.execute(
        source_path=source_path,
        backup_type=backup_type,
        parent_backup_id=parent_backup_id,
        compress=compress,
    )


def execute_backup_list(
    output_format: str = "table",
    backup_dir: Path | None = None,
) -> BackupListResult:
    """Convenience function for backup list."""
    cmd = BackupListCommand(backup_dir)
    return cmd.execute(output_format=output_format)


def execute_backup_restore(
    backup_id: str,
    target_path: Path,
    dry_run: bool = False,
    backup_dir: Path | None = None,
) -> BackupRestoreResult:
    """Convenience function for backup restore."""
    cmd = BackupRestoreCommand(backup_dir)
    return cmd.execute(
        backup_id=backup_id,
        target_path=target_path,
        dry_run=dry_run,
    )


def execute_backup_verify(
    backup_id: str,
    backup_dir: Path | None = None,
) -> BackupVerifyResult:
    """Convenience function for backup verify."""
    cmd = BackupVerifyCommand(backup_dir)
    return cmd.execute(backup_id=backup_id)
