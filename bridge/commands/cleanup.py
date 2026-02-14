"""
bridge.commands.cleanup - Cleanup CLI command

This module provides the cleanup command for removing temporary files,
cache data, and test artifacts.

Command:
- cleanup: Remove temporary files and cache
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CleanupResult:
    """Result of cleanup command."""

    success: bool
    removed_count: int = 0
    freed_space_bytes: int = 0
    freed_space_mb: float = 0.0
    removed_items: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    dry_run: bool = False
    message: str = ""


class CleanupCommand:
    """Cleanup command implementation."""

    # Patterns to clean
    CLEAN_PATTERNS = {
        "cache": [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".pytest_cache",
            ".coverage",
            "htmlcov",
            ".pyright_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".hypothesis",
            "*.egg-info/.cache",
        ],
        "temp": [
            "*.tmp",
            "*.temp",
            "tmp/",
            "temp/",
            ".tmp/",
        ],
        "artifacts": [
            "build/",
            "dist/",
            "*.egg-info/",
            ".tox/",
            ".nox/",
            "node_modules/",
        ],
        "logs": [
            "*.log",
            "logs/",
            "*.stderr",
            "*.stdout",
        ],
    }

    # Directories to clean
    CLEAN_DIRS = [
        ".codemarshal/cache",
        ".codemarshal/tmp",
        ".codemarshal/checkpoints",
    ]

    def execute(
        self,
        path: Path | None = None,
        dry_run: bool = False,
        clean_all: bool = False,
        clean_cache: bool = False,
        clean_temp: bool = False,
        clean_artifacts: bool = False,
        clean_logs: bool = False,
        verbose: bool = False,
    ) -> CleanupResult:
        """Execute cleanup command."""
        target_path = path or Path.cwd()

        # Default: clean all if nothing specified
        if not clean_all and not any(
            [clean_cache, clean_temp, clean_artifacts, clean_logs]
        ):
            clean_cache = clean_temp = clean_artifacts = clean_logs = True

        removed_items = []
        freed_space = 0
        errors = []

        # Collect items to clean
        items_to_clean = []

        if clean_cache or clean_all:
            items_to_clean.extend(
                self._collect_items(target_path, self.CLEAN_PATTERNS["cache"])
            )

        if clean_temp or clean_all:
            items_to_clean.extend(
                self._collect_items(target_path, self.CLEAN_PATTERNS["temp"])
            )

        if clean_artifacts or clean_all:
            items_to_clean.extend(
                self._collect_items(target_path, self.CLEAN_PATTERNS["artifacts"])
            )

        if clean_logs or clean_all:
            items_to_clean.extend(
                self._collect_items(target_path, self.CLEAN_PATTERNS["logs"])
            )

        # Clean CodeMarshal directories
        for clean_dir in self.CLEAN_DIRS:
            dir_path = target_path / clean_dir
            if dir_path.exists():
                items_to_clean.append(("dir", dir_path))

        if dry_run:
            print("Would clean:")
            for item_type, item_path in items_to_clean:
                if verbose:
                    print(f"  [{item_type:<8}] {item_path}")
                else:
                    print(f"  {item_path}")
            print(f"\nTotal: {len(items_to_clean)} item(s)")

            # Calculate potential space freed
            potential_freed = sum(
                self._get_size(item_path) for _, item_path in items_to_clean
            )
            print(f"Potential space freed: {potential_freed / (1024 * 1024):.2f} MB")

            return CleanupResult(
                success=True,
                removed_count=len(items_to_clean),
                freed_space_bytes=potential_freed,
                dry_run=True,
            )

        # Perform cleanup
        for item_type, item_path in items_to_clean:
            try:
                if item_type == "dir":
                    size = self._get_size(item_path)
                    shutil.rmtree(item_path)
                    removed_items.append(str(item_path))
                    freed_space += size
                else:
                    if item_path.exists():
                        if item_path.is_file():
                            size = item_path.stat().st_size
                            item_path.unlink()
                            removed_items.append(str(item_path))
                            freed_space += size
                        elif item_path.is_dir():
                            size = self._get_size(item_path)
                            shutil.rmtree(item_path)
                            removed_items.append(str(item_path))
                            freed_space += size
            except PermissionError:
                errors.append(f"Permission denied: {item_path}")
            except Exception as e:
                errors.append(f"Error cleaning {item_path}: {e}")

        return CleanupResult(
            success=len(errors) == 0,
            removed_count=len(removed_items),
            freed_space_bytes=freed_space,
            freed_space_mb=freed_space / (1024 * 1024),
            removed_items=removed_items,
            errors=errors,
            message=f"Cleaned {len(removed_items)} items, freed {freed_space / (1024 * 1024):.2f} MB",
        )

    def _collect_items(self, base_path: Path, patterns: list) -> list:
        """Collect items matching patterns."""
        items = []

        for pattern in patterns:
            if pattern.endswith("/"):
                # Directory pattern
                dir_path = base_path / pattern.rstrip("/")
                if dir_path.exists():
                    items.append(("dir", dir_path))
            elif "*" in pattern:
                # Glob pattern
                for match in base_path.rglob(pattern):
                    if match.exists():
                        items.append(("glob", match))
            else:
                # Exact match
                file_path = base_path / pattern
                if file_path.exists():
                    items.append(("exact", file_path))

        return items

    def _get_size(self, path: Path) -> int:
        """Get total size of path."""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        return 0


# Convenience function for direct execution
def execute_cleanup(
    path: Path | None = None,
    dry_run: bool = False,
    clean_all: bool = False,
    clean_cache: bool = False,
    clean_temp: bool = False,
    clean_artifacts: bool = False,
    clean_logs: bool = False,
    verbose: bool = False,
) -> CleanupResult:
    """Convenience function for cleanup."""
    cmd = CleanupCommand()
    return cmd.execute(
        path=path,
        dry_run=dry_run,
        clean_all=clean_all,
        clean_cache=clean_cache,
        clean_temp=clean_temp,
        clean_artifacts=clean_artifacts,
        clean_logs=clean_logs,
        verbose=verbose,
    )
