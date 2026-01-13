# observations/input_validation/size_limits.py
"""
File size and resource constraint validation.

Enforces finite attention before observation begins.
These limits are truth constraints, not performance hacks.
"""

import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Configure logging at module level
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SizeLimits:
    """
    Hard limits that define what can be observed.
    
    These are truth constraints: you cannot claim to have observed
    what you truncated or failed to read entirely.
    """

    # Maximum file size in bytes that can be fully observed
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10 MB

    # Maximum number of files in a single directory
    max_directory_breadth: int = 10_000

    # Maximum total files to observe in a single investigation
    max_total_files: int = 100_000

    # Maximum total observation footprint in bytes (sum of file sizes)
    max_total_footprint_bytes: int = 1 * 1024 * 1024 * 1024  # 1 GB

    # Minimum file size to consider (files smaller than this are ignored)
    # This prevents observation of empty or tiny noise files
    min_file_size_bytes: int = 1

    @classmethod
    def defaults(cls) -> "SizeLimits":
        """Return the system default size limits."""
        return cls()

    def validate(self) -> None:
        """Validate that limits are sane and consistent."""
        if self.max_file_size_bytes <= 0:
            raise ValueError("max_file_size_bytes must be positive")
        if self.max_directory_breadth <= 0:
            raise ValueError("max_directory_breadth must be positive")
        if self.max_total_files <= 0:
            raise ValueError("max_total_files must be positive")
        if self.max_total_footprint_bytes <= 0:
            raise ValueError("max_total_footprint_bytes must be positive")
        if self.min_file_size_bytes < 0:
            raise ValueError("min_file_size_bytes cannot be negative")

        if self.min_file_size_bytes >= self.max_file_size_bytes:
            raise ValueError(
                "min_file_size_bytes must be less than max_file_size_bytes"
            )


class SizeLimitValidator:
    """
    Validates file and directory sizes against hard limits.
    
    This validator maintains state to track cumulative totals
    across an investigation, ensuring we don't exceed total limits.
    """

    def __init__(
        self,
        limits: SizeLimits | None = None,
        investigation_root: Path | None = None
    ) -> None:
        """
        Initialize the validator.
        
        Args:
            limits: Size limits to enforce. Uses defaults if None.
            investigation_root: Root path of the investigation, used for
                consistent path resolution. If None, paths must be absolute.
        """
        self.limits: SizeLimits = limits or SizeLimits.defaults()
        self.limits.validate()

        self.investigation_root: Path | None = None
        if investigation_root is not None:
            self.investigation_root = investigation_root.resolve()

        # State tracking
        self.total_files_observed: int = 0
        self.total_bytes_observed: int = 0
        self._observed_paths: set[Path] = set()

        logger.debug(
            f"SizeLimitValidator initialized with limits: "
            f"file={self.limits.max_file_size_bytes:,}B, "
            f"dir_breadth={self.limits.max_directory_breadth:,}, "
            f"total_files={self.limits.max_total_files:,}"
        )

    def reset(self) -> None:
        """Reset all counters for a new investigation."""
        self.total_files_observed = 0
        self.total_bytes_observed = 0
        self._observed_paths.clear()
        logger.debug("SizeLimitValidator reset")

    def _resolve_path(self, path: str | Path) -> Path:
        """Resolve a path relative to investigation root if needed."""
        path_obj = Path(path)

        if not path_obj.is_absolute():
            if self.investigation_root is None:
                raise ValueError(
                    f"Relative path '{path}' requires investigation_root to be set"
                )
            resolved = (self.investigation_root / path_obj).resolve()
        else:
            resolved = path_obj.resolve()

        return resolved

    def validate_file_size(self, file_path: str | Path) -> dict[str, Any]:
        """
        Validate a single file's size against limits.
        
        Args:
            file_path: Path to the file to validate.
            
        Returns:
            Dictionary with validation results:
                - "valid": bool - Whether file passes all size checks
                - "size_bytes": int - Actual file size
                - "reason": Optional[str] - If invalid, why
                - "limit_exceeded": Optional[str] - Which limit was exceeded
            
        Raises:
            FileNotFoundError: If file doesn't exist.
            OSError: If file cannot be accessed.
        """
        path = self._resolve_path(file_path)

        # Check if we've already observed this path in this investigation
        if path in self._observed_paths:
            logger.warning(f"Duplicate observation attempt for path: {path}")
            return {
                "valid": False,
                "size_bytes": 0,
                "reason": "Path already observed in this investigation",
                "limit_exceeded": "duplicate_observation"
            }

        try:
            stat_result = path.stat()
            file_size = stat_result.st_size

            # Check against total file count limit
            if self.total_files_observed >= self.limits.max_total_files:
                return {
                    "valid": False,
                    "size_bytes": file_size,
                    "reason": f"Total file limit reached ({self.limits.max_total_files})",
                    "limit_exceeded": "max_total_files"
                }

            # Check against total byte footprint
            projected_total = self.total_bytes_observed + file_size
            if projected_total > self.limits.max_total_footprint_bytes:
                return {
                    "valid": False,
                    "size_bytes": file_size,
                    "reason": (
                        f"Total byte footprint would exceed limit "
                        f"({self.limits.max_total_footprint_bytes:,}B)"
                    ),
                    "limit_exceeded": "max_total_footprint_bytes"
                }

            # Check against file size limits
            if file_size > self.limits.max_file_size_bytes:
                return {
                    "valid": False,
                    "size_bytes": file_size,
                    "reason": (
                        f"File size ({file_size:,}B) exceeds limit "
                        f"({self.limits.max_file_size_bytes:,}B)"
                    ),
                    "limit_exceeded": "max_file_size_bytes"
                }

            if file_size < self.limits.min_file_size_bytes:
                return {
                    "valid": False,
                    "size_bytes": file_size,
                    "reason": (
                        f"File size ({file_size:,}B) below minimum "
                        f"({self.limits.min_file_size_bytes:,}B)"
                    ),
                    "limit_exceeded": "min_file_size_bytes"
                }

            # File passes all checks
            return {
                "valid": True,
                "size_bytes": file_size,
                "reason": None,
                "limit_exceeded": None
            }

        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {path}")
        except OSError as e:
            raise OSError(f"Cannot access file {path}: {e}")

    def validate_directory_breadth(
        self,
        dir_path: str | Path
    ) -> dict[str, Any]:
        """
        Validate a directory's file count against breadth limit.
        
        Args:
            dir_path: Path to the directory to validate.
            
        Returns:
            Dictionary with validation results:
                - "valid": bool - Whether directory passes breadth check
                - "file_count": int - Number of files in directory
                - "reason": Optional[str] - If invalid, why
                - "limit_exceeded": Optional[str] - Which limit was exceeded
                
        Raises:
            FileNotFoundError: If directory doesn't exist.
            NotADirectoryError: If path is not a directory.
            OSError: If directory cannot be accessed.
        """
        path = self._resolve_path(dir_path)

        try:
            if not path.is_dir():
                raise NotADirectoryError(f"Not a directory: {path}")

            # Count files in directory (non-recursive)
            file_count = 0
            with os.scandir(path) as entries:
                for entry in entries:
                    if entry.is_file():
                        file_count += 1

            # Check against directory breadth limit
            if file_count > self.limits.max_directory_breadth:
                return {
                    "valid": False,
                    "file_count": file_count,
                    "reason": (
                        f"Directory has {file_count} files, "
                        f"exceeds limit of {self.limits.max_directory_breadth}"
                    ),
                    "limit_exceeded": "max_directory_breadth"
                }

            # Directory passes check
            return {
                "valid": True,
                "file_count": file_count,
                "reason": None,
                "limit_exceeded": None
            }

        except FileNotFoundError:
            raise FileNotFoundError(f"Directory not found: {path}")
        except PermissionError as e:
            raise OSError(f"Permission denied accessing directory {path}: {e}")

    def record_observation(
        self,
        file_path: str | Path,
        file_size: int
    ) -> None:
        """
        Record that a file has been observed.
        
        This updates the cumulative counters. Must be called after
        successful validation and actual observation.
        
        Args:
            file_path: Path to the file that was observed.
            file_size: Size of the file in bytes.
            
        Raises:
            ValueError: If recording would exceed limits.
        """
        path = self._resolve_path(file_path)

        # Safety check - should have been validated first
        projected_files = self.total_files_observed + 1
        if projected_files > self.limits.max_total_files:
            raise ValueError(
                f"Recording would exceed total file limit "
                f"({self.limits.max_total_files})"
            )

        projected_bytes = self.total_bytes_observed + file_size
        if projected_bytes > self.limits.max_total_footprint_bytes:
            raise ValueError(
                f"Recording would exceed total byte footprint "
                f"({self.limits.max_total_footprint_bytes:,}B)"
            )

        # Update state
        self._observed_paths.add(path)
        self.total_files_observed += 1
        self.total_bytes_observed += file_size

        logger.debug(
            f"Recorded observation: {path} "
            f"({file_size:,}B, total: {self.total_files_observed} files, "
            f"{self.total_bytes_observed:,}B)"
        )

    def get_current_state(self) -> dict[str, Any]:
        """
        Get current validation state.
        
        Returns:
            Dictionary with current counters and remaining capacity.
        """
        return {
            "total_files_observed": self.total_files_observed,
            "total_bytes_observed": self.total_bytes_observed,
            "remaining_files": max(0, self.limits.max_total_files - self.total_files_observed),
            "remaining_bytes": max(0, self.limits.max_total_footprint_bytes - self.total_bytes_observed),
            "unique_paths_observed": len(self._observed_paths)
        }

    def get_limits(self) -> dict[str, Any]:
        """Get the current limits as a dictionary."""
        return {
            "max_file_size_bytes": self.limits.max_file_size_bytes,
            "max_directory_breadth": self.limits.max_directory_breadth,
            "max_total_files": self.limits.max_total_files,
            "max_total_footprint_bytes": self.limits.max_total_footprint_bytes,
            "min_file_size_bytes": self.limits.min_file_size_bytes
        }


# Public API functions for standalone use

def validate_file_against_defaults(file_path: str | Path) -> dict[str, Any]:
    """
    Validate a single file against default size limits.
    
    This is a convenience function for standalone use without
    maintaining validator state.
    
    Args:
        file_path: Path to the file to validate.
        
    Returns:
        Validation results dictionary (see validate_file_size).
    """
    validator = SizeLimitValidator()
    return validator.validate_file_size(file_path)


def validate_directory_against_defaults(dir_path: str | Path) -> dict[str, Any]:
    """
    Validate a directory against default breadth limits.
    
    This is a convenience function for standalone use without
    maintaining validator state.
    
    Args:
        dir_path: Path to the directory to validate.
        
    Returns:
        Validation results dictionary (see validate_directory_breadth).
    """
    validator = SizeLimitValidator()
    return validator.validate_directory_breadth(dir_path)


# Test function for module verification
def _test_module() -> None:
    """Run basic tests on the module."""
    import tempfile

    print("Testing size_limits module...")

    # Create test files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Test 1: Valid small file
        small_file = tmp_path / "small.txt"
        small_file.write_text("test")
        result = validate_file_against_defaults(small_file)
        assert result["valid"] is True, f"Small file should be valid: {result}"
        print("✓ Small file validation passed")

        # Test 2: Directory breadth
        result = validate_directory_against_defaults(tmp_path)
        assert result["valid"] is True, f"Empty directory should be valid: {result}"
        print("✓ Directory validation passed")

        # Test 3: Stateful validator
        validator = SizeLimitValidator(investigation_root=tmp_path)

        # Record the small file
        file_size = small_file.stat().st_size
        validator.record_observation(small_file, file_size)

        state = validator.get_current_state()
        assert state["total_files_observed"] == 1, "Should have 1 file recorded"
        assert state["total_bytes_observed"] == file_size, "Byte count should match"
        print("✓ Stateful recording passed")

    print("All tests passed!")


if __name__ == "__main__":
    # When run directly, execute tests
    try:
        _test_module()
        sys.exit(0)
    except Exception as e:
        print(f"Test failed: {e}", file=sys.stderr)
        sys.exit(1)
