"""
bridge.commands.pattern - Pattern detection CLI command

This module provides the pattern command for running custom pattern detectors.

Command:
- pattern: List, add, search, apply, create, and share pattern detectors
"""

from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from patterns.collector import PatternCollector
from patterns.loader import (
    PatternDefinition,
    PatternLoader,
    PatternManager,
    PatternScanner,
)
from patterns.marketplace import PatternMarketplace
from patterns.templates import PatternTemplateRegistry


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


@dataclass
class PatternSearchCommandResult:
    """Result of marketplace pattern search."""

    success: bool
    total_count: int
    patterns: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""
    error: str | None = None


@dataclass
class PatternApplyResult:
    """Result of applying one marketplace pattern and scanning target files."""

    success: bool
    pattern_id: str = ""
    installed: bool = False
    patterns_scanned: int = 0
    files_scanned: int = 0
    matches_found: int = 0
    matches: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    scan_time_ms: float = 0.0
    message: str = ""
    error: str | None = None


@dataclass
class PatternCreateResult:
    """Result of creating a pattern from a template."""

    success: bool
    template_id: str = ""
    pattern_id: str = ""
    created: bool = False
    installed: bool = False
    dry_run: bool = False
    submission_id: str = ""
    validation_errors: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)
    output_path: str | None = None
    pattern: dict[str, Any] | None = None
    message: str = ""
    error: str | None = None


@dataclass
class PatternShareResult:
    """Result of sharing a pattern as a local bundle."""

    success: bool
    pattern_id: str = ""
    package_id: str = ""
    path: str = ""
    version: str = ""
    created_at: str = ""
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
        context_lines: int = 2,
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
            scanner = PatternScanner(context_lines=context_lines)

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
                        "context_before": match.context_before,
                        "context_after": match.context_after,
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


class PatternSearchCommand:
    """Search local marketplace patterns."""

    def execute(
        self,
        query: str = "",
        tags: list[str] | None = None,
        severity: str | None = None,
        language: str | None = None,
        limit: int = 20,
        storage_root: Path | str = Path("storage"),
    ) -> PatternSearchCommandResult:
        """Execute marketplace search."""
        try:
            marketplace = PatternMarketplace(storage_root=storage_root)
            result = marketplace.search(
                query=query,
                tags=tags,
                severity=severity,
                language=language,
                limit=max(int(limit), 0),
            )
            payload = [asdict(item) for item in result.results]
            return PatternSearchCommandResult(
                success=result.success,
                total_count=result.total_count,
                patterns=payload,
                message=result.message,
                error=result.error,
            )
        except Exception as e:
            return PatternSearchCommandResult(
                success=False,
                total_count=0,
                patterns=[],
                error=f"Marketplace search failed: {e}",
            )


class PatternApplyCommand:
    """Install/apply a marketplace pattern then scan target path."""

    def execute(
        self,
        pattern_ref: str,
        path: Path,
        glob: str = "*",
        max_files: int = 10000,
        storage_root: Path | str = Path("storage"),
    ) -> PatternApplyResult:
        """Execute apply command."""
        try:
            marketplace = PatternMarketplace(storage_root=storage_root)
            install_result = marketplace.install(pattern_ref=pattern_ref)
            if not install_result.get("success", False):
                return PatternApplyResult(
                    success=False,
                    error=str(install_result.get("error") or "Install failed"),
                )

            selected_pattern_id = str(install_result.get("pattern_id") or pattern_ref)
            scan_result = PatternScanCommand().execute(
                path=path,
                patterns=[selected_pattern_id],
                glob=glob,
                max_files=max_files,
            )
            if not scan_result.success:
                return PatternApplyResult(
                    success=False,
                    pattern_id=selected_pattern_id,
                    installed=bool(install_result.get("installed", False)),
                    patterns_scanned=scan_result.patterns_scanned,
                    files_scanned=scan_result.files_scanned,
                    matches_found=scan_result.matches_found,
                    matches=scan_result.matches,
                    errors=scan_result.errors,
                    scan_time_ms=scan_result.scan_time_ms,
                    message=scan_result.message,
                    error=scan_result.error,
                )

            return PatternApplyResult(
                success=True,
                pattern_id=selected_pattern_id,
                installed=bool(install_result.get("installed", False)),
                patterns_scanned=scan_result.patterns_scanned,
                files_scanned=scan_result.files_scanned,
                matches_found=scan_result.matches_found,
                matches=scan_result.matches,
                errors=scan_result.errors,
                scan_time_ms=scan_result.scan_time_ms,
                message=str(install_result.get("message") or "Pattern applied"),
            )
        except Exception as e:
            return PatternApplyResult(success=False, error=f"Apply failed: {e}")


class PatternCreateCommand:
    """Create a custom pattern from a template."""

    def execute(
        self,
        template_id: str,
        values: dict[str, str] | None = None,
        *,
        pattern_id: str | None = None,
        name: str | None = None,
        description: str = "",
        severity: str | None = None,
        tags: list[str] | None = None,
        languages: list[str] | None = None,
        dry_run: bool = False,
        output_path: Path | str | None = None,
        submitter: str = "local",
        source: str = "template",
        notes: str = "",
        storage_root: Path | str = Path("storage"),
    ) -> PatternCreateResult:
        """Execute create command."""
        try:
            registry = PatternTemplateRegistry()
            rendered = registry.render_pattern(
                template_id=template_id,
                values=values or {},
                pattern_id=pattern_id,
                name=name,
                description=description or None,
                severity=severity,
                tags=tags,
                languages=languages,
            )
            collector = PatternCollector(storage_root=storage_root)
            submission, report = collector.submit_local(
                rendered.pattern,
                submitter=submitter,
                source=source,
                notes=notes,
            )
            if not report.valid:
                return PatternCreateResult(
                    success=False,
                    template_id=rendered.template_id,
                    pattern_id=rendered.pattern.id,
                    dry_run=dry_run,
                    created=False,
                    installed=False,
                    submission_id=submission.submission_id,
                    validation_errors=report.errors,
                    validation_warnings=report.warnings,
                    pattern=asdict(rendered.pattern),
                    error="Validation failed",
                )

            if dry_run:
                return PatternCreateResult(
                    success=True,
                    template_id=rendered.template_id,
                    pattern_id=rendered.pattern.id,
                    dry_run=True,
                    created=False,
                    installed=False,
                    submission_id=submission.submission_id,
                    validation_warnings=report.warnings,
                    pattern=asdict(rendered.pattern),
                    message="Dry-run successful; pattern not installed",
                )

            manager = PatternManager()
            installed = manager.add_custom_pattern(rendered.pattern)
            if not installed:
                return PatternCreateResult(
                    success=False,
                    template_id=rendered.template_id,
                    pattern_id=rendered.pattern.id,
                    dry_run=False,
                    created=False,
                    installed=False,
                    submission_id=submission.submission_id,
                    pattern=asdict(rendered.pattern),
                    error="Failed to install generated pattern",
                )

            collector.curate(
                submission,
                approve=True,
                reason="Auto-approved local template creation",
                labels=["auto", "local"],
            )

            output_file: str | None = None
            if output_path is not None:
                marketplace = PatternMarketplace(storage_root=storage_root)
                package = marketplace.share(
                    rendered.pattern.id,
                    bundle_out=output_path,
                    include_examples=False,
                )
                output_file = package.path

            return PatternCreateResult(
                success=True,
                template_id=rendered.template_id,
                pattern_id=rendered.pattern.id,
                created=True,
                installed=True,
                dry_run=False,
                submission_id=submission.submission_id,
                validation_warnings=report.warnings,
                output_path=output_file,
                pattern=asdict(rendered.pattern),
                message="Pattern created successfully",
            )
        except Exception as e:
            return PatternCreateResult(
                success=False,
                error=f"Create failed: {e}",
            )


class PatternShareCommand:
    """Share a pattern as a local package bundle."""

    def execute(
        self,
        pattern_id: str,
        *,
        bundle_out: Path | str | None = None,
        include_examples: bool = False,
        storage_root: Path | str = Path("storage"),
    ) -> PatternShareResult:
        """Execute share command."""
        try:
            marketplace = PatternMarketplace(storage_root=storage_root)
            package = marketplace.share(
                pattern_id=pattern_id,
                bundle_out=bundle_out,
                include_examples=include_examples,
            )
            return PatternShareResult(
                success=True,
                pattern_id=package.pattern_id,
                package_id=package.package_id,
                path=package.path,
                version=package.version,
                created_at=package.created_at,
                message="Pattern bundle created",
            )
        except Exception as e:
            return PatternShareResult(success=False, error=f"Share failed: {e}")


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
    context_lines: int = 2,
) -> PatternScanCommandResult:
    """Convenience function for pattern scan."""
    cmd = PatternScanCommand()
    return cmd.execute(
        path, patterns, category, glob, output_format, max_files, context_lines
    )


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


def execute_pattern_search(
    query: str = "",
    tags: list[str] | None = None,
    severity: str | None = None,
    language: str | None = None,
    limit: int = 20,
    storage_root: Path | str = Path("storage"),
) -> PatternSearchCommandResult:
    """Convenience function for pattern marketplace search."""
    cmd = PatternSearchCommand()
    return cmd.execute(
        query=query,
        tags=tags,
        severity=severity,
        language=language,
        limit=limit,
        storage_root=storage_root,
    )


def execute_pattern_apply(
    pattern_ref: str,
    path: Path,
    glob: str = "*",
    max_files: int = 10000,
    storage_root: Path | str = Path("storage"),
) -> PatternApplyResult:
    """Convenience function for applying and scanning one pattern."""
    cmd = PatternApplyCommand()
    return cmd.execute(
        pattern_ref=pattern_ref,
        path=path,
        glob=glob,
        max_files=max_files,
        storage_root=storage_root,
    )


def execute_pattern_create(
    template_id: str,
    values: dict[str, str] | None = None,
    *,
    pattern_id: str | None = None,
    name: str | None = None,
    description: str = "",
    severity: str | None = None,
    tags: list[str] | None = None,
    languages: list[str] | None = None,
    dry_run: bool = False,
    output_path: Path | str | None = None,
    submitter: str = "local",
    source: str = "template",
    notes: str = "",
    storage_root: Path | str = Path("storage"),
) -> PatternCreateResult:
    """Convenience function for creating a pattern from template."""
    cmd = PatternCreateCommand()
    return cmd.execute(
        template_id=template_id,
        values=values,
        pattern_id=pattern_id,
        name=name,
        description=description,
        severity=severity,
        tags=tags,
        languages=languages,
        dry_run=dry_run,
        output_path=output_path,
        submitter=submitter,
        source=source,
        notes=notes,
        storage_root=storage_root,
    )


def execute_pattern_share(
    pattern_id: str,
    *,
    bundle_out: Path | str | None = None,
    include_examples: bool = False,
    storage_root: Path | str = Path("storage"),
) -> PatternShareResult:
    """Convenience function for sharing a local pattern bundle."""
    cmd = PatternShareCommand()
    return cmd.execute(
        pattern_id=pattern_id,
        bundle_out=bundle_out,
        include_examples=include_examples,
        storage_root=storage_root,
    )
