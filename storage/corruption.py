"""
CORRUPTION DETECTION & FLAGGING

Detects when stored evidence has been tampered with or decayed.
Never repairs. Only detects, flags, and reports.

Constitutional Rules:
1. Never fix corruption automatically
2. Never hide corruption
3. Never guess about corruption causes
4. Corruption markers are first-class evidence
5. Detection must be deterministic and verifiable
"""

import hashlib
import json
import mmap
import os
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any


class CorruptionType(Enum):
    """Types of detectable corruption."""

    HASH_MISMATCH = auto()  # Stored hash doesn't match content
    SCHEMA_MISMATCH = auto()  # Data doesn't match declared schema
    PARTIAL_WRITE = auto()  # File appears truncated or incomplete
    SIZE_MISMATCH = auto()  # File size unexpected
    JSON_PARSE_ERROR = auto()  # JSON file cannot be parsed
    BINARY_PARSE_ERROR = auto()  # Binary file cannot be parsed
    MISSING_REQUIRED = auto()  # Required fields missing
    TYPE_MISMATCH = auto()  # Data type doesn't match schema
    VERSION_MISMATCH = auto()  # Version unsupported or unknown
    CORRUPTION_MARKER = auto()  # File has explicit corruption marker


@dataclass(frozen=True)
class CorruptionEvidence:
    """Immutable evidence of corruption."""

    path: Path
    corruption_type: CorruptionType
    expected_value: Any | None = None
    actual_value: Any | None = None
    detected_at: float = 0.0  # Will be set to time.time() when created
    context: dict[str, Any] | None = None

    def __post_init__(self):
        # Set detection time at creation
        import time

        object.__setattr__(self, "detected_at", time.time())


class CorruptionDetectionError(Exception):
    """Base exception for corruption detection failures."""

    pass


class FileAccessError(CorruptionDetectionError):
    """Cannot access file for corruption detection."""

    pass


class HashMismatchError(CorruptionDetectionError):
    """File hash doesn't match expected value."""

    pass


class SchemaViolationError(CorruptionDetectionError):
    """File violates schema constraints."""

    pass


class PartialWriteError(CorruptionDetectionError):
    """File appears to be partially written or truncated."""

    pass


class CorruptionMarker:
    """
    Creates and reads explicit corruption markers.

    A corruption marker is a small JSON file placed next to corrupted data
    that explains what corruption was detected and when.
    """

    MARKER_SUFFIX = ".corrupted"

    @staticmethod
    def create_marker(
        corrupted_path: Path,
        evidence: CorruptionEvidence,
        marker_suffix: str = MARKER_SUFFIX,
    ) -> Path:
        """
        Create a corruption marker file for a corrupted file.

        Args:
            corrupted_path: Path to the corrupted file
            evidence: Corruption evidence
            marker_suffix: Suffix for marker file

        Returns:
            Path to created marker file

        Raises:
            FileAccessError: If marker cannot be written
        """
        marker_path = corrupted_path.with_suffix(corrupted_path.suffix + marker_suffix)

        marker_data: dict[str, Any] = {
            "corrupted_file": str(corrupted_path.absolute()),
            "detection_time": evidence.detected_at,
            "corruption_type": evidence.corruption_type.name,
            "expected_value": evidence.expected_value,
            "actual_value": evidence.actual_value,
            "context": evidence.context or {},
            "generator": "CodeMarshal Corruption Detection",
            "schema_version": "v2.1.0",
        }

        try:
            # Use atomic write if available, otherwise careful write
            marker_path.write_text(json.dumps(marker_data, indent=2))
            return marker_path
        except OSError as e:
            raise FileAccessError(
                f"Cannot create corruption marker at {marker_path}: {e}"
            ) from e

    @staticmethod
    def has_marker(file_path: Path, marker_suffix: str = MARKER_SUFFIX) -> bool:
        """
        Check if a file has a corruption marker.

        Args:
            file_path: Path to check for corruption marker
            marker_suffix: Suffix for marker file

        Returns:
            True if corruption marker exists
        """
        marker_path = file_path.with_suffix(file_path.suffix + marker_suffix)
        return marker_path.exists() and marker_path.is_file()

    @staticmethod
    def read_marker(
        file_path: Path, marker_suffix: str = MARKER_SUFFIX
    ) -> dict[str, Any] | None:
        """
        Read corruption marker if it exists.

        Args:
            file_path: Path to check for corruption marker
            marker_suffix: Suffix for marker file

        Returns:
            Marker data as dict, or None if no marker exists or cannot be read
        """
        marker_path = file_path.with_suffix(file_path.suffix + marker_suffix)

        if not marker_path.exists():
            return None

        try:
            content = marker_path.read_text(encoding="utf-8")
            return json.loads(content)
        except (OSError, json.JSONDecodeError):
            # If we can't read the marker, that's interesting but not an error
            return None


def _calculate_file_hash(path: Path, hash_algo: str = "sha256") -> str:
    """
    Calculate file hash in a memory-efficient way.

    Args:
        path: Path to file
        hash_algo: Hash algorithm to use

    Returns:
        Hexadecimal hash string

    Raises:
        FileAccessError: If file cannot be read
    """
    try:
        hasher = hashlib.new(hash_algo)
        file_size = path.stat().st_size

        # For small files, read all at once
        if file_size < 1024 * 1024:  # 1MB
            data = path.read_bytes()
            hasher.update(data)
            return hasher.hexdigest()

        # For larger files, read in chunks
        with open(path, "rb") as f:
            # Use mmap for efficient large file reading if available
            if hasattr(mmap, "MAP_SHARED") and os.name != "nt":  # mmap on Unix
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped:
                    # Process in 1MB chunks
                    chunk_size = 1024 * 1024
                    offset = 0
                    while offset < file_size:
                        chunk = mmapped[offset : offset + chunk_size]
                        if not chunk:
                            break
                        hasher.update(chunk)
                        offset += len(chunk)
            else:
                # Fallback to regular chunked reading
                chunk_size = 1024 * 1024
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    hasher.update(chunk)

        return hasher.hexdigest()
    except OSError as e:
        raise FileAccessError(f"Cannot hash file {path}: {e}") from e


def verify_hash(
    path: Path, expected_hash: str, hash_algo: str = "sha256"
) -> CorruptionEvidence | None:
    """
    Verify file hash matches expected value.

    Args:
        path: Path to file
        expected_hash: Expected hexadecimal hash
        hash_algo: Hash algorithm used

    Returns:
        CorruptionEvidence if hash mismatch, None if valid
    """
    if not path.exists():
        return CorruptionEvidence(
            path=path,
            corruption_type=CorruptionType.HASH_MISMATCH,
            expected_value=f"File exists with hash {expected_hash}",
            actual_value="File does not exist",
        )

    try:
        actual_hash = _calculate_file_hash(path, hash_algo)
        if actual_hash != expected_hash.lower():
            return CorruptionEvidence(
                path=path,
                corruption_type=CorruptionType.HASH_MISMATCH,
                expected_value=expected_hash.lower(),
                actual_value=actual_hash,
                context={"hash_algorithm": hash_algo},
            )
        return None
    except FileAccessError as e:
        return CorruptionEvidence(
            path=path,
            corruption_type=CorruptionType.HASH_MISMATCH,
            expected_value=f"Readable file with hash {expected_hash}",
            actual_value=f"Cannot read file: {e}",
            context={"hash_algorithm": hash_algo},
        )


def detect_partial_write(
    path: Path, min_expected_size: int = 1
) -> CorruptionEvidence | None:
    """
    Detect if a file appears to be partially written or truncated.

    Note: This is a heuristic, not proof. Always used with other checks.

    Args:
        path: Path to file
        min_expected_size: Minimum reasonable file size

    Returns:
        CorruptionEvidence if partial write detected, None otherwise
    """
    if not path.exists():
        return CorruptionEvidence(
            path=path,
            corruption_type=CorruptionType.PARTIAL_WRITE,
            expected_value=f"File exists with size >= {min_expected_size}",
            actual_value="File does not exist",
        )

    try:
        file_size = path.stat().st_size

        # Check if file is empty when it shouldn't be
        if file_size < min_expected_size:
            return CorruptionEvidence(
                path=path,
                corruption_type=CorruptionType.PARTIAL_WRITE,
                expected_value=f"Size >= {min_expected_size} bytes",
                actual_value=f"{file_size} bytes",
            )

        # For text files, check if ends with newline (common for partial writes)
        if file_size > 0:
            try:
                with open(path, "rb") as f:
                    f.seek(-1, os.SEEK_END)
                    last_byte = f.read(1)
                    # Many text writers don't end with newline, so this is just a hint
                    if last_byte == b"\x00":  # Null byte in text file
                        return CorruptionEvidence(
                            path=path,
                            corruption_type=CorruptionType.PARTIAL_WRITE,
                            expected_value="Text file should not end with null byte",
                            actual_value="Ends with null byte",
                            context={"file_size": file_size},
                        )
            except OSError:
                pass

        return None
    except OSError as e:
        return CorruptionEvidence(
            path=path,
            corruption_type=CorruptionType.PARTIAL_WRITE,
            expected_value="Accessible file",
            actual_value=f"Cannot access: {e}",
        )


def verify_json_structure(
    path: Path,
    required_fields: set[str] | None = None,
    schema_version_field: str = "schema_version",
) -> CorruptionEvidence | None:
    """
    Verify JSON file can be parsed and has basic structure.

    Args:
        path: Path to JSON file
        required_fields: Set of field names that must be present
        schema_version_field: Field name containing schema version

    Returns:
        CorruptionEvidence if JSON issues found, None if valid
    """
    if not path.exists():
        return CorruptionEvidence(
            path=path,
            corruption_type=CorruptionType.JSON_PARSE_ERROR,
            expected_value="Valid JSON file",
            actual_value="File does not exist",
        )

    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return CorruptionEvidence(
            path=path,
            corruption_type=CorruptionType.JSON_PARSE_ERROR,
            expected_value="Readable UTF-8 text file",
            actual_value=f"Cannot read: {e}",
        )

    # Try to parse JSON
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return CorruptionEvidence(
            path=path,
            corruption_type=CorruptionType.JSON_PARSE_ERROR,
            expected_value="Valid JSON syntax",
            actual_value=f"JSON parse error: {e}",
            context={"error_position": str(e.pos) if hasattr(e, "pos") else None},
        )

    # Check required fields
    if required_fields:
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            return CorruptionEvidence(
                path=path,
                corruption_type=CorruptionType.MISSING_REQUIRED,
                expected_value=f"Fields present: {required_fields}",
                actual_value=f"Missing fields: {missing_fields}",
            )

    # Check schema version field if specified
    if schema_version_field and schema_version_field not in data:
        return CorruptionEvidence(
            path=path,
            corruption_type=CorruptionType.MISSING_REQUIRED,
            expected_value=f"Field present: {schema_version_field}",
            actual_value="Missing schema version field",
        )

    return None


def verify_binary_header(
    path: Path, expected_magic: bytes, header_size: int
) -> CorruptionEvidence | None:
    """
    Verify binary file has expected header.

    Args:
        path: Path to binary file
        expected_magic: Expected magic bytes at start of file
        header_size: Expected total header size

    Returns:
        CorruptionEvidence if header mismatch, None if valid
    """
    if not path.exists():
        return CorruptionEvidence(
            path=path,
            corruption_type=CorruptionType.BINARY_PARSE_ERROR,
            expected_value=f"File exists with header {expected_magic.hex()}",
            actual_value="File does not exist",
        )

    try:
        file_size = path.stat().st_size
        if file_size < header_size:
            return CorruptionEvidence(
                path=path,
                corruption_type=CorruptionType.PARTIAL_WRITE,
                expected_value=f"Size >= {header_size} bytes",
                actual_value=f"{file_size} bytes",
            )

        with open(path, "rb") as f:
            magic = f.read(len(expected_magic))
            if magic != expected_magic:
                return CorruptionEvidence(
                    path=path,
                    corruption_type=CorruptionType.BINARY_PARSE_ERROR,
                    expected_value=f"Magic bytes: {expected_magic.hex()}",
                    actual_value=f"Got: {magic.hex() if magic else 'empty'}",
                )

        return None
    except OSError as e:
        return CorruptionEvidence(
            path=path,
            corruption_type=CorruptionType.BINARY_PARSE_ERROR,
            expected_value="Readable binary file",
            actual_value=f"Cannot read: {e}",
        )


def check_directory_integrity(
    dir_path: Path,
    expected_files: set[str] | None = None,
    hash_manifest: dict[str, str] | None = None,
) -> list[CorruptionEvidence]:
    """
    Check integrity of all files in a directory.

    Args:
        dir_path: Directory to check
        expected_files: Set of expected filenames (optional)
        hash_manifest: Map of filename -> expected hash (optional)

    Returns:
        List of corruption evidence found
    """
    if not dir_path.exists():
        return [
            CorruptionEvidence(
                path=dir_path,
                corruption_type=CorruptionType.MISSING_REQUIRED,
                expected_value="Directory exists",
                actual_value="Directory does not exist",
            )
        ]

    if not dir_path.is_dir():
        return [
            CorruptionEvidence(
                path=dir_path,
                corruption_type=CorruptionType.TYPE_MISMATCH,
                expected_value="Directory",
                actual_value="Not a directory",
            )
        ]

    evidence_list: list[CorruptionEvidence] = []

    # Check for expected files
    if expected_files:
        found_files = {f.name for f in dir_path.iterdir() if f.is_file()}
        missing_files = expected_files - found_files
        extra_files = found_files - expected_files

        for missing in missing_files:
            evidence_list.append(
                CorruptionEvidence(
                    path=dir_path / missing,
                    corruption_type=CorruptionType.MISSING_REQUIRED,
                    expected_value="File present",
                    actual_value="File missing",
                )
            )

        # Extra files aren't necessarily corruption, but note them
        for extra in extra_files:
            evidence_list.append(
                CorruptionEvidence(
                    path=dir_path / extra,
                    corruption_type=CorruptionType.SIZE_MISMATCH,
                    expected_value="No file (not in expected set)",
                    actual_value="Unexpected file present",
                    context={"file_type": "unexpected"},
                )
            )

    # Verify hashes if manifest provided
    if hash_manifest:
        for filename, expected_hash in hash_manifest.items():
            file_path = dir_path / filename
            if file_path.exists():
                hash_evidence = verify_hash(file_path, expected_hash)
                if hash_evidence:
                    evidence_list.append(hash_evidence)

    return evidence_list


class CorruptionDetector:
    """
    Main corruption detection orchestrator.

    Collects detection methods and tracks found corruption.
    """

    def __init__(self):
        self._detected_corruption: list[CorruptionEvidence] = []
        self._checked_paths: set[Path] = set()

    def check_file(
        self,
        path: Path,
        expected_hash: str | None = None,
        min_size: int = 1,
        is_json: bool = False,
        json_required_fields: set[str] | None = None,
        is_binary: bool = False,
        binary_magic: bytes | None = None,
        binary_header_size: int = 0,
    ) -> list[CorruptionEvidence]:
        """
        Run comprehensive corruption checks on a file.

        Args:
            path: File to check
            expected_hash: Expected hash (optional)
            min_size: Minimum expected file size
            is_json: Whether to validate as JSON
            json_required_fields: Required JSON fields (if is_json)
            is_binary: Whether to validate as binary
            binary_magic: Expected magic bytes (if is_binary)
            binary_header_size: Expected header size (if is_binary)

        Returns:
            List of corruption evidence found
        """
        if path in self._checked_paths:
            return []

        self._checked_paths.add(path)
        evidence: list[CorruptionEvidence] = []

        # Check for existing corruption marker
        if CorruptionMarker.has_marker(path):
            evidence.append(
                CorruptionEvidence(
                    path=path,
                    corruption_type=CorruptionType.CORRUPTION_MARKER,
                    expected_value="No corruption marker",
                    actual_value="Corruption marker present",
                )
            )

        # Check file exists and is accessible
        if not path.exists():
            evidence.append(
                CorruptionEvidence(
                    path=path,
                    corruption_type=CorruptionType.MISSING_REQUIRED,
                    expected_value="File exists",
                    actual_value="File does not exist",
                )
            )
            self._detected_corruption.extend(evidence)
            return evidence

        # Check partial write
        partial_evidence = detect_partial_write(path, min_size)
        if partial_evidence:
            evidence.append(partial_evidence)

        # Check hash if provided
        if expected_hash:
            hash_evidence = verify_hash(path, expected_hash)
            if hash_evidence:
                evidence.append(hash_evidence)

        # JSON-specific checks
        if is_json:
            json_evidence = verify_json_structure(path, json_required_fields)
            if json_evidence:
                evidence.append(json_evidence)

        # Binary-specific checks
        if is_binary and binary_magic:
            binary_evidence = verify_binary_header(
                path, binary_magic, binary_header_size
            )
            if binary_evidence:
                evidence.append(binary_evidence)

        self._detected_corruption.extend(evidence)
        return evidence

    def check_directory(
        self,
        dir_path: Path,
        expected_files: set[str] | None = None,
        hash_manifest: dict[str, str] | None = None,
    ) -> list[CorruptionEvidence]:
        """
        Check directory integrity.

        Args:
            dir_path: Directory to check
            expected_files: Expected files in directory
            hash_manifest: Expected file hashes

        Returns:
            List of corruption evidence found
        """
        evidence = check_directory_integrity(dir_path, expected_files, hash_manifest)
        self._detected_corruption.extend(evidence)
        return evidence

    def get_all_corruption(self) -> list[CorruptionEvidence]:
        """Get all corruption evidence found by this detector."""
        return self._detected_corruption.copy()

    def clear(self) -> None:
        """Clear all detected corruption and checked paths."""
        self._detected_corruption.clear()
        self._checked_paths.clear()

    def mark_all_corruption(self) -> list[Path]:
        """
        Create corruption markers for all detected corruption.

        Returns:
            List of created marker file paths
        """
        marker_paths: list[Path] = []
        for evidence in self._detected_corruption:
            try:
                marker_path = CorruptionMarker.create_marker(evidence.path, evidence)
                marker_paths.append(marker_path)
            except FileAccessError:
                # Silently skip if we can't create marker
                continue
        return marker_paths


@dataclass
class CorruptionCheck:
    """Result of an integrity check."""

    is_corrupt: bool
    corruption_type: str
    issues: list[str]
    severity: str


@dataclass
class CorruptionState:
    """State of corruption for a resource."""

    file_path: str
    corruption_type: str
    detected_at: Any  # datetime
    severity: str
    details: str | None = None


def detect_corruption(data: bytes, context_type: str) -> CorruptionState | None:
    """
    Detect corruption in binary data.

    Args:
        data: Binary content to check
        context_type: Type of content (e.g., "session_context")

    Returns:
        CorruptionState if corruption detected, None otherwise
    """
    try:
        from datetime import datetime

        # Check if empty
        if not data:
            return CorruptionState(
                file_path="memory",
                corruption_type="empty_data",
                detected_at=datetime.now(),
                severity="high",
            )

        # If context_type implies JSON, check JSON validity
        if context_type in ["session_context", "investigation_history"]:
            try:
                json.loads(data.decode("utf-8"))
            except Exception as e:
                return CorruptionState(
                    file_path="memory",
                    corruption_type="json_parse_error",
                    detected_at=datetime.now(),
                    severity="high",
                    details=str(e),
                )

        return None
    except Exception as e:
        from datetime import datetime

        return CorruptionState(
            file_path="memory",
            corruption_type="unknown_error",
            detected_at=datetime.now(),
            severity="high",
            details=str(e),
        )


# Export public API
__all__ = [
    "CorruptionType",
    "CorruptionEvidence",
    "CorruptionDetectionError",
    "FileAccessError",
    "HashMismatchError",
    "SchemaViolationError",
    "PartialWriteError",
    "CorruptionMarker",
    "verify_hash",
    "detect_partial_write",
    "verify_json_structure",
    "verify_binary_header",
    "check_directory_integrity",
    "CorruptionDetector",
    "CorruptionCheck",
    "CorruptionState",
    "detect_corruption",
]
