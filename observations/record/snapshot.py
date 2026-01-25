"""
observations/record/snapshot.py

Complete observation snapshot - the forensic unit of truth.

A snapshot is a sealed bundle of:
- All observation outputs (from all eyes)
- Metadata about how and when they were taken
- References to anchors
- Integrity material (hash roots)

This module defines:
- Snapshot data structure (immutable)
- Rules for construction (only from valid observations)
- Serialization (canonical form)
- Deserialization (read-only)

Production principle: This answers "what did the system see at time T?" without negotiation.
"""

import json
import uuid
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from functools import total_ordering
from pathlib import Path, PurePath
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    cast,
)

if TYPE_CHECKING:
    # Type-only imports to avoid circular dependencies
    from observations.record.anchors import Anchor
    from observations.record.integrity import IntegrityRoot

# ============================================================================
# CORE TYPES
# ============================================================================


@dataclass(frozen=True)
class SnapshotMetadata:
    """Immutable metadata about a snapshot."""

    # Core identification
    snapshot_id: str  # UUID v4, globally unique
    created_at: datetime  # UTC, timezone-aware

    # Source information
    source_path: str  # Absolute path that was observed
    source_type: str  # 'directory', 'file', 'project'

    # System context
    system_platform: str  # platform.system()
    python_version: str  # platform.python_version()
    codemarshal_version: str  # From pyproject.toml or defaults

    # Recording context
    recording_duration_seconds: float  # How long observation took
    observation_count: int  # Total number of observations
    eyes_used: frozenset[str]  # Which observation eyes were active

    # Constitutional compliance markers
    limitations_declared: bool  # Whether limitations were explicitly declared
    invariants_preserved: bool  # Whether all invariants were maintained
    input_validated: bool  # Whether input passed validation

    @classmethod
    def create(
        cls,
        source_path: str | Path,
        recording_duration: float,
        observation_count: int,
        eyes_used: list[str],
        codemarshal_version: str = "0.1.0-dev",
        limitations_declared: bool = True,
        invariants_preserved: bool = True,
        input_validated: bool = True,
    ) -> "SnapshotMetadata":
        """Create new metadata with current context."""
        import platform

        source_path_str = str(Path(source_path).absolute())

        return cls(
            snapshot_id=str(uuid.uuid4()),
            created_at=datetime.now(UTC),
            source_path=source_path_str,
            source_type="directory" if Path(source_path).is_dir() else "file",
            system_platform=platform.system(),
            python_version=platform.python_version(),
            codemarshal_version=codemarshal_version,
            recording_duration_seconds=recording_duration,
            observation_count=observation_count,
            eyes_used=frozenset(eyes_used),
            limitations_declared=limitations_declared,
            invariants_preserved=invariants_preserved,
            input_validated=input_validated,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        result = asdict(self)

        # Convert datetime to ISO format
        result["created_at"] = self.created_at.isoformat()

        # Convert frozenset to sorted list for determinism
        result["eyes_used"] = sorted(self.eyes_used)

        return result


class ObservationCategory(str, Enum):
    """Categories of observations for organization."""

    STRUCTURE = "structure"  # Files, directories, paths
    CONTENT = "content"  # File contents, imports, exports
    BOUNDARY = "boundary"  # Module boundaries, dependencies
    ENCODING = "encoding"  # File encoding, type detection
    VALIDATION = "validation"  # Input validation results
    LIMITATION = "limitation"  # Declared limitations


@dataclass(frozen=True)
class ObservationGroup:
    """Immutable grouping of observations by category."""

    category: ObservationCategory
    eye_name: str  # Name of the observation eye that produced these
    observations: tuple[dict[str, Any], ...]  # Immutable tuple of observation dicts
    limitation: str | None = None  # What this eye cannot see

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "category": self.category.value,
            "eye_name": self.eye_name,
            "observations": list(self.observations),  # Convert tuple to list for JSON
            "limitation": self.limitation,
        }

    @property
    def count(self) -> int:
        """Number of observations in this group."""
        return len(self.observations)

    @classmethod
    def from_eye_results(
        cls,
        category: ObservationCategory,
        eye_name: str,
        results: list[dict[str, Any]],
        limitation: str | None = None,
    ) -> "ObservationGroup":
        """Create group from eye results with normalization."""
        # Normalize each observation for determinism
        normalized = []
        for obs in results:
            normalized.append(cls._normalize_observation(obs))

        return cls(
            category=category,
            eye_name=eye_name,
            observations=tuple(normalized),
            limitation=limitation,
        )

    @staticmethod
    def _normalize_observation(obs: dict[str, Any]) -> dict[str, Any]:
        """Normalize a single observation for deterministic ordering."""

        def recursive_normalize(obj: Any) -> Any:
            """Recursively normalize nested structures."""
            if isinstance(obj, dict):
                # Sort keys and normalize values
                return OrderedDict(
                    sorted((k, recursive_normalize(v)) for k, v in obj.items())
                )
            elif isinstance(obj, list):
                # Normalize each item, sort if it's a list of primitives/dicts
                normalized_items = [recursive_normalize(item) for item in obj]

                # Sort if all items are comparable types
                try:
                    # Try to sort - will fail for complex nested structures
                    return sorted(normalized_items)
                except TypeError:
                    # Leave in original order if not sortable
                    return normalized_items
            elif isinstance(obj, tuple):
                # Convert to list, normalize, then back to tuple
                return tuple(recursive_normalize(list(obj)))
            elif isinstance(obj, set):
                # Convert to sorted list
                return sorted(recursive_normalize(list(obj)))
            elif isinstance(obj, (str, int, float, bool)) or obj is None:
                # Primitive types unchanged
                return obj
            elif isinstance(obj, (Path, PurePath)):
                # Convert paths to strings
                return str(obj)
            elif isinstance(obj, datetime):
                # Convert datetime to ISO format
                return obj.isoformat()
            elif hasattr(obj, "to_dict"):
                # Convert objects with to_dict method
                return recursive_normalize(obj.to_dict())
            else:
                # Unknown type - try to convert to string
                return str(obj)

        return cast(dict[str, Any], recursive_normalize(obs))


@dataclass(frozen=True)
class SnapshotPayload:
    """Immutable payload containing all observations."""

    groups: tuple[ObservationGroup, ...]

    @classmethod
    def from_groups(cls, groups: list[ObservationGroup]) -> "SnapshotPayload":
        """Create payload from groups with sorting for determinism."""
        # Sort groups by category, then eye_name
        sorted_groups = sorted(groups, key=lambda g: (g.category.value, g.eye_name))

        return cls(groups=tuple(sorted_groups))

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {"groups": [group.to_dict() for group in self.groups]}

    @property
    def total_observations(self) -> int:
        """Total number of observations across all groups."""
        return sum(group.count for group in self.groups)

    @property
    def categories_present(self) -> frozenset[str]:
        """Set of observation categories present."""
        return frozenset(group.category.value for group in self.groups)

    def get_group(
        self, category: ObservationCategory, eye_name: str
    ) -> ObservationGroup | None:
        """Get a specific observation group."""
        for group in self.groups:
            if group.category == category and group.eye_name == eye_name:
                return group
        return None


# ============================================================================
# SNAPSHOT CORE
# ============================================================================


@total_ordering
@dataclass(frozen=True)
class Snapshot:
    """
    Immutable snapshot of observations.

    This is the core forensic unit - once created, it never changes.
    """

    # Version and identification
    version: str  # Format version from observations.record.version
    metadata: SnapshotMetadata

    # Core content
    payload: SnapshotPayload

    # Integrity and references
    anchors: tuple["Anchor", ...] | None = None  # Will be set after creation
    integrity_root: Optional["IntegrityRoot"] = None  # Will be set after creation

    # Cache for deterministic serialization
    _canonical_dict: dict[str, Any] | None = field(
        default=None, init=False, repr=False, compare=False
    )
    _canonical_json: str | None = field(
        default=None, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        """Validate snapshot after creation."""
        # Validate version format (basic check)
        if not self.version or "." not in self.version:
            raise ValueError(f"Invalid version format: {self.version}")

        # Validate metadata
        if not isinstance(self.metadata, SnapshotMetadata):
            raise TypeError(
                f"metadata must be SnapshotMetadata, got {type(self.metadata)}"
            )

        # Validate payload
        if not isinstance(self.payload, SnapshotPayload):
            raise TypeError(
                f"payload must be SnapshotPayload, got {type(self.payload)}"
            )

        # Validate observation count matches metadata
        if self.payload.total_observations != self.metadata.observation_count:
            raise ValueError(
                f"Observation count mismatch: "
                f"metadata says {self.metadata.observation_count}, "
                f"payload has {self.payload.total_observations}"
            )

    @classmethod
    def create(
        cls,
        source_path: str | Path,
        observation_groups: list[ObservationGroup],
        recording_duration: float,
        codemarshal_version: str = "0.1.0-dev",
        version: str = "1.0.0",
    ) -> "Snapshot":
        """
        Create a new snapshot from observation groups.

        This is the primary constructor - all snapshots must be created through this.
        """
        # Count total observations
        total_observations = sum(group.count for group in observation_groups)

        # Get list of eyes used
        eyes_used = [group.eye_name for group in observation_groups]

        # Create metadata
        metadata = SnapshotMetadata.create(
            source_path=source_path,
            recording_duration=recording_duration,
            observation_count=total_observations,
            eyes_used=eyes_used,
            codemarshal_version=codemarshal_version,
        )

        # Create payload
        payload = SnapshotPayload.from_groups(observation_groups)

        return cls(
            version=version,
            metadata=metadata,
            payload=payload,
            anchors=None,
            integrity_root=None,
        )

    def with_anchors(self, anchors: list["Anchor"]) -> "Snapshot":
        """Return a new snapshot with anchors set."""
        return Snapshot(
            version=self.version,
            metadata=self.metadata,
            payload=self.payload,
            anchors=tuple(
                sorted(anchors, key=lambda a: a.identifier)
            ),  # Sort for determinism
            integrity_root=self.integrity_root,
        )

    def with_integrity(self, integrity_root: "IntegrityRoot") -> "Snapshot":
        """Return a new snapshot with integrity root set."""
        return Snapshot(
            version=self.version,
            metadata=self.metadata,
            payload=self.payload,
            anchors=self.anchors,
            integrity_root=integrity_root,
        )

    # ============================================================================
    # SERIALIZATION
    # ============================================================================

    def to_dict(self, canonical: bool = False) -> dict[str, Any]:
        """
        Convert snapshot to dictionary.

        Args:
            canonical: If True, returns deterministic canonical form for hashing.
                      If False, returns pretty-printed form for readability.
        """
        if canonical and self._canonical_dict is not None:
            return self._canonical_dict.copy()

        # Build base dictionary
        result = OrderedDict() if canonical else {}

        # Add version first (important for canonical form)
        result["version"] = self.version

        # Add metadata
        result["metadata"] = self.metadata.to_dict()

        # Add payload
        result["payload"] = self.payload.to_dict()

        # Add anchors if present
        if self.anchors is not None:
            if TYPE_CHECKING:
                pass
            anchors: list[Anchor] = list(self.anchors)

            # Convert anchors to their canonical form
            anchor_dicts = [anchor.to_dict() for anchor in anchors]

            # Sort for determinism in canonical form
            if canonical:
                anchor_dicts.sort(key=lambda d: json.dumps(d, sort_keys=True))

            result["anchors"] = anchor_dicts

        # Add integrity root if present
        if self.integrity_root is not None:
            if TYPE_CHECKING:
                pass
            result["integrity"] = self.integrity_root.to_dict()

        # Cache canonical form
        if canonical:
            # Ensure all nested structures are in canonical form
            canonical_result = self._make_canonical(result)
            object.__setattr__(self, "_canonical_dict", canonical_result)
            return canonical_result.copy()

        return result

    def _make_canonical(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively ensure dictionary is in canonical form."""

        def canonicalize(obj: Any) -> Any:
            if isinstance(obj, dict):
                # Sort keys and canonicalize values
                sorted_items = sorted(obj.items())
                return OrderedDict((k, canonicalize(v)) for k, v in sorted_items)
            elif isinstance(obj, list):
                # Canonicalize each item
                canonical_items = [canonicalize(item) for item in obj]

                # Sort if items are comparable
                try:
                    # Try JSON string comparison for sorting
                    return sorted(
                        canonical_items, key=lambda x: json.dumps(x, sort_keys=True)
                    )
                except TypeError:
                    # Leave in original order if not sortable
                    return canonical_items
            elif isinstance(obj, tuple):
                # Convert to list, canonicalize, back to tuple
                return tuple(canonicalize(list(obj)))
            else:
                # Primitives and strings unchanged
                return obj

        return cast(dict[str, Any], canonicalize(data))

    def to_json(self, canonical: bool = False, indent: int | None = None) -> str:
        """
        Convert snapshot to JSON string.

        Args:
            canonical: If True, returns deterministic canonical JSON for hashing.
                      If False, returns pretty-printed JSON for readability.
            indent: Indentation level for pretty printing (None for compact).
        """
        if canonical and self._canonical_json is not None:
            return self._canonical_json

        if canonical:
            # Force no whitespace for canonical form
            json_str = json.dumps(
                self.to_dict(canonical=True),
                separators=(",", ":"),
                sort_keys=False,  # We already sorted in to_dict
            )
            object.__setattr__(self, "_canonical_json", json_str)
            return json_str
        else:
            return json.dumps(
                self.to_dict(canonical=False), indent=indent, sort_keys=True
            )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Snapshot":
        """
        Create snapshot from dictionary.

        Note: This is read-only deserialization. The resulting snapshot
        is immutable but may not have the same Python object structure
        as one created through create().
        """
        # Basic validation
        required_keys = {"version", "metadata", "payload"}
        if not required_keys.issubset(data.keys()):
            missing = required_keys - set(data.keys())
            raise ValueError(f"Missing required keys: {missing}")

        # Parse metadata
        metadata_dict = data["metadata"]

        # Convert ISO timestamp back to datetime
        if "created_at" in metadata_dict and isinstance(
            metadata_dict["created_at"], str
        ):
            metadata_dict["created_at"] = datetime.fromisoformat(
                metadata_dict["created_at"]
            )

        # Convert eyes_used list back to frozenset
        if "eyes_used" in metadata_dict and isinstance(
            metadata_dict["eyes_used"], list
        ):
            metadata_dict["eyes_used"] = frozenset(metadata_dict["eyes_used"])

        metadata = SnapshotMetadata(**metadata_dict)

        # Parse payload
        payload_dict = data["payload"]
        groups = []

        for group_dict in payload_dict.get("groups", []):
            # Convert observations list to tuple
            observations = tuple(group_dict.get("observations", []))

            group = ObservationGroup(
                category=ObservationCategory(group_dict["category"]),
                eye_name=group_dict["eye_name"],
                observations=observations,
                limitation=group_dict.get("limitation"),
            )
            groups.append(group)

        payload = SnapshotPayload(groups=tuple(groups))

        # Parse anchors if present
        anchors = None
        if "anchors" in data:
            if TYPE_CHECKING:
                pass
            anchor_objs = []
            for anchor_dict in data["anchors"]:
                # Anchor.from_dict will be implemented in anchors.py
                # For now, we'll pass the dict
                anchor_objs.append(anchor_dict)
            anchors = tuple(anchor_objs)

        # Parse integrity if present
        integrity_root = None
        if "integrity" in data:
            if TYPE_CHECKING:
                pass
            integrity_root = data[
                "integrity"
            ]  # Will be properly parsed in integrity.py

        return cls(
            version=data["version"],
            metadata=metadata,
            payload=payload,
            anchors=anchors,
            integrity_root=integrity_root,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Snapshot":
        """Create snapshot from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    # ============================================================================
    # PROPERTIES AND QUERIES
    # ============================================================================

    @property
    def snapshot_id(self) -> str:
        """Get the snapshot's unique ID."""
        return self.metadata.snapshot_id

    @property
    def created_at(self) -> datetime:
        """Get the creation timestamp."""
        return self.metadata.created_at

    @property
    def source_path(self) -> str:
        """Get the observed source path."""
        return self.metadata.source_path

    @property
    def total_observations(self) -> int:
        """Get total number of observations."""
        return self.payload.total_observations

    def has_anchors(self) -> bool:
        """Check if snapshot has anchors."""
        return self.anchors is not None and len(self.anchors) > 0

    def has_integrity(self) -> bool:
        """Check if snapshot has integrity root."""
        return self.integrity_root is not None

    def is_complete(self) -> bool:
        """Check if snapshot is complete (has anchors and integrity)."""
        return self.has_anchors() and self.has_integrity()

    def get_observation_counts_by_category(self) -> dict[str, int]:
        """Get counts of observations by category."""
        counts = {}
        for group in self.payload.groups:
            category = group.category.value
            counts[category] = counts.get(category, 0) + group.count
        return counts

    def get_observation_counts_by_eye(self) -> dict[str, int]:
        """Get counts of observations by eye."""
        counts = {}
        for group in self.payload.groups:
            eye = group.eye_name
            counts[eye] = counts.get(eye, 0) + group.count
        return counts

    # ============================================================================
    # COMPARISON
    # ============================================================================

    def __eq__(self, other: Any) -> bool:
        """Snapshots are equal if their canonical JSON is identical."""
        if not isinstance(other, Snapshot):
            return NotImplemented

        # Compare canonical forms for true equality
        return self.to_json(canonical=True) == other.to_json(canonical=True)

    def __lt__(self, other: Any) -> bool:
        """Snapshots are ordered by creation time."""
        if not isinstance(other, Snapshot):
            return NotImplemented

        return self.created_at < other.created_at

    def __hash__(self) -> int:
        """Hash based on canonical JSON."""
        return hash(self.to_json(canonical=True))

    # ============================================================================
    # STRING REPRESENTATIONS
    # ============================================================================

    def __repr__(self) -> str:
        return (
            f"Snapshot("
            f"id={self.snapshot_id[:8]}..., "
            f"created={self.created_at.isoformat()[:19]}Z, "
            f"observations={self.total_observations}, "
            f"source={Path(self.source_path).name}"
            f")"
        )

    def summary(self) -> str:
        """Get a human-readable summary of the snapshot."""
        lines = [
            f"Snapshot: {self.snapshot_id[:8]}...",
            f"Created: {self.created_at.isoformat()[:19]}Z",
            f"Source: {self.source_path}",
            f"Observations: {self.total_observations}",
        ]

        # Add observation breakdown
        counts_by_category = self.get_observation_counts_by_category()
        if counts_by_category:
            lines.append("By category:")
            for category, count in sorted(counts_by_category.items()):
                lines.append(f"  {category}: {count}")

        # Add status markers
        status = []
        if self.has_anchors():
            status.append(f"anchors={len(self.anchors)}")  # type: ignore
        else:
            status.append("no-anchors")

        if self.has_integrity():
            status.append("integrity-verified")
        else:
            status.append("no-integrity")

        lines.append(f"Status: {', '.join(status)}")

        return "\n".join(lines)


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================


def create_empty_snapshot(source_path: str | Path) -> Snapshot:
    """Create an empty snapshot (for testing or initialization)."""
    metadata = SnapshotMetadata.create(
        source_path=source_path,
        recording_duration=0.0,
        observation_count=0,
        eyes_used=[],
    )

    payload = SnapshotPayload(groups=())

    return Snapshot(version="1.0.0", metadata=metadata, payload=payload)


def validate_snapshot_for_storage(snapshot: Snapshot) -> tuple[bool, str | None]:
    """
    Validate that a snapshot is complete and ready for storage.

    Returns:
        Tuple of (is_valid: bool, reason: Optional[str])
    """
    if not snapshot.has_anchors():
        return False, "Snapshot missing anchors"

    if not snapshot.has_integrity():
        return False, "Snapshot missing integrity root"

    # Check observation count matches metadata
    if snapshot.total_observations != snapshot.metadata.observation_count:
        return False, (
            f"Observation count mismatch: "
            f"metadata={snapshot.metadata.observation_count}, "
            f"actual={snapshot.total_observations}"
        )

    # Check all required fields are present
    required_metadata_fields = [
        "snapshot_id",
        "created_at",
        "source_path",
        "observation_count",
    ]

    for required_field in required_metadata_fields:
        if not getattr(snapshot.metadata, required_field, None):
            return False, f"Missing metadata field: {required_field}"

    return True, None


# ============================================================================
# CANONICAL HASHING UTILITY
# ============================================================================


def get_canonical_hash_input(snapshot: Snapshot) -> bytes:
    """
    Get the canonical byte representation for hashing.

    This should only be used by the integrity module.
    """
    canonical_json = snapshot.to_json(canonical=True)
    return canonical_json.encode("utf-8")


# ============================================================================
# SNAPSHOT BUILDER (For incremental construction)
# ============================================================================


class SnapshotBuilder:
    """
    Builder for creating snapshots incrementally.

    This is the only allowed way to construct snapshots outside of deserialization.
    """

    def __init__(self, source_path: str | Path):
        self.source_path = Path(source_path).absolute()
        self.groups: list[ObservationGroup] = []
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

    def start_recording(self) -> None:
        """Start the recording timer."""
        if self.start_time is not None:
            raise RuntimeError("Recording already started")
        self.start_time = datetime.now(UTC)

    def add_observations(
        self,
        category: ObservationCategory,
        eye_name: str,
        observations: list[dict[str, Any]],
        limitation: str | None = None,
    ) -> None:
        """Add observations from an eye."""
        if self.start_time is None:
            raise RuntimeError("Must start recording before adding observations")

        group = ObservationGroup.from_eye_results(
            category=category,
            eye_name=eye_name,
            results=observations,
            limitation=limitation,
        )
        self.groups.append(group)

    def build(self, codemarshal_version: str = "0.1.0-dev") -> Snapshot:
        """Build the final snapshot."""
        if self.start_time is None:
            raise RuntimeError("Must start recording before building")

        if self.end_time is None:
            self.end_time = datetime.now(UTC)

        recording_duration = (self.end_time - self.start_time).total_seconds()

        return Snapshot.create(
            source_path=self.source_path,
            observation_groups=self.groups,
            recording_duration=recording_duration,
            codemarshal_version=codemarshal_version,
        )

    def finish(self) -> None:
        """Mark recording as finished."""
        if self.end_time is not None:
            raise RuntimeError("Recording already finished")
        self.end_time = datetime.now(UTC)


# Export public API
__all__ = [
    "Snapshot",
    "CodeSnapshot",  # Alias for backward compatibility
    "SnapshotMetadata",
    "SnapshotPayload",
    "ObservationGroup",
    "SnapshotBuilder",
]

# Backward compatibility alias
CodeSnapshot = Snapshot
