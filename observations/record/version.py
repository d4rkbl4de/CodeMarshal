"""
observations/record/version.py

Snapshot format versioning and compatibility management.

This module defines schema evolution for snapshots, ensuring:
- Backward readability: Old snapshots remain readable
- Forward tolerance: When possible, tolerate newer versions safely
- Explicit upgrade paths: Pure, deterministic transforms only

Production principle: Version refusal is safer than false compatibility.
"""

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, TypeVar
from uuid import UUID

# ============================================================================
# VERSION IDENTIFIERS
# ============================================================================


class VersionFormat(Enum):
    """Format of the snapshot version identifier."""

    SEMANTIC = auto()  # MAJOR.MINOR.PATCH for breaking/feature/patch changes
    TIMESTAMP = auto()  # YYYYMMDD-HHMMSS for chronological ordering

    @classmethod
    def detect(cls, version_str: str) -> "VersionFormat":
        """Determine the format of a version string."""
        if re.match(r"^\d+\.\d+\.\d+$", version_str):
            return cls.SEMANTIC
        elif re.match(r"^\d{8}-\d{6}$", version_str):
            return cls.TIMESTAMP
        else:
            raise ValueError(f"Unrecognized version format: {version_str}")


@dataclass(frozen=True)
class SemanticVersion:
    """Semantic versioning (MAJOR.MINOR.PATCH) for snapshot formats."""

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, version_str: str) -> "SemanticVersion":
        """Parse a semantic version string."""
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_str)
        if not match:
            raise ValueError(f"Invalid semantic version: {version_str}")

        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
        )

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_backward_compatible_with(self, other: "SemanticVersion") -> bool:
        """Check if this version is backward compatible with another.

        Rules:
        - Same MAJOR version required
        - MINOR must be >= other.minor
        - PATCH can be anything (patch changes don't break compatibility)
        """
        return self.major == other.major and self.minor >= other.minor

    def can_upgrade_to(self, target: "SemanticVersion") -> tuple[bool, str | None]:
        """Determine if upgrade to target version is possible.

        Returns:
            Tuple of (can_upgrade: bool, reason: Optional[str])
        """
        # Can't downgrade
        if target.major < self.major:
            return False, f"Downgrade not allowed: {self} -> {target}"
        if target.major == self.major and target.minor < self.minor:
            return False, f"Downgrade not allowed: {self} -> {target}"

        # Major version changes require explicit upgrade path
        if target.major > self.major:
            # We only allow +1 major version upgrades
            if target.major != self.major + 1:
                return False, f"Cannot skip major versions: {self} -> {target}"

            # Specific upgrade rules for known major version changes
            # (Add more as format evolves)
            if self.major == 1 and target.major == 2:
                # V1 -> V2 upgrade requires specific handling
                # This will be implemented when V2 is defined
                return True, None

        # Minor/patch upgrades within same major version are always allowed
        return True, None


@dataclass(frozen=True)
class TimestampVersion:
    """Timestamp-based versioning for chronological ordering."""

    timestamp: datetime

    @classmethod
    def parse(cls, version_str: str) -> "TimestampVersion":
        """Parse a timestamp version string (YYYYMMDD-HHMMSS)."""
        try:
            dt = datetime.strptime(version_str, "%Y%m%d-%H%M%S")
            # Timestamp versions must be timezone-aware UTC
            dt = dt.replace(tzinfo=UTC)
            return cls(timestamp=dt)
        except ValueError as e:
            raise ValueError(f"Invalid timestamp version: {version_str}") from e

    @classmethod
    def now(cls) -> "TimestampVersion":
        """Create a new timestamp version for the current time."""
        return cls(timestamp=datetime.now(UTC))

    def __str__(self) -> str:
        # Always output in UTC, zero-padded
        utc_time = self.timestamp.astimezone(UTC)
        return utc_time.strftime("%Y%m%d-%H%M%S")

    def is_backward_compatible_with(self, other: "TimestampVersion") -> bool:
        """Timestamp versions are always backward compatible.

        Since they're chronological, newer versions can read older ones
        (assuming format hasn't changed in incompatible ways).
        """
        return True  # Actual format compatibility is handled elsewhere

    def can_upgrade_to(self, target: "TimestampVersion") -> tuple[bool, str | None]:
        """Timestamp versions can't be upgraded - they're absolute."""
        return False, "Timestamp versions cannot be upgraded (they're absolute)"


VersionType = SemanticVersion | TimestampVersion


@dataclass(frozen=True)
class SnapshotVersion:
    """Complete version identifier for a snapshot."""

    version: VersionType
    format: VersionFormat

    @classmethod
    def parse(cls, version_str: str) -> "SnapshotVersion":
        """Parse a version string into a structured version object."""
        format_type = VersionFormat.detect(version_str)

        if format_type == VersionFormat.SEMANTIC:
            version_obj = SemanticVersion.parse(version_str)
        else:  # TIMESTAMP
            version_obj = TimestampVersion.parse(version_str)

        return cls(version=version_obj, format=format_type)

    @classmethod
    def current(cls) -> "SnapshotVersion":
        """Get the current snapshot format version.

        Current format uses semantic versioning starting at 1.0.0.
        This should only be changed when the snapshot format changes.
        """
        return cls(
            version=SemanticVersion(major=1, minor=0, patch=0),
            format=VersionFormat.SEMANTIC,
        )

    def __str__(self) -> str:
        return str(self.version)

    def is_compatible(self, other: "SnapshotVersion") -> bool:
        """Check if this version is compatible with another version.

        Compatibility rules:
        - Same format required (can't mix semantic and timestamp)
        - Semantic: backward compatibility rules apply
        - Timestamp: always backward compatible
        """
        if self.format != other.format:
            return False

        return self.version.is_backward_compatible_with(other.version)

    def can_upgrade_to(self, target: "SnapshotVersion") -> tuple[bool, str | None]:
        """Determine if upgrade to target version is possible.

        Returns:
            Tuple of (can_upgrade: bool, reason: Optional[str])
        """
        # Can't change format
        if self.format != target.format:
            return False, f"Cannot change format: {self.format} -> {target.format}"

        return self.version.can_upgrade_to(target.version)


# ============================================================================
# COMPATIBILITY RULES
# ============================================================================


class VersionCompatibility:
    """Manager for snapshot format compatibility rules."""

    # Minimum supported version for each format
    MIN_SUPPORTED_VERSIONS = {
        VersionFormat.SEMANTIC: SemanticVersion.parse("1.0.0"),
        VersionFormat.TIMESTAMP: TimestampVersion.parse("20240101-000000"),
    }

    @classmethod
    def is_supported(cls, version: SnapshotVersion) -> tuple[bool, str | None]:
        """Check if a version is supported by this codebase.

        Returns:
            Tuple of (is_supported: bool, reason: Optional[str])
        """
        # Check if format is supported
        if version.format not in cls.MIN_SUPPORTED_VERSIONS:
            return False, f"Unsupported version format: {version.format}"

        min_version = cls.MIN_SUPPORTED_VERSIONS[version.format]

        # For semantic versions, check against minimum
        if version.format == VersionFormat.SEMANTIC:
            if not isinstance(version.version, SemanticVersion):
                return False, "Expected SemanticVersion for SEMANTIC format"

            # Current codebase can read any 1.x.x version
            if version.version.major != 1:
                return False, f"Unsupported major version: {version.version.major}"

            if version.version.minor < min_version.minor:
                return False, f"Version too old: {version} < {min_version}"

        # For timestamp versions, check if it's after minimum
        elif version.format == VersionFormat.TIMESTAMP:
            if not isinstance(version.version, TimestampVersion):
                return False, "Expected TimestampVersion for TIMESTAMP format"

            if version.version.timestamp < min_version.timestamp:
                return False, f"Version too old: {version} < {min_version}"

        return True, None

    @classmethod
    def validate_upgrade_path(
        cls, from_version: SnapshotVersion, to_version: SnapshotVersion
    ) -> tuple[bool, str | None]:
        """Validate that an upgrade path exists and is safe.

        Returns:
            Tuple of (is_valid: bool, reason: Optional[str])
        """
        # Check if both versions are supported
        from_supported, reason = cls.is_supported(from_version)
        if not from_supported:
            return False, f"Source version not supported: {reason}"

        to_supported, reason = cls.is_supported(to_version)
        if not to_supported:
            return False, f"Target version not supported: {reason}"

        # Check if upgrade is possible
        return from_version.can_upgrade_to(to_version)


# ============================================================================
# VERSION UPGRADE PATHS
# ============================================================================

T = TypeVar("T", bound=dict[str, Any])


class VersionUpgrader:
    """Pure, deterministic transforms for snapshot version upgrades.

    Each upgrade is a pure function that takes a snapshot dict and returns
    a new dict in the target format. Original is never modified.

    All upgrade functions must be:
    - Pure (no side effects)
    - Deterministic (same input → same output)
    - Total (defined for all valid inputs)
    - Explicit (no guessing missing fields)
    """

    # Registry of upgrade functions
    # Key: (from_version_str, to_version_str)
    # Value: upgrade function
    _upgrade_registry: dict[tuple[str, str], Any] = {}

    @classmethod
    def register(cls, from_version: str, to_version: str):
        """Decorator to register an upgrade function."""

        def decorator(func):
            cls._upgrade_registry[(from_version, to_version)] = func
            return func

        return decorator

    @classmethod
    def upgrade(
        cls, snapshot: dict[str, Any], target_version: SnapshotVersion
    ) -> dict[str, Any]:
        """Upgrade a snapshot to a target version.

        Args:
            snapshot: The snapshot dictionary to upgrade
            target_version: Target version to upgrade to

        Returns:
            New snapshot dictionary at target version

        Raises:
            ValueError: If upgrade path doesn't exist or is invalid
            KeyError: If snapshot doesn't have required version field
        """
        # Extract current version from snapshot
        if "version" not in snapshot:
            raise KeyError("Snapshot missing 'version' field")

        current_version = SnapshotVersion.parse(snapshot["version"])

        # Check if upgrade is needed
        if str(current_version) == str(target_version):
            return snapshot.copy()  # No-op upgrade, but return copy

        # Validate upgrade path
        can_upgrade, reason = current_version.can_upgrade_to(target_version)
        if not can_upgrade:
            raise ValueError(
                f"Cannot upgrade {current_version} to {target_version}: {reason}"
            )

        # Find upgrade path (direct or through intermediates)
        upgrade_path = cls._find_upgrade_path(current_version, target_version)
        if not upgrade_path:
            raise ValueError(
                f"No upgrade path found from {current_version} to {target_version}"
            )

        # Apply upgrades sequentially
        result = snapshot.copy()
        for from_ver, to_ver in upgrade_path:
            upgrade_func = cls._upgrade_registry.get((str(from_ver), str(to_ver)))
            if not upgrade_func:
                raise ValueError(
                    f"No upgrade function registered for {from_ver} → {to_ver}"
                )

            result = upgrade_func(result)
            result["version"] = str(to_ver)

        return result

    @classmethod
    def _find_upgrade_path(
        cls, from_version: SnapshotVersion, to_version: SnapshotVersion
    ) -> list | None:
        """Find a path of upgrade functions from one version to another.

        For now, only supports direct upgrades. In the future, this could
        handle multi-step upgrades through intermediate versions.
        """
        # Check for direct upgrade
        key = (str(from_version), str(to_version))
        if key in cls._upgrade_registry:
            return [(from_version, to_version)]

        # Find multi-step upgrade path through intermediate versions
        # Implement simple BFS to find shortest path using registered edges only
        from collections import deque

        queue = deque([from_version])
        parents: dict[SnapshotVersion, SnapshotVersion | None] = {from_version: None}

        while queue:
            current_version = queue.popleft()

            # Explore all registered upgrades from current version
            for potential_version in cls._upgrade_registry.keys():
                if potential_version[0] != str(current_version):
                    continue

                next_version = SnapshotVersion.parse(potential_version[1])
                if next_version in parents:
                    continue

                parents[next_version] = current_version
                if next_version == to_version:
                    # Build path by walking parents
                    path = [next_version]
                    while parents[path[-1]] is not None:
                        path.append(parents[path[-1]])
                    path.reverse()

                    result = []
                    for i in range(len(path) - 1):
                        result.append((path[i], path[i + 1]))
                    return result

                queue.append(next_version)

        return None


# ============================================================================
# UPGRADE FUNCTION DEFINITIONS
# ============================================================================


@VersionUpgrader.register("1.0.0", "1.1.0")
def upgrade_1_0_0_to_1_1_0(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Example upgrade from v1.0.0 to v1.1.0.

    Adds metadata fields for recording environment context.
    This is a template - actual upgrades will be defined as format evolves.
    """
    # Always start with a copy
    result = snapshot.copy()

    # Add new metadata section if not present
    if "metadata" not in result:
        result["metadata"] = {}

    metadata = result["metadata"]

    # Add environment context fields with explicit defaults
    if "environment" not in metadata:
        metadata["environment"] = {
            "python_version": None,  # Will be populated by runtime
            "platform": None,
            "codemarshal_version": None,
            "recording_time": datetime.now(UTC).isoformat(),
        }

    # Ensure all required fields exist (explicit, no guessing)
    env_fields = ["python_version", "platform", "codemarshal_version", "recording_time"]
    for field in env_fields:
        if field not in metadata["environment"]:
            metadata["environment"][field] = None

    return result


@VersionUpgrader.register("1.1.0", "1.2.0")
def upgrade_1_1_0_to_1_2_0(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Example upgrade from v1.1.0 to v1.2.0.

    Adds integrity hash to each observation for tamper detection.
    """
    result = snapshot.copy()

    # Add integrity section
    if "integrity" not in result:
        result["integrity"] = {
            "version": "sha256",  # Default hash algorithm
            "observations_hash": None,  # Will be computed by integrity module
            "anchors_hash": None,
            "full_hash": None,
        }

    # Ensure each observation has a placeholder for its hash
    if "observations" in result:
        for obs_type, observations in result["observations"].items():
            if isinstance(observations, list):
                for i, obs in enumerate(observations):
                    if isinstance(obs, dict) and "integrity_hash" not in obs:
                        result["observations"][obs_type][i]["integrity_hash"] = None

    return result


# ============================================================================
# PUBLIC API
# ============================================================================


def get_current_version() -> SnapshotVersion:
    """Get the current snapshot format version."""
    return SnapshotVersion.current()


def validate_snapshot_version(version_str: str) -> tuple[bool, str | None]:
    """Validate that a version string is supported.

    Returns:
        Tuple of (is_valid: bool, reason: Optional[str])
    """
    try:
        version = SnapshotVersion.parse(version_str)
        return VersionCompatibility.is_supported(version)
    except ValueError as e:
        return False, str(e)


def check_compatibility(from_version: str, to_version: str) -> tuple[bool, str | None]:
    """Check if a snapshot can be upgraded from one version to another.

    Returns:
        Tuple of (is_compatible: bool, reason: Optional[str])
    """
    try:
        from_ver = SnapshotVersion.parse(from_version)
        to_ver = SnapshotVersion.parse(to_version)
        return VersionCompatibility.validate_upgrade_path(from_ver, to_ver)
    except ValueError as e:
        return False, str(e)


def upgrade_snapshot(snapshot: dict[str, Any], target_version: str) -> dict[str, Any]:
    """Upgrade a snapshot dictionary to a target version.

    Returns a new dictionary; original is never modified.

    Raises:
        ValueError: If upgrade is not possible
        KeyError: If snapshot is missing required fields
    """
    target_ver = SnapshotVersion.parse(target_version)
    return VersionUpgrader.upgrade(snapshot, target_ver)


# ============================================================================
# SERIALIZATION UTILITIES
# ============================================================================


def serialize_version(version: SnapshotVersion) -> str:
    """Serialize a version object to string."""
    return str(version)


def deserialize_version(version_str: str) -> SnapshotVersion:
    """Deserialize a version string to object."""
    return SnapshotVersion.parse(version_str)


# ============================================================================
# TEST UTILITIES (for internal testing only)
# ============================================================================


def _create_test_snapshot(version: str | None = None) -> dict[str, Any]:
    """Create a minimal valid snapshot for testing.

    Internal use only - for testing version compatibility.
    """
    if version is None:
        version = str(get_current_version())

    return {
        "version": version,
        "metadata": {
            "created_at": datetime.now(UTC).isoformat(),
            "source_path": "/test/path",
        },
        "observations": {"files": [], "imports": []},
        "anchors": [],
    }


def get_snapshot_version(
    storage_path: str, snapshot_id: UUID
) -> SnapshotVersion | None:
    """
    Get the version of a stored snapshot.

    Args:
        storage_path: Path to observation storage
        snapshot_id: ID of snapshot to check

    Returns:
        SnapshotVersion if found, None otherwise
    """
    try:
        base_path = Path(storage_path)
        # Try standard locations
        candidates = [
            base_path / "snapshots" / f"{snapshot_id}.json",
            base_path / f"{snapshot_id}.json",
        ]

        target_file = None
        for candidate in candidates:
            if candidate.exists():
                target_file = candidate
                break

        if not target_file:
            return None

        with open(target_file, encoding="utf-8") as f:
            data = json.load(f)
            if "version" in data:
                return SnapshotVersion.parse(data["version"])

        return None

    except Exception:
        return None


def get_latest_snapshot(storage_path: str) -> UUID | None:
    """
    Get the most recent snapshot ID from storage.

    Args:
        storage_path: Path to observation storage

    Returns:
        UUID of latest snapshot, or None if none found
    """
    base_path = Path(storage_path)
    candidates = []

    # Prefer snapshots directory, but allow flat layout
    snapshots_dir = base_path / "snapshots"
    if snapshots_dir.exists():
        candidates.extend(snapshots_dir.glob("*.json"))
    candidates.extend(base_path.glob("*.json"))

    latest_id: UUID | None = None
    latest_time: datetime | None = None

    for snapshot_file in candidates:
        try:
            with open(snapshot_file, encoding="utf-8") as f:
                data = json.load(f)

            # Filter out non-snapshot JSON files
            if not isinstance(data, dict):
                continue
            if not {"version", "metadata", "payload"}.issubset(data.keys()):
                continue
            if not isinstance(data.get("metadata"), dict):
                continue

            metadata = data.get("metadata", {})
            created_at_str = metadata.get("created_at") or data.get("created_at")
            snapshot_id_str = metadata.get("snapshot_id") or data.get("snapshot_id")

            if not snapshot_id_str:
                # Fall back to filename without extension
                snapshot_id_str = snapshot_file.stem

            # Parse timestamp if available, else use file mtime
            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str)
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=UTC)
            else:
                created_at = datetime.fromtimestamp(
                    snapshot_file.stat().st_mtime, tz=UTC
                )

            if latest_time is None or created_at > latest_time:
                latest_time = created_at
                latest_id = UUID(str(snapshot_id_str))
        except Exception:
            continue

    return latest_id
