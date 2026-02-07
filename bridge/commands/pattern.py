"""
bridge.commands.pattern - Pattern detection CLI command

This module provides the pattern command for running custom pattern detectors.

Command:
- pattern: List, add, and run pattern detectors
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from patterns.loader import (
    PatternDefinition,
    PatternLoader,
    PatternManager,
    PatternScanner,
)


@dataclass
class PatternListResult:
    """Result of pattern list command."""

    success: bool
    patterns: list[PatternDefinition]
    total_count: int
    message: str = ""
    error: str | None = None


@dataclass
class PatternScanCommandResult:
    """Result of pattern scan command."""

    success: bool
    patterns_scanned: int
    files_scanned: int
    matches_found: int
    matches: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    scan_time_ms: float = 0.0
    message: str = ""
    error: str | None = None


@dataclass
class PatternAddResult:
    """Result of pattern add command."""

    success: bool
    pattern_id: str = ""
    message: str = ""
    error: str | None = None


class PatternListCommand:
    """List available patterns."""

    def execute(
        self,
        category: str | None = None,
        show_disabled: bool = False,
        output_format: str = "table",
    ) -> PatternListResult:
        """
        Execute pattern list command.

        Args:
            category: Filter by category (security, performance, style)
            show_disabled: Include disabled patterns
            output_format: Output format (table, json)

        Returns:
            PatternListResult with pattern list
        """
        try:
            loader = PatternLoader()

            if category:
                patterns = loader.load_builtin_patterns(category)
            else:
                patterns = loader.load_all_patterns()

            # Filter disabled patterns unless requested
            if not show_disabled:
                patterns = [p for p in patterns if p.enabled]

            return PatternListResult(
                success=True,
                patterns=patterns,
                total_count=len(patterns),
                message=f"Found {len(patterns)} pattern(s)",
            )

        except Exception as e:
            return PatternListResult(
                success=False,
                patterns=[],
                total_count=0,
                error=f"Failed to list patterns: {e}",
            )


class PatternScanCommand:
    """Scan code for pattern matches."""

    def execute(
        self,
        path: Path,
        patterns: list[str] | None = None,
        category: str | None = None,
        glob: str = "*",
        output_format: str = "table",
        max_files: int = 10000,
    ) -> PatternScanCommandResult:
        """
        Execute pattern scan command.

        Args:
            path: Directory or file to scan
            patterns: Specific pattern IDs to run (None = all)
            category: Run all patterns in category
            glob: File glob pattern
            output_format: Output format (table, json)
            max_files: Maximum files to scan

        Returns:
            PatternScanCommandResult with scan results
        """
        try:
            loader = PatternLoader()
            scanner = PatternScanner()

            # Load patterns to scan
            if patterns:
                # Load specific patterns
                all_patterns = loader.load_all_patterns()
                patterns_to_scan = [p for p in all_patterns if p.id in patterns]
            elif category:
                patterns_to_scan = loader.load_builtin_patterns(category)
            else:
                patterns_to_scan = loader.load_all_patterns()

            if not patterns_to_scan:
                return PatternScanCommandResult(
                    success=False,
                    patterns_scanned=0,
                    files_scanned=0,
                    matches_found=0,
                    message="No patterns selected",
                )

            # Run scan
            result = scanner.scan(path, patterns_to_scan, glob, max_files)

            if not result.success:
                return PatternScanCommandResult(
                    success=False,
                    patterns_scanned=len(patterns_to_scan),
                    files_scanned=0,
                    matches_found=0,
                    errors=result.errors,
                    message="Scan failed",
                )

            # Convert matches to dict for output
            matches_dict = []
            for match in result.matches:
                matches_dict.append(
                    {
                        "pattern_id": match.pattern_id,
                        "pattern_name": match.pattern_name,
                        "file": str(match.file_path),
                        "line": match.line_number,
                        "content": match.line_content,
                        "matched": match.matched_text,
                        "severity": match.severity,
                        "message": match.message,
                        "description": match.description,
                        "tags": match.tags,
                    }
                )

            return PatternScanCommandResult(
                success=True,
                patterns_scanned=result.patterns_scanned,
                files_scanned=result.files_scanned,
                matches_found=len(result.matches),
                matches=matches_dict,
                errors=result.errors,
                scan_time_ms=result.scan_time_ms,
                message=f"Found {len(result.matches)} matches in {result.files_scanned} files",
            )

        except Exception as e:
            return PatternScanCommandResult(
                success=False,
                patterns_scanned=0,
                files_scanned=0,
                matches_found=0,
                message=f"Scan error: {e}",
            )


class PatternAddCommand:
    """Add a custom pattern."""

    def execute(
        self,
        pattern_id: str,
        name: str,
        pattern: str,
        severity: str = "warning",
        description: str = "",
        message: str = "",
        tags: list[str] | None = None,
        languages: list[str] | None = None,
    ) -> PatternAddResult:
        """
        Execute pattern add command.

        Args:
            pattern_id: Unique pattern identifier
            name: Human-readable name
            pattern: Regex pattern
            severity: critical, warning, or info
            description: Pattern description
            message: Message template
            tags: List of tags
            languages: Target languages

        Returns:
            PatternAddResult with result
        """
        try:
            # Validate pattern
            import re

            try:
                re.compile(pattern)
            except re.error as e:
                return PatternAddResult(
                    success=False, error=f"Invalid regex pattern: {e}"
                )

            pattern_def = PatternDefinition(
                id=pattern_id,
                name=name,
                pattern=pattern,
                severity=severity,
                description=description,
                message=message or f"{name} detected",
                tags=tags or [],
                languages=languages or [],
                enabled=True,
            )

            manager = PatternManager()
            success = manager.add_custom_pattern(pattern_def)

            if success:
                return PatternAddResult(
                    success=True,
                    pattern_id=pattern_id,
                    message=f"Pattern '{pattern_id}' added successfully",
                )
            else:
                return PatternAddResult(success=False, error="Failed to save pattern")

        except Exception as e:
            return PatternAddResult(success=False, error=f"Error adding pattern: {e}")


# Convenience functions
def execute_pattern_list(
    category: str | None = None,
    show_disabled: bool = False,
    output_format: str = "table",
) -> PatternListResult:
    """Convenience function for pattern list."""
    cmd = PatternListCommand()
    return cmd.execute(category, show_disabled, output_format)


def execute_pattern_scan(
    path: Path,
    patterns: list[str] | None = None,
    category: str | None = None,
    glob: str = "*",
    output_format: str = "table",
    max_files: int = 10000,
) -> PatternScanCommandResult:
    """Convenience function for pattern scan."""
    cmd = PatternScanCommand()
    return cmd.execute(path, patterns, category, glob, output_format, max_files)


def execute_pattern_add(
    pattern_id: str,
    name: str,
    pattern: str,
    severity: str = "warning",
    description: str = "",
    message: str = "",
    tags: list[str] | None = None,
    languages: list[str] | None = None,
) -> PatternAddResult:
    """Convenience function for pattern add."""
    cmd = PatternAddCommand()
    return cmd.execute(
        pattern_id, name, pattern, severity, description, message, tags, languages
    )
