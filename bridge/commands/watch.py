"""
watch.py - Real-time file system watching and diff commands.

Commands:
    - watch: Monitor directory for changes
    - diff: Show differences between file versions
    - status: Show current investigation status with changes
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from observations.eyes.diff_sight import DiffSight, generate_diff_report
from observations.eyes.watcher import ChangeType, FileSystemWatcher, WatcherConfig


def watch_command(
    path: str,
    recursive: bool = True,
    duration: int | None = None,
    output_format: str = "text",
) -> dict[str, Any]:
    """
    Watch a directory for file system changes.

    Args:
        path: Directory path to watch
        recursive: Watch subdirectories
        duration: Watch duration in seconds (None = indefinite)
        output_format: Output format (text, json)

    Returns:
        Dictionary with watch results
    """
    watch_path = Path(path).resolve()

    if not watch_path.exists():
        return {
            "success": False,
            "error": f"Path does not exist: {watch_path}",
        }

    if not watch_path.is_dir():
        return {
            "success": False,
            "error": f"Path is not a directory: {watch_path}",
        }

    # Check if watchdog is available
    try:
        from observations.eyes.watcher import WATCHDOG_AVAILABLE

        if not WATCHDOG_AVAILABLE:
            return {
                "success": False,
                "error": (
                    "watchdog library not installed. Install with: pip install watchdog"
                ),
            }
    except ImportError:
        return {
            "success": False,
            "error": (
                "watchdog library not installed. Install with: pip install watchdog"
            ),
        }

    changes = []

    def on_change(change):
        """Callback for file system changes."""
        changes.append(change)

        if output_format == "text":
            change_type_str = {
                ChangeType.CREATED: "+",
                ChangeType.MODIFIED: "~",
                ChangeType.DELETED: "-",
                ChangeType.MOVED: "→",
            }.get(change.change_type, "?")

            print(
                f"[{change_type_str}] {change.path}",
                file=sys.stderr,
                flush=True,
            )

    config = WatcherConfig(recursive=recursive)

    try:
        with FileSystemWatcher(watch_path, config, on_change) as watcher:
            if output_format == "text":
                print(
                    f"Watching {watch_path} "
                    f"({'recursively' if recursive else 'non-recursively'})...",
                    file=sys.stderr,
                )
                print("Press Ctrl+C to stop", file=sys.stderr)

            if duration:
                time.sleep(duration)
            else:
                # Run indefinitely until interrupted
                while True:
                    time.sleep(0.1)

    except KeyboardInterrupt:
        if output_format == "text":
            print("\nStopped watching.", file=sys.stderr)

    result = {
        "success": True,
        "watch_path": str(watch_path),
        "recursive": recursive,
        "changes_detected": len(changes),
        "changes": [c.to_dict() for c in changes],
    }

    if output_format == "json":
        print(json.dumps(result, indent=2))
    elif output_format == "text":
        print(f"\nTotal changes detected: {len(changes)}", file=sys.stderr)

    return result


def diff_command(
    old_path: str,
    new_path: str | None = None,
    unified: bool = True,
    semantic: bool = True,
    output_format: str = "text",
) -> dict[str, Any]:
    """
    Show differences between file versions.

    Args:
        old_path: Path to old file or directory
        new_path: Path to new file or directory (None = compare with current)
        unified: Show unified diff format
        semantic: Show semantic changes
        output_format: Output format (text, json)

    Returns:
        Dictionary with diff results
    """
    old_file = Path(old_path).resolve()

    if not old_file.exists():
        return {
            "success": False,
            "error": f"Path does not exist: {old_file}",
        }

    diff_sight = DiffSight()

    if old_file.is_file():
        # Single file diff
        if new_path:
            new_file = Path(new_path).resolve()
            if not new_file.exists():
                return {
                    "success": False,
                    "error": f"New path does not exist: {new_file}",
                }
            file_diff = diff_sight.diff_files(old_file, new_file)
        else:
            # Compare with tracked version
            old_content = diff_sight._read_file(old_file)
            file_diff = diff_sight.calculate_diff(old_file, None, old_content)

        diffs = [file_diff]
    else:
        # Directory diff
        if new_path:
            new_dir = Path(new_path).resolve()
            if not new_dir.exists():
                return {
                    "success": False,
                    "error": f"New path does not exist: {new_dir}",
                }

            # Get all files in both directories
            old_files = set(old_file.rglob("*"))
            new_files = set(new_dir.rglob("*"))

            all_files = old_files | new_files
            diffs = []

            for file_path in all_files:
                if file_path.is_file():
                    rel_path = file_path.relative_to(
                        old_file if file_path in old_files else new_dir
                    )
                    old_file_path = old_file / rel_path
                    new_file_path = new_dir / rel_path

                    file_diff = diff_sight.diff_files(old_file_path, new_file_path)
                    diffs.append(file_diff)
        else:
            # Compare files in directory with their tracked versions
            all_files = list(old_file.rglob("*"))
            diffs = []

            for file_path in all_files:
                if file_path.is_file():
                    old_content = diff_sight._read_file(file_path)
                    file_diff = diff_sight.calculate_diff(file_path, None, old_content)
                    diffs.append(file_diff)

    # Generate report
    report = generate_diff_report(diffs)

    # Output results
    if output_format == "text":
        _print_diff_report(report, diffs, unified, semantic)
    elif output_format == "json":
        print(json.dumps(report, indent=2))

    return {
        "success": True,
        "summary": report["summary"],
        "file_changes": len(report["file_changes"]),
        "semantic_changes": len(report["semantic_changes"]),
    }


def status_command(
    path: str | None = None,
    output_format: str = "text",
) -> dict[str, Any]:
    """
    Show current investigation status with recent changes.

    Args:
        path: Investigation path (None = use current directory)
        output_format: Output format (text, json)

    Returns:
        Dictionary with status information
    """
    if path is None:
        path = "."

    watch_path = Path(path).resolve()

    if not watch_path.exists():
        return {
            "success": False,
            "error": f"Path does not exist: {watch_path}",
        }

    # Get file statistics
    total_files = 0
    total_dirs = 0
    recent_files = []

    cutoff_time = time.time() - 3600  # Files modified in last hour

    for item in watch_path.rglob("*"):
        if item.is_file():
            total_files += 1
            try:
                stat = item.stat()
                if stat.st_mtime > cutoff_time:
                    recent_files.append(
                        {
                            "path": str(item.relative_to(watch_path)),
                            "modified": stat.st_mtime,
                            "size": stat.st_size,
                        }
                    )
            except (OSError, IOError):
                pass
        elif item.is_dir():
            total_dirs += 1

    # Sort recent files by modification time
    recent_files.sort(key=lambda x: x["modified"], reverse=True)

    result = {
        "success": True,
        "path": str(watch_path),
        "total_files": total_files,
        "total_directories": total_dirs,
        "recent_changes_count": len(recent_files),
        "recent_changes": recent_files[:10],  # Top 10 most recent
    }

    if output_format == "text":
        print(f"Investigation Status: {watch_path}")
        print(f"Total files: {total_files}")
        print(f"Total directories: {total_dirs}")
        print(f"\nRecent changes (last hour): {len(recent_files)}")

        if recent_files:
            print("\nMost recent:")
            for file_info in recent_files[:10]:
                mtime = time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(file_info["modified"]),
                )
                print(f"  [{mtime}] {file_info['path']}")
    elif output_format == "json":
        print(json.dumps(result, indent=2))

    return result


def _print_diff_report(
    report: dict,
    diffs: list,
    unified: bool,
    semantic: bool,
) -> None:
    """Print diff report in text format."""
    summary = report["summary"]

    print(f"Diff Summary")
    print(f"============")
    print(f"Files changed: {summary['files_changed']}")
    print(f"  Added: {summary['files_added']}")
    print(f"  Deleted: {summary['files_deleted']}")
    print(f"  Modified: {summary['files_modified']}")
    print()
    print(f"Lines changed:")
    print(f"  Added: {summary['total_lines_added']}")
    print(f"  Deleted: {summary['total_lines_deleted']}")
    print(f"  Modified: {summary['total_lines_modified']}")

    if semantic and report["semantic_changes"]:
        print()
        print(f"Semantic Changes ({len(report['semantic_changes'])}):")
        for change in report["semantic_changes"]:
            print(f"  [{change['type']}] {change['symbol']}")
            if change["description"]:
                print(f"    {change['description']}")

    if unified:
        print()
        for diff in diffs:
            if diff.has_changes:
                diff_text = diffs[0].__class__.__module__.generate_unified_diff(diff)
                if diff_text:
                    print(diff_text)


# Command entry points for CLI integration
def execute_watch(
    path: str,
    recursive: bool = True,
    duration: int | None = None,
    format: str = "text",
) -> dict[str, Any]:
    """CLI entry point for watch command."""
    return watch_command(path, recursive, duration, format)


def execute_diff(
    old_path: str,
    new_path: str | None = None,
    unified: bool = True,
    semantic: bool = True,
    format: str = "text",
) -> dict[str, Any]:
    """CLI entry point for diff command."""
    return diff_command(old_path, new_path, unified, semantic, format)


def execute_status(
    path: str | None = None,
    format: str = "text",
) -> dict[str, Any]:
    """CLI entry point for status command."""
    return status_command(path, format)
