"""
ATOMIC WRITE GUARANTEES

Enforces that partial truth never exists in storage.
Either a write completes fully, or it never happened.

This module is deliberately boring by design - that's the compliment.

Constitutional Rules:
1. No partial writes visible to readers
2. No silent data corruption
3. No platform-specific surprises
4. No validation or business logic
"""

import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Any, BinaryIO, TextIO, cast

# Platform detection for cross-platform safety
IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")
IS_MACOS = sys.platform.startswith("darwin")


class AtomicWriteError(Exception):
    """Base exception for atomic write failures."""

    pass


class TempFileCreationError(AtomicWriteError):
    """Failed to create temporary file for atomic write."""

    pass


class SyncError(AtomicWriteError):
    """Failed to sync data to disk."""

    pass


class AtomicRenameError(AtomicWriteError):
    """Failed to rename temporary file to target."""

    pass


class AtomicReadError(Exception):
    """Base exception for atomic read failures."""

    pass


def _ensure_parent_dir_exists(target_path: Path) -> None:
    """
    Ensure parent directory exists without creating intermediate directories.

    Raises:
        FileNotFoundError: If parent directory doesn't exist
        PermissionError: If no permission to check directory
    """
    parent = target_path.parent
    if not parent.exists():
        raise FileNotFoundError(
            f"Parent directory does not exist: {parent}. "
            "Storage layout must create directories before atomic writes."
        )
    if not os.access(str(parent), os.W_OK):
        raise PermissionError(f"No write permission for directory: {parent}")


def _create_temp_file_in_same_dir(target_path: Path, suffix: str = ".tmp") -> Path:
    """
    Create a temporary file in the same directory as target.

    This ensures atomic rename works (same filesystem).
    """
    try:
        # Create in same directory for atomic rename guarantee
        parent_dir = target_path.parent
        fd, temp_path = tempfile.mkstemp(
            suffix=suffix, dir=str(parent_dir), prefix=f".{target_path.name}."
        )
        os.close(fd)  # We'll reopen with proper mode
        return Path(temp_path)
    except OSError as e:
        raise TempFileCreationError(
            f"Failed to create temporary file in {target_path.parent}: {e}"
        ) from e


def _sync_file(fd: int) -> None:
    """
    Force file data to physical storage.

    Args:
        fd: File descriptor to sync

    Raises:
        SyncError: If sync fails
    """
    try:
        # First flush Python buffers and commit data to file system buffers
        os.fsync(fd)

        # Directory sync logic is handled by the caller functions (atomic_write_binary
        # and AtomicWriter.__exit__) as they have access to the Path object.

    except OSError as e:
        raise SyncError(f"Failed to sync file descriptor {fd}: {e}") from e


def atomic_read_binary(target_path: str | Path) -> bytes:
    """Atomically read binary data from a file.

    Args:
        target_path: Path to file to read

    Returns:
        Raw bytes from file

    Raises:
        AtomicReadError: If read operation fails
    """
    target_path = Path(target_path)

    if not target_path.exists():
        raise AtomicReadError(f"File does not exist: {target_path}")

    if not target_path.is_file():
        raise AtomicReadError(f"Path is not a file: {target_path}")

    try:
        # Open file and read all data
        with open(target_path, "rb") as f:
            return f.read()
    except OSError as e:
        raise AtomicReadError(f"Failed to read file {target_path}: {e}") from e


def atomic_read(target_path: str | Path) -> bytes:
    """Backward-compatible alias for atomic_read_binary."""
    return atomic_read_binary(target_path)


def atomic_write_binary(
    target_path: str | Path, data: bytes, *, suffix: str = ".tmp"
) -> None:
    """
    Write binary data atomically.

    Either the entire file is written, or no file exists.
    """
    target_path = Path(target_path)

    # Step 1: Verify parent directory exists
    _ensure_parent_dir_exists(target_path)

    # Step 2: Create temporary file in same directory
    temp_path = _create_temp_file_in_same_dir(target_path, suffix)

    try:
        # Step 3: Write data to temporary file
        with open(temp_path, "wb") as f:
            f.write(data)
            f.flush()

            # Step 4: Force data to physical storage
            _sync_file(f.fileno())

        # Step 5: Atomic rename (replaces if exists)
        os.replace(str(temp_path), str(target_path))

        # Step 6: Sync directory entry (on non-Windows)
        # This is the original, correct directory sync logic you provided.
        if not IS_WINDOWS:
            parent_fd = os.open(str(target_path.parent), os.O_RDONLY)
            try:
                os.fsync(parent_fd)
            finally:
                os.close(parent_fd)

    except Exception as e:
        # Clean up temporary file on any error
        try:
            if temp_path.exists():
                temp_path.unlink()
        except OSError:
            pass

        # Re-raise with appropriate exception type
        if isinstance(e, (OSError, IOError)):
            if isinstance(e, AtomicWriteError):
                raise
            raise AtomicWriteError(f"Atomic write failed: {e}") from e
        raise


def atomic_write_text(
    target_path: str | Path, text: str, *, encoding: str = "utf-8", suffix: str = ".tmp"
) -> None:
    """
    Write text data atomically.
    """
    try:
        data = text.encode(encoding)
    except UnicodeEncodeError as e:
        raise AtomicWriteError(f"Failed to encode text as {encoding}: {e}") from e

    atomic_write_binary(target_path, data, suffix=suffix)


def atomic_write(
    target_path: str | Path, text: str, *, encoding: str = "utf-8", suffix: str = ".tmp"
) -> None:
    """Backward-compatible alias for atomic_write_text."""
    atomic_write_text(target_path, text, encoding=encoding, suffix=suffix)


def atomic_write_json_compatible(
    target_path: str | Path,
    data: dict[str, Any] | list[Any] | str | int | float | bool | None,
    *,
    indent: int | None = 2,
    suffix: str = ".tmp",
) -> None:
    """
    Write JSON-compatible data atomically.
    """
    import json
    from pathlib import Path as PathType

    # Custom JSON encoder to handle Path objects
    class PathEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, PathType):
                return str(obj)
            return super().default(obj)

    try:
        json_text = json.dumps(data, indent=indent, ensure_ascii=False, cls=PathEncoder)
    except (TypeError, ValueError) as e:
        raise AtomicWriteError(f"Data cannot be serialized to JSON: {e}") from e

    atomic_write_text(target_path, json_text, suffix=suffix)


class AtomicWriter:
    """
    Context manager for streaming atomic writes.
    """

    def __init__(
        self,
        target_path: str | Path,
        *,
        mode: str = "wb",
        suffix: str = ".tmp",
        **open_kwargs: Any,
    ):
        """
        Initialize atomic writer.
        """
        if "w" not in mode and "x" not in mode and "a" not in mode:
            raise ValueError(f"Mode must be write mode, got: {mode}")

        self.target_path = Path(target_path)
        self.mode = mode
        self.suffix = suffix
        self.open_kwargs = open_kwargs
        self.temp_path: Path | None = None
        self.file_handle: BinaryIO | TextIO | None = None

    def __enter__(self) -> BinaryIO | TextIO:
        # Ensure parent directory exists
        _ensure_parent_dir_exists(self.target_path)

        # Create temporary file
        self.temp_path = _create_temp_file_in_same_dir(self.target_path, self.suffix)

        # Open temporary file with specified mode
        file_handle = open(self.temp_path, self.mode, **self.open_kwargs)

        # Use `cast` to satisfy Pylance that the generic IO[Any] is one of the types in the Union.
        self.file_handle = cast(BinaryIO | TextIO, file_handle)

        return self.file_handle

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if self.file_handle is not None:
            try:
                # Flush and sync data before closing/renaming
                self.file_handle.flush()
                if hasattr(self.file_handle, "fileno"):
                    _sync_file(self.file_handle.fileno())
            except OSError as e:
                # Sync failure should not mask original exception if present
                if exc_type is None:
                    raise AtomicWriteError(
                        f"Failed to sync file data before commit: {e}"
                    ) from e

            self.file_handle.close()

        if exc_type is not None:
            # Error occurred - clean up temporary file
            if self.temp_path and self.temp_path.exists():
                try:
                    self.temp_path.unlink()
                except OSError:
                    pass
            return False

        # No error - commit the file
        if self.temp_path and self.temp_path.exists():
            try:
                os.replace(str(self.temp_path), str(self.target_path))

                # Restore original directory sync logic for AtomicWriter
                if not IS_WINDOWS:
                    parent_fd = os.open(str(self.target_path.parent), os.O_RDONLY)
                    try:
                        os.fsync(parent_fd)
                    finally:
                        os.close(parent_fd)

            except OSError as e:
                # Clean up on commit failure
                try:
                    self.temp_path.unlink()
                except OSError:
                    pass
                raise AtomicWriteError(f"Failed to commit atomic write: {e}") from e

        return False


@dataclass
class AtomicWriteResult:
    succeeded: bool
    error: Exception | None = None


@dataclass
class AtomicReadResult:
    is_valid: bool
    data_bytes: bytes | None = None
    error: Exception | None = None


def write_atomic(
    path: str | Path, content: Any, indent: int | None = 2
) -> AtomicWriteResult:
    """Wrapper for atomic write operations."""
    try:
        if isinstance(content, str):
            atomic_write_text(path, content)
        elif isinstance(content, bytes):
            atomic_write_binary(path, content)
        else:
            atomic_write_json_compatible(path, content, indent=indent)
        return AtomicWriteResult(True)
    except Exception as e:
        return AtomicWriteResult(False, e)


def read_atomic(path: str | Path) -> AtomicReadResult:
    """Safe read operation representing content as bytes."""
    try:
        path = Path(path)
        if not path.exists():
            return AtomicReadResult(
                False, None, FileNotFoundError(f"{path} does not exist")
            )
        try:
            # Always read bytes
            data = path.read_bytes()
            return AtomicReadResult(True, data)
        except Exception as e:
            return AtomicReadResult(False, None, e)
    except Exception as e:
        return AtomicReadResult(False, None, e)


# Export public API
__all__ = [
    "AtomicWriteError",
    "TempFileCreationError",
    "SyncError",
    "AtomicRenameError",
    "atomic_write_binary",
    "atomic_write_text",
    "atomic_write_json_compatible",
    "AtomicWriter",
    "IS_WINDOWS",
    "IS_LINUX",
    "IS_MACOS",
    "AtomicWriteResult",
    "AtomicReadResult",
    "write_atomic",
    "read_atomic",
]
