"""
diff_sight.py - Code change detection and diff reporting.

Purpose:
    Detect code changes between file versions, generate diff reports,
    and highlight semantic changes.

Constitutional Basis:
    - Article 1: Observation Purity (only reports actual changes)
    - Article 4: Progressive Disclosure (diffs at different levels of detail)
    - Article 9: Immutable Observations (track change history)

Features:
    - Line-by-line diff generation
    - Semantic change detection (imports, functions, classes)
    - Change history tracking
    - Merge/diff workflow support
"""

from __future__ import annotations

import difflib
import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, NamedTuple


class ChangeCategory(Enum):
    """Category of code change."""

    ADDITION = auto()  # New code added
    DELETION = auto()  # Code removed
    MODIFICATION = auto()  # Code changed
    REFORMAT = auto()  # Whitespace/formatting only


class SemanticChangeType(Enum):
    """Type of semantic change detected."""

    IMPORT_CHANGED = auto()
    FUNCTION_ADDED = auto()
    FUNCTION_REMOVED = auto()
    FUNCTION_MODIFIED = auto()
    CLASS_ADDED = auto()
    CLASS_REMOVED = auto()
    CLASS_MODIFIED = auto()
    SIGNATURE_CHANGED = auto()
    DOCSTRING_CHANGED = auto()
    COMMENT_CHANGED = auto()
    LOGIC_CHANGED = auto()


@dataclass(frozen=True)
class LineChange:
    """Immutable record of a single line change."""

    old_line_number: int | None
    new_line_number: int | None
    old_content: str | None
    new_content: str | None
    category: ChangeCategory


@dataclass(frozen=True)
class SemanticChange:
    """Immutable record of a semantic code change."""

    change_type: SemanticChangeType
    symbol_name: str
    old_signature: str | None
    new_signature: str | None
    description: str
    line_number: int | None = None


@dataclass
class FileDiff:
    """Complete diff for a single file."""

    file_path: Path
    old_hash: str | None
    new_hash: str | None
    old_content: str | None
    new_content: str | None
    line_changes: list[LineChange] = field(default_factory=list)
    semantic_changes: list[SemanticChange] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def has_changes(self) -> bool:
        """Check if file has any meaningful changes."""
        return len(self.line_changes) > 0 or len(self.semantic_changes) > 0

    @property
    def is_reformat_only(self) -> bool:
        """Check if changes are only formatting/whitespace."""
        if not self.line_changes:
            return False
        return all(c.category == ChangeCategory.REFORMAT for c in self.line_changes)

    @property
    def lines_added(self) -> int:
        """Count lines added."""
        return sum(
            1 for c in self.line_changes if c.category == ChangeCategory.ADDITION
        )

    @property
    def lines_deleted(self) -> int:
        """Count lines deleted."""
        return sum(
            1 for c in self.line_changes if c.category == ChangeCategory.DELETION
        )

    @property
    def lines_modified(self) -> int:
        """Count lines modified."""
        return sum(
            1 for c in self.line_changes if c.category == ChangeCategory.MODIFICATION
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_path": str(self.file_path),
            "old_hash": self.old_hash,
            "new_hash": self.new_hash,
            "has_changes": self.has_changes,
            "is_reformat_only": self.is_reformat_only,
            "lines_added": self.lines_added,
            "lines_deleted": self.lines_deleted,
            "lines_modified": self.lines_modified,
            "semantic_changes": [
                {
                    "type": c.change_type.name,
                    "symbol": c.symbol_name,
                    "description": c.description,
                }
                for c in self.semantic_changes
            ],
            "timestamp": self.timestamp.isoformat(),
        }


class DiffSight:
    """
    Diff detection and semantic change analysis.

    Features:
    - Generate unified diffs
    - Detect semantic changes (functions, classes, imports)
    - Track change history
    - Support for incremental investigations
    """

    def __init__(self):
        """Initialize diff sight."""
        self._file_history: dict[Path, str] = {}  # path -> content hash

    def calculate_diff(
        self,
        file_path: Path,
        old_content: str | None,
        new_content: str | None,
        old_hash: str | None = None,
        new_hash: str | None = None,
    ) -> FileDiff:
        """
        Calculate diff between two versions of a file.

        Args:
            file_path: Path to the file
            old_content: Previous file content
            new_content: Current file content
            old_hash: Hash of old content (calculated if not provided)
            new_hash: Hash of new content (calculated if not provided)

        Returns:
            FileDiff with line changes and semantic analysis
        """
        # Calculate hashes if not provided
        if old_hash is None and old_content is not None:
            old_hash = self._hash_content(old_content)
        if new_hash is None and new_content is not None:
            new_hash = self._hash_content(new_content)

        # Handle special cases
        if old_content is None and new_content is None:
            return FileDiff(
                file_path=file_path,
                old_hash=old_hash,
                new_hash=new_hash,
                old_content=None,
                new_content=None,
            )

        if old_content is None:
            # New file
            lines = new_content.splitlines(keepends=True)
            line_changes = [
                LineChange(
                    old_line_number=None,
                    new_line_number=i + 1,
                    old_content=None,
                    new_content=line.rstrip("\n\r"),
                    category=ChangeCategory.ADDITION,
                )
                for i, line in enumerate(lines)
            ]
            semantic_changes = self._detect_semantic_changes(None, new_content)
            return FileDiff(
                file_path=file_path,
                old_hash=old_hash,
                new_hash=new_hash,
                old_content=None,
                new_content=new_content,
                line_changes=line_changes,
                semantic_changes=semantic_changes,
            )

        if new_content is None:
            # Deleted file
            lines = old_content.splitlines(keepends=True)
            line_changes = [
                LineChange(
                    old_line_number=i + 1,
                    new_line_number=None,
                    old_content=line.rstrip("\n\r"),
                    new_content=None,
                    category=ChangeCategory.DELETION,
                )
                for i, line in enumerate(lines)
            ]
            semantic_changes = self._detect_semantic_changes(old_content, None)
            return FileDiff(
                file_path=file_path,
                old_hash=old_hash,
                new_hash=new_hash,
                old_content=old_content,
                new_content=None,
                line_changes=line_changes,
                semantic_changes=semantic_changes,
            )

        # Modified file - generate unified diff
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        line_changes = self._generate_line_changes(old_lines, new_lines)
        semantic_changes = self._detect_semantic_changes(old_content, new_content)

        return FileDiff(
            file_path=file_path,
            old_hash=old_hash,
            new_hash=new_hash,
            old_content=old_content,
            new_content=new_content,
            line_changes=line_changes,
            semantic_changes=semantic_changes,
        )

    def diff_files(self, old_file: Path, new_file: Path) -> FileDiff:
        """
        Calculate diff between two files on disk.

        Args:
            old_file: Path to old version
            new_file: Path to new version

        Returns:
            FileDiff with changes
        """
        old_content = self._read_file(old_file)
        new_content = self._read_file(new_file)

        return self.calculate_diff(new_file, old_content, new_content)

    def track_file(self, file_path: Path, content: str | None = None) -> bool:
        """
        Track file for future diff comparisons.

        Args:
            file_path: Path to file
            content: File content (read from disk if not provided)

        Returns:
            True if file changed since last tracking, False otherwise
        """
        if content is None:
            content = self._read_file(file_path)

        if content is None:
            # File doesn't exist or can't be read
            if file_path in self._file_history:
                del self._file_history[file_path]
            return True

        current_hash = self._hash_content(content)

        if file_path not in self._file_history:
            self._file_history[file_path] = current_hash
            return True

        old_hash = self._file_history[file_path]
        changed = old_hash != current_hash

        if changed:
            self._file_history[file_path] = current_hash

        return changed

    def get_tracked_files(self) -> list[Path]:
        """Get list of tracked files."""
        return list(self._file_history.keys())

    def clear_history(self) -> None:
        """Clear tracked file history."""
        self._file_history.clear()

    def generate_unified_diff(
        self,
        file_diff: FileDiff,
        context_lines: int = 3,
    ) -> str:
        """
        Generate unified diff format output.

        Args:
            file_diff: FileDiff to format
            context_lines: Number of context lines around changes

        Returns:
            Unified diff string
        """
        if not file_diff.has_changes:
            return ""

        old_lines = (
            file_diff.old_content.splitlines(keepends=True)
            if file_diff.old_content
            else []
        )
        new_lines = (
            file_diff.new_content.splitlines(keepends=True)
            if file_diff.new_content
            else []
        )

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=str(file_diff.file_path),
            tofile=str(file_diff.file_path),
            n=context_lines,
        )

        return "".join(diff)

    def _generate_line_changes(
        self,
        old_lines: list[str],
        new_lines: list[str],
    ) -> list[LineChange]:
        """Generate line-by-line changes using sequence matcher."""
        changes: list[LineChange] = []

        # Use difflib.SequenceMatcher for efficient diffing
        sm = difflib.SequenceMatcher(None, old_lines, new_lines)

        old_line_num = 0
        new_line_num = 0

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                old_line_num += i2 - i1
                new_line_num += j2 - j1
            elif tag == "delete":
                # Lines deleted from old
                for i in range(i1, i2):
                    changes.append(
                        LineChange(
                            old_line_number=old_line_num + 1,
                            new_line_number=None,
                            old_content=old_lines[i].rstrip("\n\r"),
                            new_content=None,
                            category=ChangeCategory.DELETION,
                        )
                    )
                    old_line_num += 1
            elif tag == "insert":
                # Lines inserted in new
                for j in range(j1, j2):
                    changes.append(
                        LineChange(
                            old_line_number=None,
                            new_line_number=new_line_num + 1,
                            old_content=None,
                            new_content=new_lines[j].rstrip("\n\r"),
                            category=ChangeCategory.ADDITION,
                        )
                    )
                    new_line_num += 1
            elif tag == "replace":
                # Lines replaced (delete + insert)
                # First handle deletions
                for i in range(i1, i2):
                    changes.append(
                        LineChange(
                            old_line_number=old_line_num + 1,
                            new_line_number=None,
                            old_content=old_lines[i].rstrip("\n\r"),
                            new_content=None,
                            category=ChangeCategory.DELETION,
                        )
                    )
                    old_line_num += 1

                # Then insertions
                for j in range(j1, j2):
                    changes.append(
                        LineChange(
                            old_line_number=None,
                            new_line_number=new_line_num + 1,
                            old_content=None,
                            new_content=new_lines[j].rstrip("\n\r"),
                            category=ChangeCategory.ADDITION,
                        )
                    )
                    new_line_num += 1

        # Post-process to detect modifications (adjacent delete+insert pairs)
        changes = self._coalesce_changes(changes)

        return changes

    def _coalesce_changes(self, changes: list[LineChange]) -> list[LineChange]:
        """Coalesce adjacent delete+insert pairs into modifications."""
        if not changes:
            return changes

        result: list[LineChange] = []
        i = 0

        while i < len(changes):
            current = changes[i]

            # Check if this is a deletion followed by an addition at same position
            if (
                current.category == ChangeCategory.DELETION
                and i + 1 < len(changes)
                and changes[i + 1].category == ChangeCategory.ADDITION
            ):
                next_change = changes[i + 1]

                # Check if it's just a whitespace/formatting change
                old_stripped = (
                    current.old_content.strip() if current.old_content else ""
                )
                new_stripped = (
                    next_change.new_content.strip() if next_change.new_content else ""
                )

                if old_stripped == new_stripped:
                    # Reformat only
                    result.append(
                        LineChange(
                            old_line_number=current.old_line_number,
                            new_line_number=next_change.new_line_number,
                            old_content=current.old_content,
                            new_content=next_change.new_content,
                            category=ChangeCategory.REFORMAT,
                        )
                    )
                else:
                    # Real modification
                    result.append(
                        LineChange(
                            old_line_number=current.old_line_number,
                            new_line_number=next_change.new_line_number,
                            old_content=current.old_content,
                            new_content=next_change.new_content,
                            category=ChangeCategory.MODIFICATION,
                        )
                    )
                i += 2
            else:
                result.append(current)
                i += 1

        return result

    def _detect_semantic_changes(
        self,
        old_content: str | None,
        new_content: str | None,
    ) -> list[SemanticChange]:
        """Detect semantic changes (imports, functions, classes)."""
        changes: list[SemanticChange] = []

        # Parse old and new content for Python constructs
        old_imports = self._extract_imports(old_content)
        new_imports = self._extract_imports(new_content)
        old_functions = self._extract_functions(old_content)
        new_functions = self._extract_functions(new_content)
        old_classes = self._extract_classes(old_content)
        new_classes = self._extract_classes(new_content)

        # Detect import changes
        added_imports = new_imports - old_imports
        removed_imports = old_imports - new_imports

        for imp in added_imports:
            changes.append(
                SemanticChange(
                    change_type=SemanticChangeType.IMPORT_CHANGED,
                    symbol_name=imp,
                    old_signature=None,
                    new_signature=imp,
                    description=f"Import added: {imp}",
                )
            )

        for imp in removed_imports:
            changes.append(
                SemanticChange(
                    change_type=SemanticChangeType.IMPORT_CHANGED,
                    symbol_name=imp,
                    old_signature=imp,
                    new_signature=None,
                    description=f"Import removed: {imp}",
                )
            )

        # Detect function changes
        added_funcs = new_functions.keys() - old_functions.keys()
        removed_funcs = old_functions.keys() - new_functions.keys()
        common_funcs = old_functions.keys() & new_functions.keys()

        for func_name in added_funcs:
            changes.append(
                SemanticChange(
                    change_type=SemanticChangeType.FUNCTION_ADDED,
                    symbol_name=func_name,
                    old_signature=None,
                    new_signature=new_functions[func_name],
                    description=f"Function added: {func_name}",
                )
            )

        for func_name in removed_funcs:
            changes.append(
                SemanticChange(
                    change_type=SemanticChangeType.FUNCTION_REMOVED,
                    symbol_name=func_name,
                    old_signature=old_functions[func_name],
                    new_signature=None,
                    description=f"Function removed: {func_name}",
                )
            )

        for func_name in common_funcs:
            old_sig = old_functions[func_name]
            new_sig = new_functions[func_name]
            if old_sig != new_sig:
                changes.append(
                    SemanticChange(
                        change_type=SemanticChangeType.FUNCTION_MODIFIED,
                        symbol_name=func_name,
                        old_signature=old_sig,
                        new_signature=new_sig,
                        description=f"Function modified: {func_name}",
                    )
                )

        # Detect class changes
        added_classes = new_classes.keys() - old_classes.keys()
        removed_classes = old_classes.keys() - new_classes.keys()
        common_classes = old_classes.keys() & new_classes.keys()

        for class_name in added_classes:
            changes.append(
                SemanticChange(
                    change_type=SemanticChangeType.CLASS_ADDED,
                    symbol_name=class_name,
                    old_signature=None,
                    new_signature=new_classes[class_name],
                    description=f"Class added: {class_name}",
                )
            )

        for class_name in removed_classes:
            changes.append(
                SemanticChange(
                    change_type=SemanticChangeType.CLASS_REMOVED,
                    symbol_name=class_name,
                    old_signature=old_classes[class_name],
                    new_signature=None,
                    description=f"Class removed: {class_name}",
                )
            )

        for class_name in common_classes:
            old_sig = old_classes[class_name]
            new_sig = new_classes[class_name]
            if old_sig != new_sig:
                changes.append(
                    SemanticChange(
                        change_type=SemanticChangeType.CLASS_MODIFIED,
                        symbol_name=class_name,
                        old_signature=old_sig,
                        new_signature=new_sig,
                        description=f"Class modified: {class_name}",
                    )
                )

        return changes

    def _extract_imports(self, content: str | None) -> set[str]:
        """Extract import statements from Python code."""
        if not content:
            return set()

        imports = set()
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                imports.add(stripped)
        return imports

    def _extract_functions(self, content: str | None) -> dict[str, str]:
        """Extract function definitions from Python code."""
        if not content:
            return {}

        functions = {}
        lines = content.splitlines()

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("def ") and stripped.endswith(":"):
                # Extract function signature
                sig = stripped[:-1]  # Remove trailing colon
                func_name = sig[4:].split("(")[0].strip()
                functions[func_name] = sig

        return functions

    def _extract_classes(self, content: str | None) -> dict[str, str]:
        """Extract class definitions from Python code."""
        if not content:
            return {}

        classes = {}
        lines = content.splitlines()

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("class ") and stripped.endswith(":"):
                # Extract class signature
                sig = stripped[:-1]  # Remove trailing colon
                class_name = sig[6:].split("(")[0].split(":")[0].strip()
                classes[class_name] = sig

        return classes

    def _read_file(self, file_path: Path) -> str | None:
        """Read file content safely."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except (OSError, IOError):
            return None

    def _hash_content(self, content: str) -> str:
        """Calculate SHA256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_diff_report(
    diffs: list[FileDiff],
    include_unchanged: bool = False,
) -> dict[str, Any]:
    """
    Generate a summary report of multiple file diffs.

    Args:
        diffs: List of file diffs
        include_unchanged: Include files with no changes

    Returns:
        Summary dictionary
    """
    total_files = len(diffs)
    files_changed = sum(1 for d in diffs if d.has_changes)
    files_added = sum(1 for d in diffs if d.old_hash is None and d.new_hash is not None)
    files_deleted = sum(
        1 for d in diffs if d.old_hash is not None and d.new_hash is None
    )
    files_modified = sum(
        1
        for d in diffs
        if d.old_hash is not None and d.new_hash is not None and d.has_changes
    )

    total_lines_added = sum(d.lines_added for d in diffs)
    total_lines_deleted = sum(d.lines_deleted for d in diffs)
    total_lines_modified = sum(d.lines_modified for d in diffs)

    all_semantic_changes = []
    for diff in diffs:
        all_semantic_changes.extend(diff.semantic_changes)

    return {
        "summary": {
            "total_files": total_files,
            "files_changed": files_changed,
            "files_added": files_added,
            "files_deleted": files_deleted,
            "files_modified": files_modified,
            "total_lines_added": total_lines_added,
            "total_lines_deleted": total_lines_deleted,
            "total_lines_modified": total_lines_modified,
        },
        "semantic_changes": [
            {
                "type": c.change_type.name,
                "symbol": c.symbol_name,
                "description": c.description,
            }
            for c in all_semantic_changes
        ],
        "file_changes": [d.to_dict() for d in diffs if d.has_changes],
    }
