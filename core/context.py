"""
Global Immutable Runtime Context for CodeMarshal.

Constitutional Basis:
- Article 9: Immutable Observations
- Article 13: Deterministic Operation

Production Responsibility:
Represent all facts about an execution that must never change.
This is not configuration. This is not state. This is execution reality.
"""

from __future__ import annotations

import datetime
import hashlib
import sys
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class ExecutionMode(Enum):
    """Valid execution modes for CodeMarshal."""

    CLI = auto()  # Command-line interface
    TUI = auto()  # Terminal user interface
    API = auto()  # Programmatic API

    @classmethod
    def from_string(cls, mode_str: str) -> ExecutionMode:
        """Convert string to execution mode with validation."""
        mode_str_upper = mode_str.upper()
        if mode_str_upper not in cls.__members__:
            raise ValueError(f"Unknown execution mode: {mode_str}")
        return cls[mode_str_upper]

    def __str__(self) -> str:
        return self.name


class EnforcementLevel(Enum):
    """Levels of constitutional enforcement."""

    # Article 1-4: Foundational Truths (never violate)
    FOUNDATIONAL = auto()

    # Article 5-8: Interface Integrity (strong defaults)
    INTERFACE = auto()

    # Article 9-12: Architectural Constraints
    ARCHITECTURAL = auto()

    # Article 13-15: System Behavior
    SYSTEM = auto()

    # Article 16-18: Aesthetic Constraints
    AESTHETIC = auto()

    # Article 19-21: Evolution Rules
    EVOLUTION = auto()


@dataclass(frozen=True, order=True)
class ConstitutionalRule:
    """Immutable representation of a constitutional rule."""

    tier: int
    article_number: int
    title: str
    content: str
    enforcement_level: EnforcementLevel

    @property
    def identifier(self) -> str:
        """Get unique identifier for this rule."""
        return f"Tier{self.tier}_Article{self.article_number}"

    def __hash__(self) -> int:
        """Make hashable for use in sets."""
        return hash((self.tier, self.article_number, self.title))

    def __str__(self) -> str:
        return f"Tier {self.tier}, Article {self.article_number}: {self.title}"


@dataclass(frozen=True)
class RuntimeContext:
    """
    Immutable runtime context for CodeMarshal execution.

    Constitutional Guarantees:
    1. Fully immutable after construction
    2. Hashable / serializable
    3. Safe to embed in evidence metadata
    4. Deterministic across executions
    """

    # Core execution facts
    investigation_root: Path
    constitution_hash: str
    code_version_hash: str
    execution_mode: str  # Stored as string for serialization

    # Enforcement flags
    network_enabled: bool = False  # Article 12: Local Operation
    mutation_allowed: bool = False  # Article 9: Immutable Observations
    runtime_imports_allowed: bool = False  # Article 1: Observation Purity

    # Optional runtime parameters used for orchestration (e.g., streaming)
    parameters: dict[str, Any] = field(default_factory=dict)

    # Session identification
    session_id: uuid.UUID = field(default_factory=uuid.uuid4)
    start_timestamp: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )

    # Python runtime information (for reproducibility)
    python_version: tuple[int, int, int] = field(
        default_factory=lambda: sys.version_info[:3]
    )
    platform: str = field(default_factory=lambda: sys.platform)

    # System limits (deterministic behavior)
    max_file_size_bytes: int = 100 * 1024 * 1024  # 100MB
    max_total_observation_size_bytes: int = 1 * 1024 * 1024 * 1024  # 1GB
    max_recursion_depth: int = 1000

    # Constitutional enforcement levels
    enforcement_levels: tuple[EnforcementLevel, ...] = field(
        default_factory=lambda: tuple(EnforcementLevel)
    )

    def __post_init__(self) -> None:
        """
        Validate runtime context after initialization.

        Constitutional Basis: Article 13 (Deterministic Operation)
        """
        # Validate investigation root exists and is a directory
        if not self.investigation_root.exists():
            raise ValueError(
                f"Investigation root does not exist: {self.investigation_root}"
            )

        if not self.investigation_root.is_dir():
            raise ValueError(
                f"Investigation root is not a directory: {self.investigation_root}"
            )

        # Validate hashes are proper hex strings
        if not self._is_valid_hex_string(self.constitution_hash):
            raise ValueError(
                f"Invalid constitution hash format: {self.constitution_hash}"
            )

        if not self._is_valid_hex_string(self.code_version_hash):
            raise ValueError(
                f"Invalid code version hash format: {self.code_version_hash}"
            )

        # Validate execution mode
        try:
            ExecutionMode.from_string(self.execution_mode)
        except ValueError as e:
            raise ValueError(f"Invalid execution mode: {self.execution_mode}") from e

        if not isinstance(self.parameters, dict):
            raise ValueError("parameters must be a dict")

        # Validate timestamps are timezone-aware
        if self.start_timestamp.tzinfo is None:
            raise ValueError("start_timestamp must be timezone-aware")

        # Validate limits are positive
        if self.max_file_size_bytes <= 0:
            raise ValueError("max_file_size_bytes must be positive")

        if self.max_total_observation_size_bytes <= 0:
            raise ValueError("max_total_observation_size_bytes must be positive")

        if self.max_recursion_depth <= 0:
            raise ValueError("max_recursion_depth must be positive")

    def _is_valid_hex_string(self, hex_string: str) -> bool:
        """Check if string is valid hexadecimal."""
        try:
            int(hex_string, 16)
            return True
        except ValueError:
            return False

    @property
    def resolved_investigation_root(self) -> Path:
        """
        Get fully resolved, absolute investigation root.
        """
        return self.investigation_root.resolve().absolute()

    @property
    def canonical_paths(self) -> dict[str, str]:
        """
        Get canonical path representations for reproducibility.

        Constitutional Basis: Article 13 (Deterministic Operation)
        """
        paths: dict[str, str] = {
            "investigation_root": str(self.resolved_investigation_root),
            "cwd": str(Path.cwd().resolve()),
            "home": str(Path.home().resolve()) if Path.home().exists() else "",
        }

        # Add executable path
        if sys.executable:
            paths["python_executable"] = str(Path(sys.executable).resolve())

        return paths

    @property
    def execution_mode_enum(self) -> ExecutionMode:
        """Get execution mode as enum."""
        return ExecutionMode.from_string(self.execution_mode)

    @property
    def session_id_str(self) -> str:
        """Get session ID as string."""
        return str(self.session_id)

    @property
    def investigation_id(self) -> str:
        """Backward-compatible alias for session_id_str."""
        return self.session_id_str

    @property
    def start_timestamp_iso(self) -> str:
        """Get start timestamp as ISO 8601 string."""
        return self.start_timestamp.isoformat()

    @property
    def runtime_fingerprint(self) -> str:
        """
        Generate deterministic fingerprint of runtime environment.

        Constitutional Basis: Article 13 (Deterministic Operation)
        Used to ensure reproducibility across executions.
        """
        fingerprint_data: dict[str, Any] = {
            "python_version": self.python_version,
            "platform": self.platform,
            "execution_mode": self.execution_mode,
            "constitution_hash": self.constitution_hash,
            "code_version_hash": self.code_version_hash,
            "canonical_paths": self.canonical_paths,
            "enforcement_flags": {
                "network": self.network_enabled,
                "mutation": self.mutation_allowed,
                "runtime_imports": self.runtime_imports_allowed,
            },
            "limits": {
                "max_file_size": self.max_file_size_bytes,
                "max_total_size": self.max_total_observation_size_bytes,
                "max_recursion": self.max_recursion_depth,
            },
        }

        # Convert to deterministic string representation
        import json

        fingerprint_str = json.dumps(
            fingerprint_data, sort_keys=True, separators=(",", ":")
        )

        # Calculate hash
        return hashlib.sha256(fingerprint_str.encode("utf-8")).hexdigest()

    def relative_path(self, absolute_path: Path) -> str:
        """
        Convert absolute path to relative path from investigation root.

        Constitutional Basis: Article 13 (Deterministic Operation)
        Paths are always expressed relative to investigation root for reproducibility.
        """
        abs_path = absolute_path.resolve()
        try:
            rel_path = abs_path.relative_to(self.resolved_investigation_root)
            return str(rel_path)
        except ValueError:
            # Path is outside investigation root
            return str(abs_path)

    def absolute_path(self, relative_path: Path) -> Path:
        """
        Convert relative path to absolute path from investigation root.

        Constitutional Basis: Article 13 (Deterministic Operation)
        """
        if relative_path.is_absolute():
            return relative_path.resolve()

        # Ensure path doesn't escape investigation root
        resolved = (self.resolved_investigation_root / relative_path).resolve()

        # Security check: ensure resolved path is within investigation root
        try:
            resolved.relative_to(self.resolved_investigation_root)
        except ValueError:
            raise ValueError(f"Path escapes investigation root: {relative_path}") from None

        return resolved

    def with_override(self, **kwargs: Any) -> RuntimeContext:
        """
        Create new context with overridden values.

        Constitutional Basis: Article 9 (Immutable Observations)
        Original context remains unchanged.
        """
        # Get current fields
        current_fields = {
            "investigation_root": self.investigation_root,
            "constitution_hash": self.constitution_hash,
            "code_version_hash": self.code_version_hash,
            "execution_mode": self.execution_mode,
            "network_enabled": self.network_enabled,
            "mutation_allowed": self.mutation_allowed,
            "runtime_imports_allowed": self.runtime_imports_allowed,
            "parameters": dict(self.parameters),
            "session_id": self.session_id,
            "start_timestamp": self.start_timestamp,
            "python_version": self.python_version,
            "platform": self.platform,
            "max_file_size_bytes": self.max_file_size_bytes,
            "max_total_observation_size_bytes": self.max_total_observation_size_bytes,
            "max_recursion_depth": self.max_recursion_depth,
            "enforcement_levels": self.enforcement_levels,
        }

        # Apply overrides
        current_fields.update(kwargs)

        # Create new context
        return RuntimeContext(**current_fields)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert context to JSON-serializable dictionary.

        Constitutional Basis: Article 9 (Immutable Observations)
        Used for embedding in evidence metadata.
        """
        return {
            "investigation_root": str(self.investigation_root),
            "resolved_investigation_root": str(self.resolved_investigation_root),
            "constitution_hash": self.constitution_hash,
            "code_version_hash": self.code_version_hash,
            "execution_mode": self.execution_mode,
            "network_enabled": self.network_enabled,
            "mutation_allowed": self.mutation_allowed,
            "runtime_imports_allowed": self.runtime_imports_allowed,
            "parameters": dict(self.parameters),
            "session_id": self.session_id_str,
            "start_timestamp": self.start_timestamp_iso,
            "python_version": {
                "major": self.python_version[0],
                "minor": self.python_version[1],
                "micro": self.python_version[2],
            },
            "platform": self.platform,
            "max_file_size_bytes": self.max_file_size_bytes,
            "max_total_observation_size_bytes": self.max_total_observation_size_bytes,
            "max_recursion_depth": self.max_recursion_depth,
            "enforcement_levels": [level.name for level in self.enforcement_levels],
            "runtime_fingerprint": self.runtime_fingerprint,
            "canonical_paths": self.canonical_paths,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuntimeContext:
        """
        Create context from dictionary.

        Constitutional Basis: Article 13 (Deterministic Operation)
        Used for deserialization and recovery.
        """
        # Convert string fields to proper types
        converted_data: dict[str, Any] = {}

        # Convert investigation_root to Path
        if "investigation_root" in data:
            converted_data["investigation_root"] = Path(str(data["investigation_root"]))

        # Convert constitution_hash
        if "constitution_hash" in data:
            converted_data["constitution_hash"] = str(data["constitution_hash"])

        # Convert code_version_hash
        if "code_version_hash" in data:
            converted_data["code_version_hash"] = str(data["code_version_hash"])

        # Convert execution_mode
        if "execution_mode" in data:
            converted_data["execution_mode"] = str(data["execution_mode"])

        # Convert enforcement flags
        for flag in ["network_enabled", "mutation_allowed", "runtime_imports_allowed"]:
            if flag in data:
                converted_data[flag] = bool(data[flag])

        # Convert parameters
        if "parameters" in data and isinstance(data["parameters"], dict):
            converted_data["parameters"] = dict(data["parameters"])

        # Convert session_id to UUID
        if "session_id" in data:
            converted_data["session_id"] = uuid.UUID(str(data["session_id"]))

        # Convert start_timestamp to datetime
        if "start_timestamp" in data:
            converted_data["start_timestamp"] = datetime.datetime.fromisoformat(
                str(data["start_timestamp"])
            )

        # Convert python_version from dict to tuple
        if "python_version" in data and isinstance(data["python_version"], dict):
            version = data["python_version"]
            converted_data["python_version"] = (
                int(version.get("major", 3)),
                int(version.get("minor", 11)),
                int(version.get("micro", 0)),
            )

        # Convert platform
        if "platform" in data:
            converted_data["platform"] = str(data["platform"])

        # Convert limits
        for limit in [
            "max_file_size_bytes",
            "max_total_observation_size_bytes",
            "max_recursion_depth",
        ]:
            if limit in data:
                converted_data[limit] = int(data[limit])

        # Convert enforcement_levels from list of strings to tuple of enums
        if "enforcement_levels" in data and isinstance(
            data["enforcement_levels"], list
        ):
            levels: tuple[EnforcementLevel, ...] = tuple(
                EnforcementLevel[level]
                if isinstance(level, str)
                else EnforcementLevel(level)
                for level in data["enforcement_levels"]
            )
            converted_data["enforcement_levels"] = levels

        return cls(**converted_data)

    def __hash__(self) -> int:
        """Make hashable for use in dictionaries and sets."""
        # Hash based on immutable fields only
        return hash(
            (
                self.resolved_investigation_root,
                self.constitution_hash,
                self.code_version_hash,
                self.execution_mode,
                self.network_enabled,
                self.mutation_allowed,
                self.runtime_imports_allowed,
                self.session_id,
                self.start_timestamp,
                self.python_version,
                self.platform,
                self.max_file_size_bytes,
                self.max_total_observation_size_bytes,
                self.max_recursion_depth,
                self.enforcement_levels,
            )
        )

    def __eq__(self, other: object) -> bool:
        """Equality comparison based on all fields."""
        if not isinstance(other, RuntimeContext):
            return False

        # Compare all dataclass fields directly to avoid hash collisions.
        for field_name in self.__dataclass_fields__:
            if getattr(self, field_name) != getattr(other, field_name):
                return False
        return True

    def __repr__(self) -> str:
        """Machine-readable representation."""
        return (
            f"RuntimeContext("
            f"root={self.resolved_investigation_root!r}, "
            f"session={self.session_id_str[:8]}, "
            f"mode={self.execution_mode}, "
            f"fingerprint={self.runtime_fingerprint[:8]}...)"
        )

    def __str__(self) -> str:
        """Human-readable representation."""
        lines = [
            "CodeMarshal Runtime Context",
            "========================",
            f"Investigation root: {self.resolved_investigation_root}",
            f"Session: {self.session_id_str}",
            f"Started: {self.start_timestamp_iso}",
            f"Mode: {self.execution_mode}",
            f"Constitution: {self.constitution_hash[:16]}...",
            f"Code version: {self.code_version_hash[:16]}...",
            f"Python: {'.'.join(map(str, self.python_version))} on {self.platform}",
            "",
            "Enforcement:",
            f"  Network: {'ENABLED' if self.network_enabled else 'DISABLED'}",
            f"  Mutation: {'ALLOWED' if self.mutation_allowed else 'FORBIDDEN'}",
            f"  Runtime imports: {'ALLOWED' if self.runtime_imports_allowed else 'FORBIDDEN'}",
            "",
            "Limits:",
            f"  Max file size: {self.max_file_size_bytes:,} bytes",
            f"  Max total observations: {self.max_total_observation_size_bytes:,} bytes",
            f"  Max recursion depth: {self.max_recursion_depth}",
            "",
            "Runtime fingerprint:",
            f"  {self.runtime_fingerprint[:32]}...",
        ]

        return "\n".join(lines)


# Global runtime context (optional convenience)
_RUNTIME_CONTEXT: RuntimeContext | None = None


def set_runtime_context(context: RuntimeContext) -> None:
    """Set the global runtime context."""
    global _RUNTIME_CONTEXT
    _RUNTIME_CONTEXT = context


def get_runtime_context() -> RuntimeContext:
    """Get the global runtime context, creating a safe default if missing."""
    global _RUNTIME_CONTEXT
    if _RUNTIME_CONTEXT is None:
        default_hash = hashlib.sha256(b"").hexdigest()
        _RUNTIME_CONTEXT = RuntimeContext(
            investigation_root=Path.cwd(),
            constitution_hash=default_hash,
            code_version_hash=default_hash,
            execution_mode="CLI",
        )
    return _RUNTIME_CONTEXT
