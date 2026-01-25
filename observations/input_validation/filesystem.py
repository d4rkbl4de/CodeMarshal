# observations/input_validation\filesystem.py
"""
Filesystem validation: symlink, traversal, and root confinement rules.

Defines where the system is allowed to look.
Rejects paths that escape boundaries before any observation occurs.
"""

import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)


class FilesystemValidationError(Exception):
    """Base exception for filesystem validation failures."""

    pass


class SymlinkViolationError(FilesystemValidationError):
    """Raised when symlink policy is violated."""

    pass


class TraversalViolationError(FilesystemValidationError):
    """Raised when path traversal attempts to escape root boundary."""

    pass


class CycleDetectionError(FilesystemValidationError):
    """Raised when a path cycle is detected."""

    pass


@dataclass(frozen=True)
class FilesystemPolicy:
    """
    Policy configuration for filesystem access.

    These policies are applied BEFORE any file reading occurs.
    """

    # Whether to follow symlinks at all
    allow_symlinks: bool = False

    # Maximum symlink chain length (0 = no symlinks, 1 = single symlink, etc.)
    max_symlink_depth: int = 0

    # Whether to resolve symlinks when checking boundaries
    resolve_symlinks_for_boundary_check: bool = True

    # Maximum directory traversal depth from root
    max_traversal_depth: int = 50

    # Whether to allow traversal above investigation root (should be False)
    allow_escape_root: bool = False

    # List of allowed symlink targets (if empty, all within root are allowed when symlinks enabled)
    allowed_symlink_targets: set[Path] = field(default_factory=lambda: set())

    # Whether to check for hardlink cycles
    check_hardlink_cycles: bool = True

    @classmethod
    def strict(cls) -> "FilesystemPolicy":
        """Return the strictest possible policy (no symlinks, no escape)."""
        return cls(
            allow_symlinks=False,
            max_symlink_depth=0,
            allow_escape_root=False,
            check_hardlink_cycles=True,
        )

    @classmethod
    def lenient(cls) -> "FilesystemPolicy":
        """Return a more lenient policy (limited symlinks allowed)."""
        return cls(
            allow_symlinks=True,
            max_symlink_depth=5,
            allow_escape_root=False,
            check_hardlink_cycles=True,
        )

    def validate(self) -> None:
        """Validate policy configuration is sane."""
        if self.max_symlink_depth < 0:
            raise ValueError("max_symlink_depth cannot be negative")
        if self.max_traversal_depth < 1:
            raise ValueError("max_traversal_depth must be at least 1")
        if self.allow_symlinks and self.max_symlink_depth == 0:
            raise ValueError(
                "max_symlink_depth must be > 0 when allow_symlinks is True"
            )


class FilesystemValidator:
    """
    Validates filesystem paths against security and boundary constraints.

    This ensures the system only looks where it's allowed to look.
    A rejected path is a hard stop for that path.
    """

    def __init__(
        self, investigation_root: Path, policy: FilesystemPolicy | None = None
    ) -> None:
        """
        Initialize the validator with an investigation root and policy.

        Args:
            investigation_root: The root directory of the investigation.
                All paths must be contained within this root.
            policy: Filesystem access policy. Uses strict policy if None.

        Raises:
            ValueError: If investigation_root is not an absolute path or doesn't exist.
        """
        # Validate and resolve investigation root
        if not investigation_root.is_absolute():
            raise ValueError(
                f"investigation_root must be absolute: {investigation_root}"
            )

        try:
            self._root: Path = investigation_root.resolve(strict=True)
        except (FileNotFoundError, PermissionError) as e:
            raise ValueError(
                f"Cannot resolve investigation_root {investigation_root}: {e}"
            ) from e

        # Set policy
        self._policy: FilesystemPolicy = policy or FilesystemPolicy.strict()
        self._policy.validate()

        # State tracking for cycle detection
        self._visited_symlinks: set[Path] = set()
        self._visited_hardlinks: dict[int, set[Path]] = {}

        logger.debug(
            f"FilesystemValidator initialized with root: {self._root}, "
            f"policy: symlinks={self._policy.allow_symlinks}, "
            f"max_depth={self._policy.max_symlink_depth}"
        )

    def reset(self) -> None:
        """Reset all state tracking for a new investigation."""
        self._visited_symlinks.clear()
        self._visited_hardlinks.clear()
        logger.debug("FilesystemValidator reset")

    @property
    def root(self) -> Path:
        """Get the investigation root (read-only)."""
        return self._root

    @property
    def policy(self) -> FilesystemPolicy:
        """Get the current policy (read-only)."""
        return self._policy

    def validate_path(self, path: Path, require_exists: bool = True) -> dict[str, Any]:
        """
        Validate a single path against all filesystem constraints.

        This is the main validation method that applies all checks in order:
        1. Path normalization
        2. Root confinement
        3. Symlink policy
        4. Cycle detection
        5. Traversal depth

        Args:
            path: The path to validate.
            require_exists: Whether the path must exist. If False, only
                structural validation is performed.

        Returns:
            Dictionary with validation results:
                - "valid": bool - Whether path passes all checks
                - "canonical_path": Optional[Path] - Canonical path if valid
                - "reason": Optional[str] - If invalid, why
                - "violation": Optional[str] - Type of violation
                - "symlink_chain": List[Path] - Chain of symlinks if applicable

        Raises:
            FilesystemValidationError: If validation fails (alternative to dict return).
        """
        # Convert to absolute path relative to root if needed
        if not path.is_absolute():
            absolute_path = (self._root / path).resolve()
        else:
            absolute_path = path

        # Check if path exists (if required)
        if require_exists:
            try:
                # Use strict=False to avoid following symlinks for existence check
                absolute_path.resolve(strict=False)
            except (FileNotFoundError, PermissionError) as e:
                return {
                    "valid": False,
                    "canonical_path": None,
                    "reason": f"Path does not exist or cannot be accessed: {e}",
                    "violation": "nonexistent",
                    "symlink_chain": [],
                }

        # Normalize and check root confinement
        try:
            normalized = self._normalize_path(absolute_path)
        except TraversalViolationError as e:
            return {
                "valid": False,
                "canonical_path": None,
                "reason": str(e),
                "violation": "root_escape",
                "symlink_chain": [],
            }

        # Check symlink policy
        symlink_chain: list[Path] = []
        try:
            if self._policy.allow_symlinks:
                symlink_chain = self._validate_symlinks(normalized)
            else:
                self._reject_symlinks(normalized)
        except SymlinkViolationError as e:
            return {
                "valid": False,
                "canonical_path": None,
                "reason": str(e),
                "violation": "symlink",
                "symlink_chain": [],
            }

        # Check for cycles
        try:
            self._detect_cycles(normalized, symlink_chain)
        except CycleDetectionError as e:
            return {
                "valid": False,
                "canonical_path": None,
                "reason": str(e),
                "violation": "cycle",
                "symlink_chain": symlink_chain,
            }

        # Check traversal depth
        try:
            self._check_traversal_depth(normalized)
        except TraversalViolationError as e:
            return {
                "valid": False,
                "canonical_path": None,
                "reason": str(e),
                "violation": "traversal_depth",
                "symlink_chain": symlink_chain,
            }

        # All checks passed
        return {
            "valid": True,
            "canonical_path": normalized,
            "reason": None,
            "violation": None,
            "symlink_chain": symlink_chain,
        }

    def validate_directory(
        self, dir_path: Path, check_contents: bool = True
    ) -> dict[str, Any]:
        """
        Validate a directory and optionally its contents.

        Args:
            dir_path: Directory path to validate.
            check_contents: Whether to validate that directory contents
                would also be valid (non-recursive check).

        Returns:
            Dictionary with validation results plus:
                - "is_directory": bool
                - "valid_contents": Optional[List[Path]] - List of valid child paths
                - "invalid_contents": Optional[List[Dict]] - List of invalid children with reasons
        """
        # First validate the directory itself
        base_result = self.validate_path(dir_path, require_exists=True)

        if not base_result["valid"]:
            base_result.update(
                {
                    "is_directory": False,
                    "valid_contents": None,
                    "invalid_contents": None,
                }
            )
            return base_result

        canonical_path = base_result["canonical_path"]
        if canonical_path is None:
            # This shouldn't happen if valid is True, but be defensive
            base_result.update(
                {
                    "valid": False,
                    "reason": "Internal error: canonical_path is None",
                    "is_directory": False,
                    "valid_contents": None,
                    "invalid_contents": None,
                }
            )
            return base_result

        # Check it's actually a directory
        if not canonical_path.is_dir():
            return {
                "valid": False,
                "canonical_path": canonical_path,
                "reason": "Path is not a directory",
                "violation": "not_directory",
                "symlink_chain": base_result["symlink_chain"],
                "is_directory": False,
                "valid_contents": None,
                "invalid_contents": None,
            }

        # If checking contents, validate immediate children
        valid_contents: list[Path] = []
        invalid_contents: list[dict[str, Any]] = []

        if check_contents:
            try:
                # Use os.scandir for better performance and to avoid following symlinks
                with os.scandir(canonical_path) as entries:
                    for entry in entries:
                        entry_path = Path(entry.path)

                        # Quick check: is it within root?
                        try:
                            entry_path.relative_to(self._root)
                        except ValueError:
                            # Outside root
                            invalid_contents.append(
                                {
                                    "path": entry_path,
                                    "reason": "Outside investigation root",
                                    "violation": "root_escape",
                                }
                            )
                            continue

                        # Full validation
                        validation = self.validate_path(
                            entry_path, require_exists=False
                        )
                        if validation["valid"]:
                            valid_contents.append(entry_path)
                        else:
                            invalid_contents.append(
                                {
                                    "path": entry_path,
                                    "reason": validation["reason"],
                                    "violation": validation["violation"],
                                }
                            )
            except (PermissionError, OSError) as e:
                # Can't read directory contents
                return {
                    "valid": False,
                    "canonical_path": canonical_path,
                    "reason": f"Cannot read directory contents: {e}",
                    "violation": "permission",
                    "symlink_chain": base_result["symlink_chain"],
                    "is_directory": True,
                    "valid_contents": None,
                    "invalid_contents": None,
                }

        # All checks passed
        return {
            "valid": True,
            "canonical_path": canonical_path,
            "reason": None,
            "violation": None,
            "symlink_chain": base_result["symlink_chain"],
            "is_directory": True,
            "valid_contents": valid_contents,
            "invalid_contents": invalid_contents,
        }

    def _normalize_path(self, path: Path) -> Path:
        """
        Normalize path and enforce root confinement.

        Returns the canonical path within the investigation root.
        Raises TraversalViolationError if path escapes root.
        """
        # Get canonical path (resolving symlinks if policy says to)
        if self._policy.resolve_symlinks_for_boundary_check:
            try:
                canonical = path.resolve()
            except (FileNotFoundError, PermissionError) as e:
                # If we can't resolve, we can't validate - reject
                raise TraversalViolationError(f"Cannot resolve path {path}: {e}") from e
        else:
            # Just get absolute path without resolving symlinks
            canonical = path.absolute()

        # Check if canonical path is within investigation root
        try:
            canonical.relative_to(self._root)
        except ValueError as e:
            # Outside root - check if escape is allowed
            if not self._policy.allow_escape_root:
                raise TraversalViolationError(
                    f"Path escapes investigation root: {canonical}\n"
                    f"Root: {self._root}\n"
                    f"Relative path attempted: {path.relative_to(self._root) if path.is_relative_to(self._root) else 'OUTSIDE'}"
                ) from e

        return canonical

    def _validate_symlinks(self, path: Path) -> list[Path]:
        """
        Validate symlinks according to policy.

        Returns the chain of symlinks followed.
        Raises SymlinkViolationError if policy is violated.
        """
        symlink_chain: list[Path] = []
        current = path

        # Follow symlink chain up to max depth
        for depth in range(self._policy.max_symlink_depth + 1):
            if depth > 0 and current.is_symlink():
                # Record this symlink
                symlink_chain.append(current)
                self._visited_symlinks.add(current)

            # Check if current path is a symlink
            if current.is_symlink():
                # Read the target
                try:
                    target = current.readlink()
                except (OSError, PermissionError) as e:
                    raise SymlinkViolationError(f"Cannot read symlink {current}: {e}") from e

                # Resolve target relative to symlink's directory
                if target.is_absolute():
                    next_path = target
                else:
                    next_path = (current.parent / target).resolve()

                # Check if target is in allowed list (if specified)
                if self._policy.allowed_symlink_targets:
                    if next_path not in self._policy.allowed_symlink_targets:
                        raise SymlinkViolationError(
                            f"Symlink target not in allowed list: {current} -> {next_path}"
                        )

                # Check if target is within root (unless escape is allowed)
                if not self._policy.allow_escape_root:
                    try:
                        next_path.relative_to(self._root)
                    except ValueError as e:
                        raise SymlinkViolationError(
                            f"Symlink escapes investigation root: {current} -> {next_path}"
                        ) from e

                # Move to next link in chain
                current = next_path
            else:
                # Not a symlink, we're done
                break
        else:
            # Loop completed without break = exceeded max depth
            raise SymlinkViolationError(
                f"Symlink chain exceeds maximum depth {self._policy.max_symlink_depth}: "
                f"{symlink_chain}"
            )

        return symlink_chain

    def _reject_symlinks(self, path: Path) -> None:
        """
        Reject any symlink (when policy doesn't allow them).

        Raises SymlinkViolationError if any symlink is detected.
        """
        # Check the path itself
        if path.is_symlink():
            raise SymlinkViolationError(f"Symlinks are not allowed: {path}")

        # Also check parent directories for symlinks
        # (to prevent symlink-based directory traversal)
        for parent in path.parents:
            if parent.is_symlink():
                raise SymlinkViolationError(
                    f"Parent directory is a symlink (not allowed): {parent}"
                )

    def _detect_cycles(self, path: Path, symlink_chain: list[Path]) -> None:
        """
        Detect filesystem cycles (symlink cycles or hardlink cycles).

        Raises CycleDetectionError if a cycle is detected.
        """
        # Check for symlink cycles in the chain we followed
        seen: set[Path] = set()
        for symlink in symlink_chain:
            if symlink in seen:
                raise CycleDetectionError(
                    f"Symlink cycle detected: {symlink} appears multiple times"
                )
            seen.add(symlink)

        # Check for hardlink cycles (if enabled)
        if self._policy.check_hardlink_cycles:
            try:
                stat = path.stat()
                inode = stat.st_ino

                # Track this inode
                if inode not in self._visited_hardlinks:
                    self._visited_hardlinks[inode] = set()

                # Check if we've seen this path for this inode before
                if path in self._visited_hardlinks[inode]:
                    raise CycleDetectionError(
                        f"Hardlink cycle detected: {path} (inode {inode}) already visited"
                    )

                # Record this path for this inode
                self._visited_hardlinks[inode].add(path)
            except (FileNotFoundError, PermissionError):
                # Can't stat, skip hardlink cycle check
                pass

    def _check_traversal_depth(self, path: Path) -> None:
        """
        Check that path traversal depth is within limits.

        Raises TraversalViolationError if depth is exceeded.
        """
        # Calculate depth relative to root
        try:
            relative = path.relative_to(self._root)
            depth = len(relative.parents)

            if depth > self._policy.max_traversal_depth:
                raise TraversalViolationError(
                    f"Path traversal depth {depth} exceeds limit "
                    f"{self._policy.max_traversal_depth}: {path}"
                )
        except ValueError:
            # Path is outside root (should have been caught earlier)
            pass

    def is_within_root(self, path: Path) -> bool:
        """
        Quick check if a path is within investigation root.

        This doesn't perform full validation, just a containment check.
        Useful for fast filtering before full validation.
        """
        try:
            path.relative_to(self._root)
            return True
        except ValueError:
            return False


# Public API functions for standalone use


def validate_path_against_root(
    path: Path, root: Path, policy: FilesystemPolicy | None = None
) -> dict[str, Any]:
    """
    Validate a path against a root directory with given policy.

    Convenience function for standalone use.

    Args:
        path: Path to validate.
        root: Investigation root directory.
        policy: Filesystem policy. Uses strict if None.

    Returns:
        Validation results dictionary.
    """
    validator = FilesystemValidator(root, policy)
    return validator.validate_path(path)


def validate_directory_against_root(
    dir_path: Path,
    root: Path,
    policy: FilesystemPolicy | None = None,
    check_contents: bool = True,
) -> dict[str, Any]:
    """
    Validate a directory against a root directory with given policy.

    Convenience function for standalone use.

    Args:
        dir_path: Directory path to validate.
        root: Investigation root directory.
        policy: Filesystem policy. Uses strict if None.
        check_contents: Whether to validate directory contents.

    Returns:
        Validation results dictionary.
    """
    validator = FilesystemValidator(root, policy)
    return validator.validate_directory(dir_path, check_contents)


# Test function for module verification
def _test_module() -> None:
    """Run basic tests on the module."""
    import tempfile

    print("Testing filesystem.py module...")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create test structure
        subdir = root / "subdir"
        subdir.mkdir()

        file1 = subdir / "file1.txt"
        file1.write_text("test")

        # Test 1: Basic validation
        validator = FilesystemValidator(root)
        result = validator.validate_path(file1)
        assert result["valid"] is True, f"Valid file should pass: {result}"
        print("✓ Basic file validation passed")

        # Test 2: Directory validation
        result = validator.validate_directory(subdir, check_contents=False)
        assert result["valid"] is True, f"Valid directory should pass: {result}"
        assert result["is_directory"] is True, "Should recognize as directory"
        print("✓ Directory validation passed")

        # Test 3: Path outside root (should fail)
        outside = Path("/tmp/outside.txt")
        if outside.exists():
            result = validator.validate_path(outside, require_exists=False)
            assert result["valid"] is False, "Path outside root should fail"
            assert result["violation"] == "root_escape"
            print("✓ Root escape detection passed")

        # Test 4: Symlink creation and validation
        if sys.platform != "win32":  # Symlink tests don't work well on Windows
            symlink_target = root / "symlink_target.txt"
            symlink_target.write_text("target")

            symlink = subdir / "link.txt"
            symlink.symlink_to(symlink_target)

            # With strict policy (default), symlinks should be rejected
            result = validator.validate_path(symlink)
            assert result["valid"] is False, (
                "Symlinks should be rejected in strict mode"
            )
            assert result["violation"] == "symlink"
            print("✓ Symlink rejection in strict mode passed")

            # With lenient policy, symlinks should be allowed
            lenient_validator = FilesystemValidator(root, FilesystemPolicy.lenient())
            result = lenient_validator.validate_path(symlink)
            assert result["valid"] is True, "Symlinks should be allowed in lenient mode"
            print("✓ Symlink allowance in lenient mode passed")

    print("All tests passed!")


if __name__ == "__main__":
    # When run directly, execute tests
    try:
        _test_module()
        sys.exit(0)
    except Exception as e:
        print(f"Test failed: {e}", file=sys.stderr)
        sys.exit(1)
