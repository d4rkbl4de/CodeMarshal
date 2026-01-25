"""
STRUCTURE: "What's here?" - Pure Description Without Inference

This module answers the first legitimate human question about a codebase:
What exists, spatially and quantitatively, without implying purpose or quality.

CONSTITUTIONAL RULES:
1. No heuristics - only observable facts
2. No scoring - no quality judgments
3. No conclusions - no implied meaning
4. Only counts, lists, and trees
5. No labels like "large", "messy", or "clean"

Tier 1 Violation: If this module makes any inference about code quality,
purpose, or developer intent, the system halts immediately.
"""

import collections
import json
import os
import pathlib
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from typing import (
    Any,
    Union,
)

from observations.eyes.file_sight import FileSight
from observations.limitations.declared import Limitation

# Allowed Layer 1 imports (reality layer)
from observations.record.snapshot import Snapshot


class NodeType(Enum):
    """Types of nodes in the structure tree.

    Only observable facts about file system objects.
    No inferred categories like "source", "test", or "docs".
    """

    DIRECTORY = auto()
    PYTHON_FILE = auto()
    TEXT_FILE = auto()
    BINARY_FILE = auto()
    SYMLINK = auto()
    OTHER_FILE = auto()


@dataclass(frozen=True)
class PathNode:
    """Immutable node representing a file or directory.

    Contains only observable attributes.
    No inferred meaning allowed.
    """

    absolute_path: pathlib.Path
    relative_path: pathlib.Path
    node_type: NodeType
    size_bytes: int
    modification_time: datetime | None

    # File-specific attributes (None for directories)
    file_extension: str | None = None
    line_count: int | None = None
    encoding: str | None = None

    def __post_init__(self) -> None:
        """Validate node doesn't contain inferred meaning."""
        # Constitutional: No semantic labels in node_type
        if not isinstance(self.node_type, NodeType):
            raise ConstitutionalViolation(
                f"Node type must be NodeType enum, got {type(self.node_type)}"
            )

        # Constitutional: No inferred file categories
        if self.file_extension:
            # Only allow actual file extensions, not categories
            if self.file_extension.lower() in {"src", "test", "doc", "config"}:
                raise ConstitutionalViolation(
                    f"File extension '{self.file_extension}' implies category. "
                    "Use actual extension only."
                )

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary without inference."""
        return {
            "absolute_path": str(self.absolute_path),
            "relative_path": str(self.relative_path),
            "node_type": self.node_type.name,
            "size_bytes": self.size_bytes,
            "modification_time": (
                self.modification_time.isoformat() if self.modification_time else None
            ),
            "file_extension": self.file_extension,
            "line_count": self.line_count,
            "encoding": self.encoding,
        }


@dataclass
class DirectoryTree:
    """Pure spatial organization of directory structure.

    Contains only tree relationships and counts.
    No hierarchy quality judgments allowed.
    """

    root: PathNode
    children: list[Union["DirectoryTree", PathNode]] = field(default_factory=list)
    depth: int = 0

    def add_child(self, child: Union["DirectoryTree", PathNode]) -> None:
        """Add child node to tree.

        Constitutional check: Child must be valid for its parent.
        """
        # Ensure child path is within parent path
        if isinstance(child, DirectoryTree):
            if not str(child.root.absolute_path).startswith(
                str(self.root.absolute_path) + os.path.sep
            ):
                raise ConstitutionalViolation(
                    f"Child tree {child.root.absolute_path} "
                    f"not under parent {self.root.absolute_path}"
                )
        elif isinstance(child, PathNode):
            if not str(child.absolute_path).startswith(
                str(self.root.absolute_path) + os.path.sep
            ):
                raise ConstitutionalViolation(
                    f"Child node {child.absolute_path} "
                    f"not under parent {self.root.absolute_path}"
                )

        self.children.append(child)

    def count_nodes(self) -> dict[str, int]:
        """Count nodes by type without semantic grouping."""
        counts: collections.defaultdict[str, int] = collections.defaultdict(int)

        # Count self
        counts[self.root.node_type.name] += 1

        # Count children
        for child in self.children:
            if isinstance(child, DirectoryTree):
                child_counts = child.count_nodes()
                for node_type, count in child_counts.items():
                    counts[node_type] += count
            else:
                counts[child.node_type.name] += 1

        return dict(counts)

    def get_all_paths(self) -> list[pathlib.Path]:
        """Get all paths in tree without ordering judgment."""
        paths = [self.root.absolute_path]

        for child in self.children:
            if isinstance(child, DirectoryTree):
                paths.extend(child.get_all_paths())
            else:
                paths.append(child.absolute_path)

        return paths

    def to_nested_dict(self) -> dict[str, Any]:
        """Convert to nested dictionary for JSON serialization.

        Constitutional: No inferred grouping or categorization.
        """
        children_list = []
        for child in self.children:
            if isinstance(child, DirectoryTree):
                children_list.append(child.to_nested_dict())
            else:
                children_list.append(child.to_dict())

        return {
            "root": self.root.to_dict(),
            "depth": self.depth,
            "children": children_list,
        }

    def walk(self) -> Iterator[tuple[int, Union["DirectoryTree", PathNode]]]:
        """Walk tree depth-first without prioritizing any node type."""
        yield self.depth, self
        for child in self.children:
            if isinstance(child, DirectoryTree):
                yield from child.walk()
            else:
                yield self.depth + 1, child


@dataclass
class StructureAnalysis:
    """Pure descriptive analysis of codebase structure.

    Contains only:
    - Lists (what exists)
    - Counts (how many)
    - Trees (spatial relationships)
    - Distributions (numeric spread)

    Constitutional: No conclusions about what these mean.
    """

    root_path: pathlib.Path
    total_files: int
    total_directories: int
    file_type_counts: dict[str, int]
    depth_distribution: dict[int, int]  # depth -> node count
    size_distribution: dict[str, list[int]]  # type -> list of sizes
    directory_tree: DirectoryTree
    limitations: list[Limitation]

    # Constitutional: No derived metrics with semantic meaning
    # Only observable distributions allowed

    def get_flat_file_list(self) -> list[dict[str, Any]]:
        """Get flat list of all files without sorting judgment."""
        files = []

        def collect_files(node: DirectoryTree | PathNode) -> None:
            if isinstance(node, DirectoryTree):
                for child in node.children:
                    collect_files(child)
            elif node.node_type != NodeType.DIRECTORY:
                files.append(node.to_dict())

        collect_files(self.directory_tree)
        return files

    def get_directory_sizes(self) -> dict[str, int]:
        """Calculate directory sizes in bytes.

        Constitutional: Only raw byte counts, no "large/small" labels.
        """
        sizes: dict[str, int] = {}

        def calculate_size(node: DirectoryTree | PathNode) -> int:
            if isinstance(node, DirectoryTree):
                total = node.root.size_bytes
                for child in node.children:
                    total += calculate_size(child)
                sizes[str(node.root.relative_path)] = total
                return total
            else:
                return node.size_bytes

        calculate_size(self.directory_tree)
        return sizes

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary without inference."""
        return {
            "root_path": str(self.root_path),
            "total_files": self.total_files,
            "total_directories": self.total_directories,
            "file_type_counts": self.file_type_counts,
            "depth_distribution": self.depth_distribution,
            "size_distribution": self.size_distribution,
            "directory_tree": self.directory_tree.to_nested_dict(),
            "limitations": [
                limitation.to_dict()
                if hasattr(limitation, "to_dict")
                else str(limitation)
                for limitation in self.limitations
            ],
            "analysis_timestamp": datetime.now(UTC).isoformat(),
            "_type": "structure_analysis",
        }


class StructureAnalyzer:
    """Pure analyzer that describes what exists without interpretation.

    This analyzer should be answerable by a human with a clipboard.
    The system is only faster and more consistent.
    """

    # Constitutional: No magic thresholds or heuristics
    # All patterns must be explicitly declared as limitations

    def __init__(self, snapshot: Snapshot):
        """Initialize with immutable observation snapshot."""
        self.snapshot = snapshot
        self.limitations: list[Limitation] = []

        # Constitutional: Validate we're only working with observations
        if not hasattr(snapshot, "get_file_observations"):
            raise ConstitutionalViolation(
                "Snapshot must provide file observations. "
                "Structure analysis requires Layer 1 observations only."
            )

    def analyze(self) -> StructureAnalysis:
        """Analyze structure without inference.

        Returns only observable facts:
        - What files exist
        - Where they are
        - How many there are
        - How they're organized spatially
        """
        # Get raw observations from Layer 1
        file_observations = self.snapshot.get_file_observations()

        # Build tree structure
        tree = self._build_directory_tree(file_observations)

        # Count nodes
        node_counts = tree.count_nodes()

        # Calculate distributions
        depth_dist = self._calculate_depth_distribution(tree)
        size_dist = self._calculate_size_distribution(tree)

        # Extract file type counts (raw extensions only)
        file_type_counts = self._count_file_types(tree)

        # Constitutional: No derived totals - count from tree
        total_files = sum(
            count
            for node_type, count in node_counts.items()
            if node_type != "DIRECTORY"
        )
        total_directories = node_counts.get("DIRECTORY", 0)

        return StructureAnalysis(
            root_path=self.snapshot.root_path,
            total_files=total_files,
            total_directories=total_directories,
            file_type_counts=file_type_counts,
            depth_distribution=depth_dist,
            size_distribution=size_dist,
            directory_tree=tree,
            limitations=self.limitations,
        )

    def _build_directory_tree(self, observations: list[FileSight]) -> DirectoryTree:
        """Build pure spatial tree from observations.

        Constitutional: No semantic grouping of directories.
        """
        # Get root path from first observation
        if not observations:
            raise ConstitutionalViolation(
                "No file observations available for structure analysis."
            )

        root_path = observations[0].base_path
        root_node = PathNode(
            absolute_path=root_path,
            relative_path=pathlib.Path("."),
            node_type=NodeType.DIRECTORY,
            size_bytes=0,  # Directory size calculated later
            modification_time=None,
        )

        tree = DirectoryTree(root=root_node, depth=0)

        # Group observations by directory
        dir_structure: dict[pathlib.Path, list[FileSight]] = collections.defaultdict(
            list
        )

        for obs in observations:
            if obs.relative_path:
                parent = obs.relative_path.parent
                dir_structure[parent].append(obs)

        # Build tree recursively
        self._build_subtree(tree, pathlib.Path("."), dir_structure)

        return tree

    def _build_subtree(
        self,
        parent_tree: DirectoryTree,
        current_dir: pathlib.Path,
        dir_structure: dict[pathlib.Path, list[FileSight]],
    ) -> None:
        """Recursively build subtree without inference."""
        # Get observations for this directory
        observations = dir_structure.get(current_dir, [])

        # Process subdirectories first
        subdirs: set[pathlib.Path] = set()

        for obs in observations:
            if obs.is_directory:
                subdir = current_dir / obs.relative_path.name
                subdirs.add(subdir)

        # Create subtree for each subdirectory
        for subdir in sorted(subdirs):  # Sort for deterministic output only
            dir_node = PathNode(
                absolute_path=self.snapshot.root_path / subdir,
                relative_path=subdir,
                node_type=NodeType.DIRECTORY,
                size_bytes=0,
                modification_time=None,
            )

            child_tree = DirectoryTree(root=dir_node, depth=parent_tree.depth + 1)
            parent_tree.add_child(child_tree)
            self._build_subtree(child_tree, subdir, dir_structure)

        # Add files in this directory
        for obs in observations:
            if not obs.is_directory:
                node_type = self._determine_node_type(obs)

                file_node = PathNode(
                    absolute_path=obs.absolute_path,
                    relative_path=current_dir / obs.relative_path.name,
                    node_type=node_type,
                    size_bytes=obs.size_bytes,
                    modification_time=obs.modification_time,
                    file_extension=obs.extension,
                    line_count=obs.line_count if hasattr(obs, "line_count") else None,
                    encoding=obs.encoding if hasattr(obs, "encoding") else None,
                )
                parent_tree.add_child(file_node)

    def _determine_node_type(self, observation: FileSight) -> NodeType:
        """Determine node type from observable attributes only.

        Constitutional: No inference about file purpose or content.
        """
        # Check if it's a symlink (observable attribute)
        if observation.is_symlink:
            return NodeType.SYMLINK

        # Check extension (observable attribute)
        if observation.extension == ".py":
            return NodeType.PYTHON_FILE

        # Check if it appears to be text (observable via encoding)
        if observation.encoding and observation.encoding.lower().startswith("utf"):
            return NodeType.TEXT_FILE

        # Check if binary (observable via null bytes or encoding)
        if observation.is_binary:
            return NodeType.BINARY_FILE

        # Default to other
        return NodeType.OTHER_FILE

    def _calculate_depth_distribution(self, tree: DirectoryTree) -> dict[int, int]:
        """Calculate how many nodes at each depth.

        Constitutional: Only counts, no "deep/shallow" judgments.
        """
        distribution: collections.defaultdict[int, int] = collections.defaultdict(int)

        for depth, node in tree.walk():
            if isinstance(node, DirectoryTree):
                pass
            else:
                pass

            distribution[depth] += 1

        return dict(distribution)

    def _calculate_size_distribution(self, tree: DirectoryTree) -> dict[str, list[int]]:
        """Collect file sizes by type.

        Constitutional: Raw numbers only, no statistics or summaries.
        """
        distribution: collections.defaultdict[str, list[int]] = collections.defaultdict(
            list
        )

        for _, node in tree.walk():
            if isinstance(node, DirectoryTree):
                continue

            # Add size for this file type
            distribution[node.node_type.name].append(node.size_bytes)

        return dict(distribution)

    def _count_file_types(self, tree: DirectoryTree) -> dict[str, int]:
        """Count files by observable type.

        Constitutional: Only count actual file extensions, not categories.
        """
        extensions: Counter[str] = collections.Counter()

        for _, node in tree.walk():
            if isinstance(node, DirectoryTree):
                continue

            if node.file_extension:
                extensions[node.file_extension] += 1
            else:
                extensions["(none)"] += 1

        return dict(extensions)


class StructureQuestions:
    """Answers "What exists?" with pure description."""

    def __init__(self, analyzer: StructureAnalyzer):
        self.analyzer = analyzer

    def ask_about_structure(self, snapshot: Snapshot) -> StructureAnalysis:
        """Describe what exists in the snapshot."""
        return self.analyzer.analyze()

    def get_file_counts(self, snapshot: Snapshot) -> dict[str, int]:
        """Get counts by file type."""
        analysis = self.analyzer.analyze()
        return analysis.file_type_counts


class ConstitutionalViolation(Exception):
    """Exception raised when constitutional rules are violated."""

    def __init__(self, message: str, tier: int = 1):
        super().__init__(message)
        self.tier = tier
        self.message = message

        # Constitutional: Log violations for audit
        self._log_violation()

    def _log_violation(self) -> None:
        """Log constitutional violation."""
        import logging

        logger = logging.getLogger("codemarshal.structure")
        logger.error(f"Constitutional Violation (Tier {self.tier}): {self.message}")


# Utility functions for common structure questions
def get_file_list_by_extension(
    analysis: StructureAnalysis, extension: str
) -> list[dict[str, Any]]:
    """Get files with specific extension without inference.

    Constitutional: No judgment about which extensions are "important".
    """
    files = analysis.get_flat_file_list()
    return [file for file in files if file.get("file_extension") == extension]


def get_largest_directories(
    analysis: StructureAnalysis, count: int = 10
) -> list[tuple[str, int]]:
    """Get directories by size without labeling them.

    Constitutional: No "bloated" or "large" labels, just sizes.
    """
    sizes = analysis.get_directory_sizes()
    sorted_sizes = sorted(sizes.items(), key=lambda x: x[1], reverse=True)
    return sorted_sizes[:count]


def export_structure_report(
    analysis: StructureAnalysis, output_path: pathlib.Path
) -> None:
    """Export structure analysis as JSON.

    Constitutional: Raw data only, no narrative or interpretation.
    """
    report = analysis.to_dict()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


# Example usage (for testing only)
def analyze_example_structure(root_path: pathlib.Path) -> StructureAnalysis:
    """Example function to demonstrate usage.

    Not for production - would require actual snapshot.
    """
    # This is a placeholder - in production, you'd get a real snapshot
    from observations.record.snapshot import create_snapshot

    snapshot = create_snapshot(root_path)
    analyzer = StructureAnalyzer(snapshot)
    return analyzer.analyze()


# Export public API
__all__ = [
    "NodeType",
    "PathNode",
    "DirectoryTree",
    "StructureAnalysis",
    "StructureAnalyzer",
    "ConstitutionalViolation",
    "get_file_list_by_extension",
    "get_largest_directories",
    "export_structure_report",
]
