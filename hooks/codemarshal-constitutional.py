#!/usr/bin/env python3
"""
CodeMarshal Pre-commit Hook

Detects constitutional violations before commit.
Usage: python hooks/codemarshal-constitutional.py [--strict] [--report {text,json}] [filenames...]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_codemarshal_check(files=None):
    """Run CodeMarshal pattern scan on staged files."""
    cmd = [sys.executable, "-m", "bridge.entry.cli", "pattern", "scan"]

    if files:
        # Scan specific files
        for f in files:
            cmd.extend(["--glob", f"*{Path(f).suffix}"])

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="CodeMarshal Pre-commit Hook - Detects constitutional violations"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Exit with error code if violations found"
    )
    parser.add_argument(
        "--report", choices=["text", "json"], default="text", help="Report format"
    )
    parser.add_argument("filenames", nargs="*", help="Specific files to check")

    args = parser.parse_args()

    print("🔍 Running CodeMarshal Constitutional Check...")
    print()

    # Run pattern scan
    result = run_codemarshal_check(args.filenames)

    if result.returncode != 0 and "No patterns selected" not in result.stderr:
        print("❌ CodeMarshal check failed:")
        print(result.stderr)
        return 1

    # Parse and report violations
    if args.report == "json":
        # Try to parse JSON output
        try:
            data = json.loads(result.stdout)
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError:
            print(result.stdout)
    else:
        # Text report
        if result.stdout.strip():
            print("🚨 Constitutional Violations Detected:\n")
            print(result.stdout)
            print()
            print("⚠️  Please fix these issues before committing.")
            if args.strict:
                return 1
        else:
            print("✅ No constitutional violations detected!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
