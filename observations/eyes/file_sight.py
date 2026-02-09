"""
file_sight.py - Filesystem observation without interpretation

Purpose:
Answers the question: "What files and directories exist, and what are their raw properties?"

Absolute Rules:
1. Never writes to filesystem
2. Never executes code
3. Never follows symlinks by default
4. Never modifies observed state
5. Never infers meaning from filenames
"""

import hashlib
import platform
import stat
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from pathlib import Path, PurePath
from typing import Any, NamedTuple

from .base import AbstractEye, ObservationResult


class FileType(Enum):
    """Immutable classification of filesystem entries."""

    FILE = auto()
    DIRECTORY = auto()
    SYMLINK = auto()
    BLOCK_DEVICE = auto()
    CHARACTER_DEVICE = auto()
    FIFO = auto()
    SOCKET = auto()
    UNKNOWN = auto()

    @classmethod
    def from_stat_mode(cls, mode: int) -> "FileType":
        """Derive file type from stat mode, no inference."""
        if stat.S_ISREG(mode):
            return cls.FILE
        elif stat.S_ISDIR(mode):
            return cls.DIRECTORY
        elif stat.S_ISLNK(mode):
            return cls.SYMLINK
        elif stat.S_ISBLK(mode):
            return cls.BLOCK_DEVICE
        elif stat.S_ISCHR(mode):
            return cls.CHARACTER_DEVICE
        elif stat.S_ISFIFO(mode):
            return cls.FIFO
        elif stat.S_ISSOCK(mode):
            return cls.SOCKET
        return cls.UNKNOWN


class PermissionSet(NamedTuple):
    """Bitwise POSIX permissions, immutable."""

    user_read: bool
    user_write: bool
    user_execute: bool
    group_read: bool
    group_write: bool
    group_execute: bool
    other_read: bool
    other_write: bool
    other_execute: bool

    @classmethod
    def from_mode(cls, mode: int) -> "PermissionSet":
        """Extract permissions from stat mode."""
        return cls(
            user_read=bool(mode & stat.S_IRUSR),
            user_write=bool(mode & stat.S_IWUSR),
            user_execute=bool(mode & stat.S_IXUSR),
            group_read=bool(mode & stat.S_IRGRP),
            group_write=bool(mode & stat.S_IWGRP),
            group_execute=bool(mode & stat.S_IXGRP),
            other_read=bool(mode & stat.S_IROTH),
            other_write=bool(mode & stat.S_IWOTH),
            other_execute=bool(mode & stat.S_IXOTH),
        )

    @property
    def octal_string(self) -> str:
        """Represent as octal string (e.g., '0644')."""
        octet = 0
        if self.user_read:
            octet |= 0o400
        if self.user_write:
            octet |= 0o200
        if self.user_execute:
            octet |= 0o100
        if self.group_read:
            octet |= 0o040
        if self.group_write:
            octet |= 0o020
        if self.group_execute:
            octet |= 0o010
        if self.other_read:
            octet |= 0o004
        if self.other_write:
            octet |= 0o002
        if self.other_execute:
            octet |= 0o001
        return f"0o{octet:03o}"


@dataclass(frozen=True)
class FileMetadata:
    """Complete, immutable file metadata observation."""

    path: PurePath
    resolved_path: PurePath | None = None  # If symlink resolved
    file_type: FileType = FileType.UNKNOWN
    size_bytes: int = 0
    inode_number: int = 0

    # Timestamps (timezone-aware UTC)
    access_time: datetime | None = None
    modification_time: datetime | None = None
    creation_time: datetime | None = None

    # Permissions
    permissions: PermissionSet | None = None
    uid: int | None = None
    gid: int | None = None

    # Content fingerprint
    content_hash: str | None = None  # SHA256 of content
    hash_algorithm: str = "sha256"

    # Platform-specific (recorded, not interpreted)
    is_hidden: bool = False

    # Errors encountered during observation
    observation_errors: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate invariants."""
        if self.size_bytes < 0:
            raise ValueError(f"Negative file size: {self.size_bytes}")
        if self.inode_number < 0:
            raise ValueError(f"Negative inode: {self.inode_number}")
        if self.content_hash and len(self.content_hash) != 64:
            raise ValueError(f"Invalid SHA256 hash length: {self.content_hash}")


@dataclass(frozen=True)
class DirectoryTree:
    """Immutable snapshot of directory structure. Fully hashable."""

    root_path: PurePath
    timestamp: datetime
    files: tuple[tuple[PurePath, FileMetadata], ...] = field(default_factory=tuple)
    directories: tuple[PurePath, ...] = field(default_factory=tuple)
    symlinks: tuple[PurePath, ...] = field(default_factory=tuple)
    errors: tuple[tuple[PurePath, tuple[str, ...]], ...] = field(default_factory=tuple)

    @property
    def total_size_bytes(self) -> int:
        """Sum of all file sizes (excluding directories)."""
        return sum(f.size_bytes for _, f in self.files)

    @property
    def total_files(self) -> int:
        """Count of regular files (excluding directories/symlinks)."""
        return len([f for _, f in self.files if f.file_type == FileType.FILE])


class TraversalConfig(NamedTuple):
    """Immutable configuration for filesystem traversal."""

    max_depth: int = 100
    follow_symlinks: bool = False
    compute_hashes: bool = True
    hash_limit_mb: int = 100  # Don't hash files larger than this
    exclude_patterns: tuple[str, ...] = ()
    respect_gitignore: bool = False
    skip_hidden: bool = True


class FileSight(AbstractEye):
    """
    Observes filesystem structure without interpretation.

    Core Guarantees:
    1. Zero writes to filesystem
    2. Deterministic traversal order
    3. No code execution
    4. No environment-specific assumptions
    5. Clear error reporting for permission issues
    """

    VERSION = "1.0.0"

    def __init__(self, config: TraversalConfig | None = None) -> None:
        super().__init__(name="file_sight", version=self.VERSION)
        self.config = config or TraversalConfig()
        self._platform = platform.system().lower()

    def get_capabilities(self) -> dict[str, Any]:
        """Explicitly declare capabilities for validation."""
        return {
            "name": self.name,
            "version": self.version,
            "deterministic": True,
            "side_effect_free": True,
            "max_depth": self.config.max_depth,
            "supports_hashing": self.config.compute_hashes,
        }

    def observe(self, target: str | Path) -> ObservationResult:
        """Public API: Observe filesystem structure starting at target."""
        path = Path(target) if isinstance(target, str) else target
        return self._observe_with_timing(path)

    def _observe_impl(self, target: str | Path) -> ObservationResult:
        """
        Observe filesystem structure starting at target.

        Args:
            target: Path to file or directory to observe

        Returns:
            ObservationResult containing directory tree

        Raises:
            FileNotFoundError: If target doesn't exist
            PermissionError: If cannot access target (not caught)
        """
        path = Path(target) if isinstance(target, str) else target
        path = path.resolve()

        if not path.exists():
            raise FileNotFoundError(f"Target does not exist: {path}")

        timestamp = datetime.now(UTC)

        try:
            if path.is_file():
                tree = self._observe_single_file(path, timestamp)
            else:
                tree = self._observe_directory_tree(path, timestamp)

            # Calculate confidence based on error ratio
            total_items = len(tree.files) + len(tree.directories) + len(tree.symlinks)
            error_items = len(tree.errors)
            confidence = 1.0 - (error_items / max(total_items, 1))

            return ObservationResult(
                source=str(path),
                timestamp=timestamp,
                version=self.VERSION,
                confidence=confidence,
                raw_payload=tree,
            )

        except (PermissionError, OSError) as e:
            # Permission errors at root level are fatal
            error_tree = DirectoryTree(
                root_path=path,
                timestamp=timestamp,
                errors=((PurePath("."), (f"Root access error: {str(e)}",)),),
            )

            return ObservationResult(
                source=str(path),
                timestamp=timestamp,
                version=self.VERSION,
                confidence=0.0,
                raw_payload=error_tree,
            )

    def _observe_single_file(self, path: Path, timestamp: datetime) -> DirectoryTree:
        """Observe a single file (not a directory)."""
        metadata = self._collect_file_metadata(path, Path("."))

        tree = DirectoryTree(
            root_path=path.parent,
            timestamp=timestamp,
            files=((PurePath(path.name), metadata),) if metadata else (),
            directories=(),
            symlinks=(),
            errors=((PurePath(path.name), metadata.observation_errors),)
            if metadata and metadata.observation_errors
            else (),
        )

        return tree

    def _observe_directory_tree(self, root: Path, timestamp: datetime) -> DirectoryTree:
        """Observe directory tree with configurable depth."""
        files: dict[PurePath, FileMetadata] = {}
        directories: set[PurePath] = set()
        symlinks: set[PurePath] = set()
        errors: dict[PurePath, tuple[str, ...]] = {}

        # Add root directory
        root_metadata = self._collect_file_metadata(root, root)
        if root_metadata:
            directories.add(PurePath("."))

        # Walk the tree
        for entry_path, depth in self._walk_tree(root):
            if depth > self.config.max_depth:
                continue

            rel_path = entry_path.relative_to(root)

            try:
                metadata = self._collect_file_metadata(entry_path, root)
                if not metadata:
                    continue

                if metadata.file_type == FileType.FILE:
                    files[rel_path] = metadata
                elif metadata.file_type == FileType.DIRECTORY:
                    directories.add(rel_path)
                elif metadata.file_type == FileType.SYMLINK:
                    symlinks.add(rel_path)
                    # Only follow symlinks if explicitly configured
                    if self.config.follow_symlinks and metadata.resolved_path:
                        # Try to observe symlink target
                        target_path = Path(metadata.resolved_path)
                        if target_path.exists():
                            target_metadata = self._collect_file_metadata(
                                target_path, root
                            )
                            if target_metadata:
                                if target_metadata.file_type == FileType.FILE:
                                    files[rel_path] = target_metadata
                                elif target_metadata.file_type == FileType.DIRECTORY:
                                    directories.add(rel_path)

                if metadata.observation_errors:
                    errors[rel_path] = metadata.observation_errors

            except (OSError, PermissionError) as e:
                errors[rel_path] = (f"Access error: {str(e)}",)

        tree = DirectoryTree(
            root_path=root,
            timestamp=timestamp,
            files=tuple(files.items()),
            directories=tuple(sorted(directories)),
            symlinks=tuple(sorted(symlinks)),
            errors=tuple(errors.items()),
        )

        return tree

    def _walk_tree(self, root: Path) -> Iterator[tuple[Path, int]]:
        """
        Deterministic, depth-first traversal.
        Yields (absolute_path, depth) tuples.
        """
        from collections import deque

        stack = deque([(root, 0)])

        while stack:
            current_path, depth = stack.pop()

            try:
                entries = list(current_path.iterdir())
                # Sort for deterministic output
                entries.sort(key=lambda p: p.name.lower())

                for entry in entries:
                    if self._should_skip(entry):
                        continue

                    yield entry, depth + 1

                    # Only push directories to stack (for recursion)
                    try:
                        if entry.is_dir() and not entry.is_symlink():
                            stack.append((entry, depth + 1))
                    except (OSError, PermissionError):
                        # Can't determine if directory, skip
                        continue

            except (OSError, PermissionError):
                # Can't read directory, skip it
                continue

    def _should_skip(self, path: Path) -> bool:
        """Determine if path should be skipped based on config."""
        # Skip hidden files if configured
        if self.config.skip_hidden and self._is_hidden(path):
            return True

        # Check exclude patterns
        for pattern in self.config.exclude_patterns:
            if path.match(pattern):
                return True

        return False

    def _is_hidden(self, path: Path) -> bool:
        """Determine if file is hidden (platform-specific)."""
        if self._platform == "windows":
            import ctypes

            try:
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
                return attrs & 2  # FILE_ATTRIBUTE_HIDDEN
            except (AttributeError, OSError):
                # Fallback to name check
                return path.name.startswith(".")
        else:
            # Unix-like: hidden if starts with '.'
            return path.name.startswith(".")

    def _collect_file_metadata(self, path: Path, root: Path) -> FileMetadata | None:
        """
        Collect metadata for a single filesystem entry.
        Returns None if cannot be accessed at all.
        """
        errors: list[str] = []
        metadata = {}

        # Basic path info
        metadata["path"] = PurePath(
            path.relative_to(root) if path.is_relative_to(root) else path
        )

        try:
            # Get stat info (follow symlinks for stat if configured to follow)
            if self.config.follow_symlinks:
                stat_info = path.stat()
                metadata["file_type"] = FileType.from_stat_mode(stat_info.st_mode)
            else:
                stat_info = path.lstat()
                metadata["file_type"] = FileType.from_stat_mode(stat_info.st_mode)

            # Size and inode
            metadata["size_bytes"] = stat_info.st_size
            metadata["inode_number"] = stat_info.st_ino

            # Timestamps (convert to UTC)
            metadata["access_time"] = datetime.fromtimestamp(stat_info.st_atime, tz=UTC)
            metadata["modification_time"] = datetime.fromtimestamp(
                stat_info.st_mtime, tz=UTC
            )

            # Creation time (platform-dependent)
            try:
                ctime = stat_info.st_ctime
                metadata["creation_time"] = datetime.fromtimestamp(ctime, tz=UTC)
            except (AttributeError, OSError):
                metadata["creation_time"] = None

            # Permissions and ownership
            metadata["permissions"] = PermissionSet.from_mode(stat_info.st_mode)
            metadata["uid"] = stat_info.st_uid
            metadata["gid"] = stat_info.st_gid

            # Handle symlinks
            if metadata["file_type"] == FileType.SYMLINK:
                try:
                    target = path.readlink()
                    metadata["resolved_path"] = PurePath(target)
                except (OSError, PermissionError) as e:
                    errors.append(f"Cannot read symlink target: {str(e)}")

            # Content hash (for regular files)
            if (
                metadata["file_type"] == FileType.FILE
                and self.config.compute_hashes
                and metadata["size_bytes"] <= self.config.hash_limit_mb * 1024 * 1024
            ):
                try:
                    metadata["content_hash"] = self._compute_file_hash(path)
                except (OSError, PermissionError, MemoryError) as e:
                    errors.append(f"Cannot compute hash: {str(e)}")

            # Hidden flag
            metadata["is_hidden"] = self._is_hidden(path)

        except (OSError, PermissionError) as e:
            errors.append(f"Cannot stat file: {str(e)}")

        if errors:
            metadata["observation_errors"] = tuple(errors)

        return FileMetadata(**metadata) if metadata else None

    def _compute_file_hash(self, path: Path) -> str:
        """Compute SHA256 hash of file content."""
        sha256 = hashlib.sha256()

        # Read in chunks to handle large files
        chunk_size = 65536  # 64KB

        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    sha256.update(chunk)
        except (OSError, MemoryError) as e:
            raise OSError(f"Cannot read file for hashing: {str(e)}") from e

        return sha256.hexdigest()

    def validate(self) -> bool:
        """Validate that this eye follows observation purity rules."""
        # Check for prohibited imports
        prohibited_imports = {
            "shu" + "til",  # File operations
            "sub" + "process",  # Code execution
            "os.sys" + "tem",
            "os.po" + "pen",  # Shell commands
            "import" + "lib",
            "run" + "py",  # Code loading
        }

        # Check this file's source
        current_file = Path(__file__).resolve()
        with open(current_file, encoding="utf-8") as f:
            content = f.read()

        for prohibited in prohibited_imports:
            if f"import {prohibited}" in content or f"from {prohibited}" in content:
                return False

        # Ensure no write operations
        write_operations = {
            ".wri" + "te(",
            ".write" + "lines(",
            "open(" + '"w")',
            "open(" + '"a")',
            ".mkd" + "ir(",
            ".rmd" + "ir(",
            ".unl" + "ink(",
            ".ren" + "ame(",
            ".tou" + "ch(",
            ".chm" + "od(",
            ".cho" + "wn(",
        }

        for op in write_operations:
            if op in content:
                return False

        return True


# Convenience functions for common use cases


def observe_file(file_path: str | Path) -> FileMetadata | None:
    """Observe single file metadata."""
    sight = FileSight()
    path = Path(file_path) if isinstance(file_path, str) else file_path

    if not path.is_file():
        return None

    result = sight.observe(path)
    if not isinstance(result.raw_payload, DirectoryTree):
        return None

    tree: DirectoryTree = result.raw_payload
    if tree.files:
        # Return metadata for the single file
        return tree.files[0][1]
    return None


def observe_directory(
    dir_path: str | Path, max_depth: int = 3, follow_symlinks: bool = False
) -> DirectoryTree:
    """Convenience function for directory observation."""
    config = TraversalConfig(
        max_depth=max_depth, follow_symlinks=follow_symlinks, compute_hashes=True
    )
    sight = FileSight(config)
    path = Path(dir_path) if isinstance(dir_path, str) else dir_path
    result = sight.observe(path)
    return result.raw_payload
