#!/usr/bin/env python3
"""
Count lines of code in a codebase, skipping specified directories.

Features:
- Skips common directories (venv, node_modules, .git, etc.)
- Binary file detection
- Configurable file extensions
- Progress reporting
- Breakdown by file type
- Case-insensitive directory matching
- Symlink handling
"""

import argparse
import fnmatch
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

# Default directories to skip (common build artifacts, dependencies, IDE files)
DEFAULT_SKIP_DIRS = {
    # Virtual environments
    "venv",
    "env",
    ".venv",
    ".env",
    "virtualenv",
    "virtualenvs",
    # Node.js
    "node_modules",
    "bower_components",
    # Python
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".egg-info",
    ".eggs",
    "dist",
    "build",
    "develop-eggs",
    "parts",
    "sdist",
    "wheels",
    # Version control
    ".git",
    ".svn",
    ".hg",
    ".bzr",
    "_darcs",
    "CVS",
    # IDE and editors
    ".idea",
    ".vscode",
    ".vs",
    ".sublime-project",
    ".sublime-workspace",
    # Coverage and test artifacts
    "htmlcov",
    ".coverage",
    "coverage",
    ".nyc_output",
    # Documentation builds
    "site-packages",
    "docs/_build",
    "doc/_build",
    "_build",
    # Misc
    ".next",
    ".nuxt",
    "out",
    ".output",
    "target",  # Next.js/Nuxt/Rust
}

# Default file extensions to consider as source code
DEFAULT_EXTENSIONS = {
    # Python
    ".py",
    ".pyw",
    ".pyi",
    # JavaScript/TypeScript
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".mts",
    ".cts",
    # Web
    ".html",
    ".htm",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".vue",
    ".svelte",
    # Java/Kotlin
    ".java",
    ".kt",
    ".kts",
    # C/C++
    ".c",
    ".cpp",
    ".cc",
    ".cxx",
    ".h",
    ".hpp",
    ".hh",
    ".hxx",
    # C#
    ".cs",
    ".csx",
    # Go
    ".go",
    # Ruby
    ".rb",
    ".erb",
    ".gemspec",
    # PHP
    ".php",
    ".phtml",
    ".php3",
    ".php4",
    ".php5",
    ".phps",
    # Swift
    ".swift",
    # Rust
    ".rs",
    ".rlib",
    # Shell
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".ps1",
    ".psm1",
    ".bat",
    ".cmd",
    # Config/Data
    ".xml",
    ".json",
    ".jsonc",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    # Documentation
    ".md",
    ".rst",
    ".txt",
    ".adoc",
    # Database
    ".sql",
    # Other
    ".r",
    ".pl",
    ".pm",
    ".t",
    ".lua",
    ".vim",
    ".el",
    ".clj",
    ".cljs",
    ".ex",
    ".exs",
    ".erl",
    ".hrl",
    ".fs",
    ".fsx",
    ".ml",
    ".mli",
}

# Chunk size for binary detection
BINARY_CHECK_SIZE = 8192

# Maximum file size to process (in bytes) - skip files larger than this
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def is_binary(file_path: Path) -> bool:
    """
    Check if a file is binary.

    Uses multiple heuristics:
    1. Check for null bytes in the first 8KB
    2. Check if file has encoding issues
    3. Skip if file is too large

    Returns True if file appears to be binary.
    """
    try:
        # Check file size first
        if file_path.stat().st_size > MAX_FILE_SIZE:
            return True  # Treat very large files as binary to skip them

        with open(file_path, "rb") as f:
            chunk = f.read(BINARY_CHECK_SIZE)

            # Check for null bytes (definitive binary indicator)
            if b"\0" in chunk:
                return True

            # Try to decode as UTF-8
            try:
                chunk.decode("utf-8")
                return False
            except UnicodeDecodeError:
                # Try latin-1 which accepts all bytes
                chunk.decode("latin-1")
                # If it decodes as latin-1 but not UTF-8, might be binary
                # Check ratio of non-printable characters
                non_printable = sum(1 for b in chunk if b < 32 and b not in (9, 10, 13))
                if len(chunk) > 0 and non_printable / len(chunk) > 0.3:
                    return True
                return False

    except OSError:
        return True  # If we can't read it, treat as binary


def count_lines_in_file(
    file_path: Path,
    skip_blank: bool = False,
    skip_comments: bool = False,
    comment_patterns: list[str] | None = None,
) -> int:
    """
    Count lines in a text file.

    Args:
        file_path: Path to the file
        skip_blank: If True, ignore lines with only whitespace
        skip_comments: If True, ignore comment lines (basic support)
        comment_patterns: List of comment prefixes for this file type

    Returns:
        Number of lines
    """
    try:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        count = 0
        for line in lines:
            # Skip blank lines if requested
            if skip_blank and not line.strip():
                continue

            # Skip comment lines if requested (basic implementation)
            if skip_comments and comment_patterns:
                stripped = line.strip()
                if any(stripped.startswith(prefix) for prefix in comment_patterns):
                    continue

            count += 1

        return count

    except OSError:
        return 0


def should_skip_dir(
    dir_name: str, skip_dirs: set[str], case_sensitive: bool = False
) -> bool:
    """
    Check if a directory should be skipped.

    Supports both exact matching and wildcard patterns.
    """
    if case_sensitive:
        return dir_name in skip_dirs or any(
            fnmatch.fnmatch(dir_name, pattern)
            for pattern in skip_dirs
            if "*" in pattern or "?" in pattern
        )
    else:
        dir_name_lower = dir_name.lower()
        skip_dirs_lower = {d.lower() for d in skip_dirs}
        return dir_name_lower in skip_dirs_lower or any(
            fnmatch.fnmatch(dir_name_lower, pattern.lower())
            for pattern in skip_dirs
            if "*" in pattern or "?" in pattern
        )


def get_comment_patterns(extension: str) -> list[str]:
    """Get comment patterns for a given file extension."""
    patterns = {
        ".py": ["#"],
        ".js": ["//", "/*"],
        ".jsx": ["//", "/*"],
        ".ts": ["//", "/*"],
        ".tsx": ["//", "/*"],
        ".java": ["//", "/*"],
        ".c": ["//", "/*"],
        ".cpp": ["//", "/*"],
        ".go": ["//"],
        ".rb": ["#"],
        ".php": ["//", "#", "/*"],
        ".sh": ["#"],
        ".ps1": ["#"],
        ".yaml": ["#"],
        ".yml": ["#"],
        ".json": [],  # JSON doesn't have comments (technically)
    }
    return patterns.get(extension, [])


def format_number(n: int) -> str:
    """Format a number with thousand separators."""
    return f"{n:,}"


def format_size(size_bytes: int) -> str:
    """Format byte size to human readable."""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description="Count lines of code in a codebase, skipping common junk directories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Count LOC in current directory
  %(prog)s /path/to/project         # Count LOC in specific directory
  %(prog)s --skip-blank             # Exclude blank lines
  %(prog)s --skip-dirs logs temp    # Skip additional directories
  %(prog)s --extensions .py .js     # Only count Python and JS files
  %(prog)s --progress               # Show progress while scanning
  %(prog)s --verbose                # Show files as they are processed
        """,
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--skip-dirs",
        metavar="DIR",
        nargs="+",
        default=[],
        help="Additional directory names to skip (case-insensitive, supports wildcards)",
    )
    parser.add_argument(
        "--no-default-skips",
        action="store_true",
        help="Do NOT use the default skip directories",
    )
    parser.add_argument(
        "--extensions",
        metavar="EXT",
        nargs="+",
        default=[],
        help="File extensions to count (default: common source extensions)",
    )
    parser.add_argument(
        "--no-default-exts",
        action="store_true",
        help="Do NOT use the default extensions",
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Count lines in ALL files (ignore extension filtering)",
    )
    parser.add_argument(
        "--skip-blank",
        action="store_true",
        help="Exclude blank/whitespace-only lines from the count",
    )
    parser.add_argument(
        "--skip-comments",
        action="store_true",
        help="Exclude comment lines (basic support for common languages)",
    )
    parser.add_argument(
        "--skip-binary",
        action="store_true",
        help="Skip files that appear to be binary (contain null bytes)",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        metavar="MB",
        default=10,
        help="Skip files larger than this size in MB (default: 10)",
    )
    parser.add_argument(
        "--case-sensitive-skip",
        action="store_true",
        help="Match skipped directory names exactly (default is case-insensitive)",
    )
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follow symbolic links when walking directories",
    )
    parser.add_argument(
        "--progress", action="store_true", help="Show a progress counter while scanning"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show each file as it is processed"
    )
    parser.add_argument(
        "--include-empty-files",
        action="store_true",
        help="Include files with zero lines in the file count",
    )
    parser.add_argument(
        "--top",
        type=int,
        metavar="N",
        default=10,
        help="Show top N file types (default: 10, use 0 for all)",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    # Build the set of directories to skip
    skip_dirs = set()
    if not args.no_default_skips:
        skip_dirs.update(DEFAULT_SKIP_DIRS)
    skip_dirs.update(args.skip_dirs)

    # Build the set of extensions to count
    extensions = set()
    if not args.no_default_exts and not args.include_all:
        extensions.update(DEFAULT_EXTENSIONS)
    extensions.update(
        f".{'ext' if not ext.startswith('.') else ext.lstrip('.')}"
        for ext in args.extensions
    )

    root_dir = Path(args.directory).resolve()
    if not root_dir.is_dir():
        print(f"Error: {root_dir} is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    # Update max file size
    global MAX_FILE_SIZE
    MAX_FILE_SIZE = args.max_size * 1024 * 1024

    total_lines = 0
    total_files = 0
    total_files_with_lines = 0
    total_size = 0
    skipped_binary = 0
    skipped_large = 0
    skipped_extension = 0
    errors = 0

    ext_counter = defaultdict(lambda: {"lines": 0, "files": 0})
    file_details = []

    start_time = time.time()
    last_progress_time = start_time

    print(f"Scanning: {root_dir}", file=sys.stderr)
    print(f"Skipping directories: {', '.join(sorted(skip_dirs))}", file=sys.stderr)
    if not args.include_all:
        print(f"File extensions: {', '.join(sorted(extensions))}", file=sys.stderr)
    print(file=sys.stderr)

    try:
        for dirpath, dirnames, filenames in os.walk(
            root_dir, followlinks=args.follow_symlinks
        ):
            # Filter directories in-place
            dirnames[:] = [
                d
                for d in dirnames
                if not should_skip_dir(d, skip_dirs, args.case_sensitive_skip)
            ]

            for filename in filenames:
                file_path = Path(dirpath) / filename

                # Progress reporting
                if args.progress or args.verbose:
                    current_time = time.time()
                    if args.verbose:
                        print(
                            f"Processing: {file_path.relative_to(root_dir)}",
                            file=sys.stderr,
                        )
                    elif args.progress and current_time - last_progress_time >= 1.0:
                        elapsed = current_time - start_time
                        rate = total_files / elapsed if elapsed > 0 else 0
                        print(
                            f"  {format_number(total_files)} files, {format_number(total_lines)} lines "
                            f"({rate:.0f} files/sec)",
                            file=sys.stderr,
                        )
                        last_progress_time = current_time

                try:
                    file_size = file_path.stat().st_size
                except OSError:
                    errors += 1
                    continue

                # Skip files too large
                if file_size > MAX_FILE_SIZE:
                    skipped_large += 1
                    if args.verbose:
                        print(f"  SKIPPED (too large): {file_path}", file=sys.stderr)
                    continue

                # Skip binary files if requested
                if args.skip_binary and is_binary(file_path):
                    skipped_binary += 1
                    if args.verbose:
                        print(f"  SKIPPED (binary): {file_path}", file=sys.stderr)
                    continue

                # Extension filtering (unless include_all)
                if not args.include_all:
                    ext = file_path.suffix.lower()
                    if ext not in extensions:
                        skipped_extension += 1
                        continue

                # Count lines
                comment_patterns = (
                    get_comment_patterns(file_path.suffix.lower())
                    if args.skip_comments
                    else None
                )
                lines = count_lines_in_file(
                    file_path,
                    skip_blank=args.skip_blank,
                    skip_comments=args.skip_comments,
                    comment_patterns=comment_patterns,
                )

                # Track file
                if args.include_empty_files or lines > 0:
                    total_files += 1
                    total_size += file_size

                if lines > 0:
                    total_lines += lines
                    total_files_with_lines += 1
                    ext = file_path.suffix.lower() or "(no extension)"
                    ext_counter[ext]["lines"] += lines
                    ext_counter[ext]["files"] += 1

                    if args.verbose:
                        file_details.append(
                            (str(file_path.relative_to(root_dir)), lines, file_size)
                        )

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)

    elapsed = time.time() - start_time

    # Output results
    if args.output_format == "json":
        import json

        result = {
            "directory": str(root_dir),
            "total_files": total_files,
            "total_files_with_lines": total_files_with_lines,
            "total_lines": total_lines,
            "total_size_bytes": total_size,
            "elapsed_seconds": elapsed,
            "skipped": {
                "binary": skipped_binary,
                "large_files": skipped_large,
                "by_extension": skipped_extension,
            },
            "by_extension": dict(ext_counter),
        }
        print(json.dumps(result, indent=2))
    else:
        # Text output
        print()
        print(f"Codebase: {root_dir}")
        print(f"Scan time: {elapsed:.2f} seconds")
        print()
        print(f"Total files: {format_number(total_files)}")
        print(f"Files with content: {format_number(total_files_with_lines)}")
        print(f"Total lines: {format_number(total_lines)}")
        print(f"Total size: {format_size(total_size)}")

        if args.skip_blank:
            print("  (blank lines excluded)")
        if args.skip_comments:
            print("  (comment lines excluded)")

        print()

        if skipped_binary > 0 or skipped_large > 0 or skipped_extension > 0:
            print("Skipped:")
            if skipped_binary > 0:
                print(f"  Binary files: {format_number(skipped_binary)}")
            if skipped_large > 0:
                print(
                    f"  Large files (> {args.max_size}MB): {format_number(skipped_large)}"
                )
            if skipped_extension > 0:
                print(
                    f"  Files by extension filter: {format_number(skipped_extension)}"
                )
            print()

        if ext_counter:
            print("Breakdown by extension:")

            # Sort by lines
            sorted_exts = sorted(
                ext_counter.items(), key=lambda x: x[1]["lines"], reverse=True
            )

            # Limit if requested
            if args.top > 0:
                sorted_exts = sorted_exts[: args.top]
                if len(ext_counter) > args.top:
                    print(f"  (showing top {args.top} of {len(ext_counter)} types)")

            # Calculate column widths
            max_ext_len = max(len(ext) for ext, _ in sorted_exts)
            max_lines = (
                max(data["lines"] for _, data in sorted_exts) if sorted_exts else 0
            )
            max_files = (
                max(data["files"] for _, data in sorted_exts) if sorted_exts else 0
            )
            lines_width = len(format_number(max_lines))
            files_width = len(format_number(max_files))

            # Print header
            print(
                f"  {'Extension':<{max_ext_len}}  {'Files':>{files_width}}  {'Lines':>{lines_width}}  Percentage"
            )
            print(
                f"  {'-' * max_ext_len}  {'-' * files_width}  {'-' * lines_width}  ----------"
            )

            # Print rows
            for ext, data in sorted_exts:
                lines = data["lines"]
                files = data["files"]
                percentage = (lines / total_lines * 100) if total_lines > 0 else 0
                print(
                    f"  {ext:<{max_ext_len}}  {format_number(files):>{files_width}}  {format_number(lines):>{lines_width}}  {percentage:6.2f}%"
                )

            print()

        # Show file details if verbose
        if args.verbose and file_details:
            print("\nTop 20 files by line count:")
            file_details.sort(key=lambda x: x[1], reverse=True)
            for filepath, lines, size in file_details[:20]:
                print(f"  {lines:>8} lines  {format_size(size):>10}  {filepath}")
            print()

        print("Done.")


if __name__ == "__main__":
    main()
