"""
patterns/loader.py - Pattern loading and detection system

This module provides functionality for loading and running custom pattern detectors.
Supports both built-in patterns and user-defined patterns.
"""

from __future__ import annotations

import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class PatternMatch:
    """Single pattern match result."""

    pattern_id: str
    pattern_name: str
    file_path: Path
    line_number: int
    line_content: str
    matched_text: str
    severity: str
    message: str
    description: str
    tags: list[str]


@dataclass
class PatternDefinition:
    """Pattern definition structure."""

    id: str
    name: str
    pattern: str
    severity: str = "warning"
    description: str = ""
    message: str = ""
    tags: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    enabled: bool = True

    def __post_init__(self):
        """Validate pattern after creation."""
        if not self.message:
            self.message = f"{self.name} detected"

        # Compile regex to validate it
        try:
            re.compile(self.pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{self.id}': {e}")


@dataclass
class PatternScanResult:
    """Result of pattern scan."""

    success: bool
    patterns_scanned: int
    files_scanned: int
    matches: list[PatternMatch]
    errors: list[str] = field(default_factory=list)
    scan_time_ms: float = 0.0


class PatternLoader:
    """Load patterns from various sources."""

    def __init__(self, patterns_dir: Path | None = None):
        self.patterns_dir = patterns_dir or Path(__file__).parent
        self.builtin_dir = self.patterns_dir / "builtin"
        self.custom_dir = self.patterns_dir / "custom"

    def load_all_patterns(self) -> list[PatternDefinition]:
        """Load all available patterns."""
        patterns = []

        # Load built-in patterns
        if self.builtin_dir.exists():
            patterns.extend(self._load_patterns_from_dir(self.builtin_dir))

        # Load custom patterns
        if self.custom_dir.exists():
            patterns.extend(self._load_patterns_from_dir(self.custom_dir))

        return patterns

    def load_builtin_patterns(
        self, category: str | None = None
    ) -> list[PatternDefinition]:
        """Load built-in patterns, optionally filtered by category."""
        patterns = []

        if not self.builtin_dir.exists():
            return patterns

        if category:
            # Load specific category
            category_file = self.builtin_dir / f"{category}.yaml"
            if category_file.exists():
                patterns.extend(self._load_patterns_from_file(category_file))
        else:
            # Load all categories
            for pattern_file in self.builtin_dir.glob("*.yaml"):
                patterns.extend(self._load_patterns_from_file(pattern_file))

        return patterns

    def load_custom_patterns(self) -> list[PatternDefinition]:
        """Load user-defined custom patterns."""
        patterns = []

        if not self.custom_dir.exists():
            return patterns

        for pattern_file in self.custom_dir.glob("*.yaml"):
            patterns.extend(self._load_patterns_from_file(pattern_file))

        return patterns

    def _load_patterns_from_dir(self, directory: Path) -> list[PatternDefinition]:
        """Load all patterns from a directory."""
        patterns = []

        for pattern_file in directory.rglob("*.yaml"):
            patterns.extend(self._load_patterns_from_file(pattern_file))

        return patterns

    def _load_patterns_from_file(self, file_path: Path) -> list[PatternDefinition]:
        """Load patterns from a YAML file."""
        patterns = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                return patterns

            # Handle both single pattern and list of patterns
            if isinstance(data, dict) and "patterns" in data:
                pattern_list = data["patterns"]
            elif isinstance(data, list):
                pattern_list = data
            else:
                pattern_list = [data]

            for pattern_data in pattern_list:
                try:
                    pattern = PatternDefinition(**pattern_data)
                    if pattern.enabled:
                        patterns.append(pattern)
                except (TypeError, ValueError) as e:
                    print(f"Warning: Skipping invalid pattern in {file_path}: {e}")

        except Exception as e:
            print(f"Error loading patterns from {file_path}: {e}")

        return patterns


class PatternScanner:
    """Scan files for pattern matches."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers

    def scan(
        self,
        path: Path,
        patterns: list[PatternDefinition],
        glob: str = "*",
        max_files: int = 10000,
    ) -> PatternScanResult:
        """
        Scan path for pattern matches.

        Args:
            path: Directory or file to scan
            patterns: List of patterns to match
            glob: File glob pattern
            max_files: Maximum number of files to scan

        Returns:
            PatternScanResult with matches
        """
        import time

        start_time = time.time()

        if not path.exists():
            return PatternScanResult(
                success=False,
                patterns_scanned=len(patterns),
                files_scanned=0,
                matches=[],
                errors=[f"Path does not exist: {path}"],
            )

        # Find files to scan
        if path.is_file():
            files = [path]
        else:
            files = list(path.rglob(glob))[:max_files]
            files = [f for f in files if f.is_file()]

        # Scan files in parallel
        all_matches = []
        errors = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self._scan_file, file_path, patterns): file_path
                for file_path in files
            }

            for future in as_completed(future_to_file):
                try:
                    file_matches = future.result()
                    all_matches.extend(file_matches)
                except Exception as e:
                    errors.append(str(e))

        scan_time_ms = (time.time() - start_time) * 1000

        return PatternScanResult(
            success=True,
            patterns_scanned=len(patterns),
            files_scanned=len(files),
            matches=all_matches,
            errors=errors,
            scan_time_ms=scan_time_ms,
        )

    def _scan_file(
        self, file_path: Path, patterns: list[PatternDefinition]
    ) -> list[PatternMatch]:
        """Scan a single file for pattern matches."""
        matches = []

        # Determine file language from extension
        file_ext = file_path.suffix.lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".rb": "ruby",
        }
        file_lang = lang_map.get(file_ext)

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_idx, line in enumerate(lines):
                for pattern in patterns:
                    # Skip if pattern is language-specific and doesn't match
                    if pattern.languages and file_lang:
                        if file_lang not in pattern.languages:
                            continue

                    # Search for pattern
                    regex = re.compile(pattern.pattern)
                    match = regex.search(line)

                    if match:
                        matched_text = match.group()

                        # Format message with context
                        message = pattern.message
                        message = message.replace("{{file}}", str(file_path))
                        message = message.replace("{{line}}", str(line_idx + 1))
                        message = message.replace("{{match}}", matched_text)

                        matches.append(
                            PatternMatch(
                                pattern_id=pattern.id,
                                pattern_name=pattern.name,
                                file_path=file_path,
                                line_number=line_idx + 1,
                                line_content=line.rstrip(),
                                matched_text=matched_text,
                                severity=pattern.severity,
                                message=message,
                                description=pattern.description,
                                tags=pattern.tags,
                            )
                        )

        except (UnicodeDecodeError, PermissionError, OSError):
            pass

        return matches


class PatternManager:
    """High-level pattern management."""

    def __init__(self):
        self.loader = PatternLoader()
        self.scanner = PatternScanner()

    def list_patterns(self, category: str | None = None) -> list[PatternDefinition]:
        """List available patterns."""
        if category:
            return self.loader.load_builtin_patterns(category)
        else:
            return self.loader.load_all_patterns()

    def add_custom_pattern(self, pattern: PatternDefinition) -> bool:
        """Add a custom pattern."""
        try:
            custom_file = self.loader.custom_dir / "user_patterns.yaml"
            self.loader.custom_dir.mkdir(parents=True, exist_ok=True)

            # Load existing patterns
            existing = []
            if custom_file.exists():
                with open(custom_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "patterns" in data:
                        existing = data["patterns"]

            # Add new pattern
            existing.append(
                {
                    "id": pattern.id,
                    "name": pattern.name,
                    "pattern": pattern.pattern,
                    "severity": pattern.severity,
                    "description": pattern.description,
                    "message": pattern.message,
                    "tags": pattern.tags,
                    "languages": pattern.languages,
                    "enabled": pattern.enabled,
                }
            )

            # Save back
            with open(custom_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    {"patterns": existing},
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                )

            return True

        except Exception as e:
            print(f"Error saving custom pattern: {e}")
            return False


# Convenience functions
def load_patterns(category: str | None = None) -> list[PatternDefinition]:
    """Load patterns (convenience function)."""
    loader = PatternLoader()
    if category:
        return loader.load_builtin_patterns(category)
    return loader.load_all_patterns()


def scan_patterns(
    path: Path, patterns: list[PatternDefinition] | None = None, glob: str = "*"
) -> PatternScanResult:
    """Scan for patterns (convenience function)."""
    if patterns is None:
        patterns = load_patterns()

    scanner = PatternScanner()
    return scanner.scan(path, patterns, glob)
