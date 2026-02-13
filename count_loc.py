#!/usr/bin/env python3
"""
Count lines of code in a codebase, skipping specified directories.
Now with better binary detection, optional blank-line skipping, and case‑insensitive skip.
"""

import os
import sys
import argparse
import time
from collections import defaultdict
from pathlib import Path

# Default directories to skip (add or remove as needed)
DEFAULT_SKIP_DIRS = {
    'node_modules', 'venv', 'env', '.venv', '.env',
    '.git', '__pycache__', 'dist', 'build', '.idea', '.vscode'
}

# Default file extensions to consider as source code
DEFAULT_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h',
    '.hpp', '.cs', '.go', '.rb', '.php', '.swift', '.kt', '.rs',
    '.html', '.htm', '.css', '.scss', '.sass', '.less',
    '.xml', '.json', '.yml', '.yaml', '.md', '.rst', '.txt',
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd'
}

# Chunk size for binary detection
BINARY_CHECK_SIZE = 1024


def is_binary(file_path):
    """Return True if the file appears to be binary (contains null bytes)."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(BINARY_CHECK_SIZE)
            return b'\0' in chunk
    except (IOError, OSError):
        return False  # if we can't read, assume not binary (will be handled later)


def count_lines_in_file(file_path, skip_blank=False):
    """Return number of lines in a text file. If skip_blank, ignore lines with only whitespace."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            if skip_blank:
                return sum(1 for line in f if line.strip())
            else:
                return sum(1 for _ in f)
    except (IOError, OSError):
        return 0


def main():
    parser = argparse.ArgumentParser(
        description='Count lines of code in a codebase, skipping common junk directories.'
    )
    parser.add_argument(
        'directory', nargs='?', default='.',
        help='Root directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--skip-dirs', metavar='DIR', nargs='+', default=[],
        help='Additional directory names to skip (case‑insensitive matching)'
    )
    parser.add_argument(
        '--no-default-skips', action='store_true',
        help='Do NOT use the default skip directories'
    )
    parser.add_argument(
        '--extensions', metavar='EXT', nargs='+', default=[],
        help='File extensions to count (default: common source extensions)'
    )
    parser.add_argument(
        '--no-default-exts', action='store_true',
        help='Do NOT use the default extensions'
    )
    parser.add_argument(
        '--include-all', action='store_true',
        help='Count lines in ALL files (ignore extension filtering)'
    )
    parser.add_argument(
        '--skip-blank', action='store_true',
        help='Exclude blank/whitespace‑only lines from the count'
    )
    parser.add_argument(
        '--skip-binary', action='store_true',
        help='Skip files that appear to be binary (contain null bytes)'
    )
    parser.add_argument(
        '--case-sensitive-skip', action='store_true',
        help='Match skipped directory names exactly (default is case‑insensitive)'
    )
    parser.add_argument(
        '--follow-symlinks', action='store_true',
        help='Follow symbolic links when walking directories'
    )
    parser.add_argument(
        '--progress', action='store_true',
        help='Show a progress counter while scanning'
    )
    parser.add_argument(
        '--include-empty-files', action='store_true',
        help='Include files with zero lines in the file count'
    )
    args = parser.parse_args()

    # Build the set of directories to skip
    skip_dirs = set()
    if not args.no_default_skips:
        skip_dirs.update(DEFAULT_SKIP_DIRS)
    skip_dirs.update(args.skip_dirs)  # user‑supplied extras

    # Build the set of extensions to count
    extensions = set()
    if not args.no_default_exts and not args.include_all:
        extensions.update(DEFAULT_EXTENSIONS)
    extensions.update(args.extensions)  # user‑supplied extras

    root_dir = Path(args.directory).resolve()
    if not root_dir.is_dir():
        print(f"Error: {root_dir} is not a valid directory.")
        sys.exit(1)

    # Prepare for case‑insensitive matching if needed
    if args.case_sensitive_skip:
        def skip_match(d):
            return d in skip_dirs
    else:
        skip_dirs_lower = {d.lower() for d in skip_dirs}
        def skip_match(d):
            return d.lower() in skip_dirs_lower

    total_lines = 0
    total_files = 0
    total_files_with_lines = 0
    ext_counter = defaultdict(int)
    file_count = 0
    start_time = time.time()

    for dirpath, dirnames, filenames in os.walk(
        root_dir, followlinks=args.follow_symlinks
    ):
        # Filter directories in‑place
        dirnames[:] = [d for d in dirnames if not skip_match(d)]

        for filename in filenames:
            file_path = Path(dirpath) / filename

            if args.progress:
                file_count += 1
                if file_count % 1000 == 0:
                    elapsed = time.time() - start_time
                    print(f"  Progress: {file_count} files scanned, "
                          f"{total_lines} lines so far ({elapsed:.1f}s)", file=sys.stderr)

            # Skip binary files if requested
            if args.skip_binary and is_binary(file_path):
                continue

            # Extension filtering (unless include_all)
            if not args.include_all:
                ext = file_path.suffix.lower()
                if ext not in extensions:
                    continue

            lines = count_lines_in_file(file_path, skip_blank=args.skip_blank)

            # Always increment total_files if we considered the file (even 0 lines)
            if args.include_empty_files or lines > 0:
                total_files += 1

            if lines > 0:
                total_lines += lines
                total_files_with_lines += 1
                ext = file_path.suffix.lower()
                ext_counter[ext] += lines

    # Print results
    print(f"\nCodebase: {root_dir}")
    print(f"Total files considered: {total_files}")
    if args.include_empty_files:
        print(f"  (of which {total_files_with_lines} contain at least one line)")
    print(f"Total lines of code: {total_lines}")
    if args.skip_blank:
        print("  (blank lines excluded)")

    if ext_counter:
        print("\nBreakdown by extension:")
        for ext in sorted(ext_counter, key=ext_counter.get, reverse=True):
            display_ext = ext or '(no extension)'
            print(f"  {display_ext}: {ext_counter[ext]} lines")

    elapsed = time.time() - start_time
    print(f"\nDone in {elapsed:.2f} seconds.")


if __name__ == '__main__':
    main()