"""
patterns/engine.py - Advanced pattern detection helpers.

Provides context-aware detection, statistical outlier detection,
and optional fix suggestions for matched patterns.
"""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from patterns.loader import (
    PatternDefinition,
    PatternLoader,
    PatternMatch,
    PatternManager,
    PatternScanner,
)
from patterns.marketplace import PatternMarketplace
from patterns.templates import PatternTemplateRegistry


@dataclass(frozen=True)
class StatisticalAnomaly:
    """Statistical outlier for a pattern's match counts."""

    pattern_id: str
    pattern_name: str
    file_path: Path
    match_count: int
    mean: float
    standard_deviation: float
    z_score: float

    @property
    def direction(self) -> str:
        """Whether the outlier is above or below the mean."""
        return "high" if self.z_score >= 0 else "low"


@dataclass(frozen=True)
class FixSuggestion:
    """Optional fix suggestion for a pattern match."""

    pattern_id: str
    title: str
    description: str
    confidence: float = 0.4
    file_path: Path | None = None
    line_number: int | None = None


class PatternEngine:
    """Advanced pattern detection with context awareness."""

    _SUGGESTION_MAP: dict[str, tuple[str, str, float]] = {
        "nested_loop_n2": (
            "Reduce nested loops",
            "Consider precomputing lookups or merging loops to reduce complexity.",
            0.45,
        ),
        "nested_loop_n3": (
            "Flatten triple nested loops",
            "Look for opportunities to batch or restructure logic.",
            0.4,
        ),
        "large_function": (
            "Split large function",
            "Refactor into smaller functions with clear responsibilities.",
            0.4,
        ),
        "sync_io_loop": (
            "Batch or async I/O",
            "Move blocking I/O outside loops or use async batching.",
            0.45,
        ),
        "n_plus_one": (
            "Use eager loading",
            "Fetch related data in bulk to avoid N+1 queries.",
            0.45,
        ),
        "range_len_loop": (
            "Use enumerate",
            "Replace range(len(...)) with enumerate for clarity and safety.",
            0.35,
        ),
        "mutable_default": (
            "Avoid mutable defaults",
            "Use None as the default and initialize inside the function.",
            0.5,
        ),
        "bare_except": (
            "Catch explicit exceptions",
            "Replace bare except with specific exception types.",
            0.4,
        ),
        "cross_layer_import": (
            "Introduce boundary interface",
            "Insert an adapter or interface layer between architectural tiers.",
            0.45,
        ),
        "god_class": (
            "Decompose large class",
            "Split responsibilities into smaller, cohesive classes.",
            0.4,
        ),
    }

    def __init__(
        self,
        patterns_dir: Path | None = None,
        context_lines: int = 2,
        max_workers: int = 4,
    ) -> None:
        self.loader = PatternLoader(patterns_dir)
        self.context_lines = context_lines
        self.max_workers = max_workers

    def detect_with_context(
        self, file_path: Path, pattern: PatternDefinition
    ) -> list[PatternMatch]:
        """Detect a pattern with surrounding code context."""
        scanner = PatternScanner(
            max_workers=self.max_workers, context_lines=self.context_lines
        )
        result = scanner.scan(file_path, [pattern], max_files=1)
        if not result.success:
            return []
        return result.matches

    def detect_statistical_outliers(
        self,
        codebase: Path,
        patterns: list[PatternDefinition] | None = None,
        glob: str = "*",
        max_files: int = 10000,
        z_threshold: float = 2.5,
    ) -> list[StatisticalAnomaly]:
        """Find statistically unusual patterns using z-score analysis."""
        if patterns is None:
            patterns = self.loader.load_all_patterns()

        if not patterns:
            return []

        scanner = PatternScanner(
            max_workers=self.max_workers, context_lines=self.context_lines
        )
        result = scanner.scan(codebase, patterns, glob, max_files)
        if not result.success or not result.matches:
            return []

        counts_by_pattern: dict[str, Counter[Path]] = defaultdict(Counter)
        for match in result.matches:
            counts_by_pattern[match.pattern_id][match.file_path] += 1

        pattern_lookup = {pattern.id: pattern for pattern in patterns}
        anomalies: list[StatisticalAnomaly] = []

        for pattern_id, file_counts in counts_by_pattern.items():
            values = list(file_counts.values())
            if len(values) < 2:
                continue

            mean = statistics.mean(values)
            stdev = statistics.pstdev(values)
            if stdev == 0:
                continue

            for file_path, count in file_counts.items():
                z_score = (count - mean) / stdev
                if abs(z_score) < z_threshold:
                    continue

                pattern_def = pattern_lookup.get(pattern_id, None)
                anomalies.append(
                    StatisticalAnomaly(
                        pattern_id=pattern_id,
                        pattern_name=pattern_def.name
                        if pattern_def is not None
                        else pattern_id,
                        file_path=file_path,
                        match_count=count,
                        mean=mean,
                        standard_deviation=stdev,
                        z_score=z_score,
                    )
                )

        return sorted(anomalies, key=lambda a: abs(a.z_score), reverse=True)

    def search_marketplace_patterns(
        self,
        query: str,
        *,
        tags: list[str] | None = None,
        severity: str | None = None,
        language: str | None = None,
        limit: int = 20,
        storage_root: Path | str = Path("storage"),
    ) -> list[dict[str, Any]]:
        """Search local marketplace entries."""
        marketplace = PatternMarketplace(storage_root=storage_root)
        result = marketplace.search(
            query=query,
            tags=tags,
            severity=severity,
            language=language,
            limit=limit,
        )
        return [
            {
                "pattern_id": item.pattern_id,
                "name": item.name,
                "description": item.description,
                "severity": item.severity,
                "tags": item.tags,
                "languages": item.languages,
                "version": item.version,
                "source": item.source,
                "installed": item.installed,
                "rating": {
                    "average_rating": item.rating.average_rating,
                    "total_reviews": item.rating.total_reviews,
                },
            }
            for item in result.results
        ]

    def apply_pattern(
        self,
        pattern_ref: str,
        target_path: Path,
        *,
        glob: str = "*",
        max_files: int = 10000,
        storage_root: Path | str = Path("storage"),
    ) -> dict[str, Any]:
        """Install or resolve one pattern and run scan on target path."""
        marketplace = PatternMarketplace(storage_root=storage_root)
        install_result = marketplace.install(pattern_ref)
        if not install_result.get("success", False):
            return {
                "success": False,
                "error": str(install_result.get("error") or "Pattern install failed"),
            }

        selected_pattern_id = str(install_result.get("pattern_id") or pattern_ref)
        scanner = PatternScanner(
            max_workers=self.max_workers,
            context_lines=self.context_lines,
        )
        patterns = [
            item
            for item in self.loader.load_all_patterns()
            if item.id.strip().lower() == selected_pattern_id.strip().lower()
        ]
        if not patterns:
            return {
                "success": False,
                "error": f"Pattern not available after install: {selected_pattern_id}",
            }

        result = scanner.scan(
            target_path,
            patterns,
            glob=glob,
            max_files=max_files,
        )
        return {
            "success": result.success,
            "pattern_id": selected_pattern_id,
            "installed": bool(install_result.get("installed", False)),
            "patterns_scanned": result.patterns_scanned,
            "files_scanned": result.files_scanned,
            "matches_found": len(result.matches),
            "scan_time_ms": result.scan_time_ms,
            "matches": [
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
                for match in result.matches
            ],
            "errors": result.errors,
        }

    def compare_patterns(self, left_id: str, right_id: str) -> dict[str, Any]:
        """Compare two patterns and return notable differences."""
        lookup = {
            item.id.strip().lower(): item for item in self.loader.load_all_patterns()
        }
        left = lookup.get(left_id.strip().lower())
        right = lookup.get(right_id.strip().lower())
        if left is None or right is None:
            missing = []
            if left is None:
                missing.append(left_id)
            if right is None:
                missing.append(right_id)
            return {
                "success": False,
                "error": f"Pattern not found: {', '.join(missing)}",
            }

        return {
            "success": True,
            "left": {
                "id": left.id,
                "name": left.name,
                "severity": left.severity,
                "tags": left.tags,
                "languages": left.languages,
                "pattern": left.pattern,
            },
            "right": {
                "id": right.id,
                "name": right.name,
                "severity": right.severity,
                "tags": right.tags,
                "languages": right.languages,
                "pattern": right.pattern,
            },
            "diff": {
                "severity_changed": left.severity != right.severity,
                "regex_changed": left.pattern != right.pattern,
                "tags_added": [tag for tag in right.tags if tag not in left.tags],
                "tags_removed": [tag for tag in left.tags if tag not in right.tags],
                "languages_added": [
                    lang for lang in right.languages if lang not in left.languages
                ],
                "languages_removed": [
                    lang for lang in left.languages if lang not in right.languages
                ],
            },
        }

    def customize_from_template(
        self,
        template_id: str,
        values: dict[str, str],
        *,
        pattern_id: str | None = None,
        name: str | None = None,
        description: str = "",
        severity: str | None = None,
        tags: list[str] | None = None,
        languages: list[str] | None = None,
        install: bool = False,
    ) -> PatternDefinition:
        """Render a pattern from template and optionally install it."""
        registry = PatternTemplateRegistry()
        rendered = registry.render_pattern(
            template_id=template_id,
            values=values,
            pattern_id=pattern_id,
            name=name,
            description=description or None,
            severity=severity,
            tags=tags,
            languages=languages,
        )
        if install:
            PatternManager().add_custom_pattern(rendered.pattern)
        return rendered.pattern

    def suggest_fix(self, match: PatternMatch) -> FixSuggestion | None:
        """Suggest automated fixes for a pattern match."""
        suggestion = self._SUGGESTION_MAP.get(match.pattern_id)
        if not suggestion:
            return None

        title, description, confidence = suggestion
        return FixSuggestion(
            pattern_id=match.pattern_id,
            title=title,
            description=description,
            confidence=confidence,
            file_path=match.file_path,
            line_number=match.line_number,
        )
