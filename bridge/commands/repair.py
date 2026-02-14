"""
bridge.commands.repair - Repair CLI command

This module provides the repair command for fixing corrupted data,
validating integrity, and restoring system state.

Command:
- repair: Fix corrupted data and validate integrity
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from storage.backup import BackupManager


@dataclass
class RepairResult:
    """Result of repair command."""

    success: bool
    fixed_items: int = 0
    errors: list[str] = field(default_factory=list)
    validation_report: dict[str, Any] = field(default_factory=dict)
    message: str = ""


class RepairCommand:
    """Repair command implementation."""

    def execute(
        self,
        path: Path | None = None,
        create_backup: bool = True,
        restore_from: Path | None = None,
        validate_only: bool = False,
        repair_storage: bool = True,
        repair_investigations: bool = True,
        verbose: bool = False,
    ) -> RepairResult:
        """Execute repair command."""
        target_path = path or Path.cwd()

        # Create backup before repair
        if create_backup and not validate_only:
            try:
                backup_dir = Path.home() / ".codemarshal" / "backups"
                backup_dir.mkdir(parents=True, exist_ok=True)
                manager = BackupManager(backup_dir)

                codemarshal_dir = target_path / ".codemarshal"
                if codemarshal_dir.exists():
                    manifest = manager.create_full_backup(codemarshal_dir)
                    print(f"Pre-repair backup created: {manifest.backup_id}")
            except Exception as e:
                print(f"Warning: Could not create pre-repair backup: {e}")

        # Restore from backup if specified
        if restore_from:
            try:
                backup_dir = Path.home() / ".codemarshal" / "backups"
                manager = BackupManager(backup_dir)

                codemarshal_dir = target_path / ".codemarshal"
                result = manager.restore_backup(restore_from.stem, codemarshal_dir)

                if result["success"]:
                    print("Restore completed successfully")
                    return RepairResult(
                        success=True, message=f"Restored from backup: {restore_from}"
                    )
                else:
                    return RepairResult(
                        success=False,
                        error=f"Restore failed: {result.get('error', 'Unknown error')}",
                    )
            except Exception as e:
                return RepairResult(success=False, errors=[f"Restore failed: {e}"])

        # Validate and repair
        validation_report = {}
        fixed_items = 0
        errors = []

        if repair_storage:
            storage_report = self._repair_storage(target_path, verbose)
            validation_report["storage"] = storage_report
            fixed_items += storage_report.get("fixed_count", 0)
            errors.extend(storage_report.get("errors", []))

        if repair_investigations:
            inv_report = self._repair_investigations(target_path, verbose)
            validation_report["investigations"] = inv_report
            fixed_items += inv_report.get("fixed_count", 0)
            errors.extend(inv_report.get("errors", []))

        # Check integrity
        integrity_report = self._check_integrity(target_path)
        validation_report["integrity"] = integrity_report

        return RepairResult(
            success=len(errors) == 0,
            fixed_items=fixed_items,
            validation_report=validation_report,
            errors=errors,
            message=f"Repaired {fixed_items} items",
        )

    def _repair_storage(self, path: Path, verbose: bool) -> dict:
        """Repair storage integrity."""
        report = {"valid": True, "checked": 0, "fixed_count": 0, "errors": []}

        storage_dir = path / ".codemarshal" / "storage"
        if not storage_dir.exists():
            return report

        for json_file in storage_dir.rglob("*.json"):
            report["checked"] += 1

            try:
                with open(json_file) as f:
                    content = f.read()
                    json.loads(content)
            except json.JSONDecodeError:
                report["valid"] = False
                report["errors"].append(f"Corrupted: {json_file}")

                if verbose:
                    print(f"  Repairing: {json_file}")

                # Try to fix
                try:
                    # Common fix: trailing commas
                    fixed_content = content.replace(",]", "]").replace(",}", "}")
                    parsed = json.loads(fixed_content)

                    with open(json_file, "w") as f:
                        json.dump(parsed, f, indent=2)

                    report["fixed_count"] += 1
                    if verbose:
                        print("    [OK] Fixed")

                except Exception as fix_error:
                    report["errors"].append(f"Cannot fix: {json_file} - {fix_error}")

        return report

    def _repair_investigations(self, path: Path, verbose: bool) -> dict:
        """Repair investigation state."""
        report = {"valid": True, "checked": 0, "fixed_count": 0, "errors": []}

        inv_dir = path / ".codemarshal" / "investigations"
        if not inv_dir.exists():
            return report

        required_files = ["metadata.json", "observations.json"]

        for inv_subdir in inv_dir.iterdir():
            if not inv_subdir.is_dir():
                continue

            report["checked"] += 1

            # Check required files
            for req_file in required_files:
                file_path = inv_subdir / req_file
                if not file_path.exists():
                    report["valid"] = False
                    report["errors"].append(f"Missing: {file_path}")

                    if not verbose:
                        continue

                    # Try to create missing file
                    try:
                        if req_file == "metadata.json":
                            metadata = {
                                "id": inv_subdir.name,
                                "created_at": datetime.now().isoformat(),
                                "status": "incomplete",
                            }
                            with open(file_path, "w") as f:
                                json.dump(metadata, f, indent=2)
                            report["fixed_count"] += 1
                            print(f"  Created: {file_path}")

                    except Exception as e:
                        report["errors"].append(f"Cannot create {file_path}: {e}")

        return report

    def _check_integrity(self, path: Path) -> dict:
        """Check system integrity."""
        report = {"checks_passed": 0, "checks_failed": 0, "warnings": []}

        # Check config
        try:
            from bridge.commands.config import ConfigShowCommand

            cmd = ConfigShowCommand()
            config = cmd._load_config(cmd._get_default_config_path())
            report["checks_passed"] += 1
        except Exception as e:
            report["checks_failed"] += 1
            report["warnings"].append(f"Config load failed: {e}")

        # Check storage
        try:
            from storage.atomic import atomic_read_binary, atomic_write_text

            test_file = path / ".codemarshal" / ".integrity_test"
            atomic_write_text(test_file, "test")
            atomic_read_binary(test_file)
            test_file.unlink()
            report["checks_passed"] += 1
        except Exception as e:
            report["checks_failed"] += 1
            report["warnings"].append(f"Storage integrity check failed: {e}")

        return report


# Convenience function for direct execution
def execute_repair(
    path: Path | None = None,
    create_backup: bool = True,
    restore_from: Path | None = None,
    validate_only: bool = False,
    repair_storage: bool = True,
    repair_investigations: bool = True,
    verbose: bool = False,
) -> RepairResult:
    """Convenience function for repair."""
    cmd = RepairCommand()
    return cmd.execute(
        path=path,
        create_backup=create_backup,
        restore_from=restore_from,
        validate_only=validate_only,
        repair_storage=repair_storage,
        repair_investigations=repair_investigations,
        verbose=verbose,
    )
