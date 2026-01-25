"""
base.py - Observation Interface Contract

Purpose:
Defines what it means to "see" in the CodeMarshal system. This is the load-bearing
wall of Layer 1 (Observations). Every eye must adhere to this contract.

Core Principles:
1. Observations are immutable facts
2. Observations are side-effect free
3. Observations are reproducible
4. Observations carry provenance (source, timestamp, confidence)
"""

import abc
import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any,
    Generic,
    Protocol,
    TypeVar,
    runtime_checkable,
)


def _make_immutable(obj: Any) -> Any:
    """Recursively convert mutable objects to immutable equivalents."""
    if isinstance(obj, dict):
        return frozenset((k, _make_immutable(v)) for k, v in obj.items())
    if isinstance(obj, (list, set, tuple)):
        return tuple(_make_immutable(i) for i in obj)
    return obj


def _to_mutable(obj: Any) -> Any:
    """Recursively convert immutable objects back to mutable equivalents."""
    if isinstance(obj, frozenset):
        return {k: _to_mutable(v) for k, v in obj}
    if isinstance(obj, tuple):
        return [_to_mutable(i) for i in obj]
    return obj


class ObservationError(Enum):
    """Classification of observation errors."""

    PERMISSION_DENIED = auto()
    FILE_NOT_FOUND = auto()
    INVALID_FORMAT = auto()
    SIZE_LIMIT_EXCEEDED = auto()
    PARSING_ERROR = auto()
    UNKNOWN_ENCODING = auto()
    INTERNAL_ERROR = auto()

    @property
    def description(self) -> str:
        """Human-readable error description."""
        descriptions = {
            self.PERMISSION_DENIED: "Cannot access due to permissions",
            self.FILE_NOT_FOUND: "File or directory does not exist",
            self.INVALID_FORMAT: "File format is invalid or corrupted",
            self.SIZE_LIMIT_EXCEEDED: "File exceeds size limit for observation",
            self.PARSING_ERROR: "Cannot parse content due to syntax errors",
            self.UNKNOWN_ENCODING: "Cannot determine file encoding",
            self.INTERNAL_ERROR: "Internal error during observation",
        }
        return descriptions.get(self, "Unknown error")


@dataclass(frozen=True)
class ErrorContext:
    """Immutable context for observation errors."""

    error_type: ObservationError
    message: str
    file_path: Path | None = None
    line_number: int | None = None
    column_number: int | None = None
    additional_info: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure all fields are immutable."""
        # Convert dictionary to frozenset for hashability
        if isinstance(self.additional_info, dict):
            # We use object.__setattr__ because the dataclass is frozen
            object.__setattr__(
                self, "additional_info", _make_immutable(self.additional_info)
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_type": self.error_type.name,
            "message": self.message,
            "file_path": str(self.file_path) if self.file_path else None,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "additional_info": _to_mutable(self.additional_info),
        }


@dataclass(frozen=True)
class Provenance:
    """Immutable provenance information for an observation."""

    observer_name: str
    observer_version: str
    observation_timestamp: datetime
    observation_duration_ms: int = 0
    input_hash: str | None = None  # Hash of input for reproducibility
    environment_fingerprint: str | None = None  # Hash of relevant environment

    @property
    def signature(self) -> str:
        """Unique signature for this observation provenance."""
        components = [
            self.observer_name,
            self.observer_version,
            self.observation_timestamp.isoformat(),
            str(self.observation_duration_ms),
            self.input_hash or "",
            self.environment_fingerprint or "",
        ]
        return hashlib.sha256("|".join(components).encode()).hexdigest()[:16]


# Type alias for cleaner type hints
T = TypeVar("T", covariant=True)


@dataclass(frozen=True)
class ObservationResult(Generic[T]):
    """
    Immutable container for observation results.

    Type parameter T is the type of the raw_payload (the actual observation data).
    """

    source: str  # What was observed (e.g., file path, directory, URL)
    timestamp: datetime
    version: str  # Version of the eye that made this observation
    confidence: float  # 0.0 to 1.0, where 1.0 is certain

    # The actual observation data (must be immutable)
    raw_payload: Any

    # Provenance and metadata
    provenance: Provenance | None = None
    errors: tuple[ErrorContext, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    # Performance metrics
    memory_usage_bytes: int | None = None
    cpu_time_ms: int | None = None

    def __post_init__(self) -> None:
        """Validate invariants."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )

        if self.timestamp.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware")

        # Ensure all fields are immutable
        if not isinstance(self.raw_payload, (str, int, float, bool, type(None), Enum)):
            # We use object.__setattr__ because the dataclass is frozen
            object.__setattr__(self, "raw_payload", _make_immutable(self.raw_payload))

        # Ensure all fields are hashable (for immutability)
        self._validate_hashable()

    def _validate_hashable(self) -> None:
        """Ensure all fields are hashable for immutability."""
        for field_name, field_value in self.__dict__.items():
            try:
                hash(field_value)
            except TypeError as e:
                raise TypeError(
                    f"Field '{field_name}' with type {type(field_value)} is not hashable. "
                    f"All observation result fields must be immutable."
                ) from e

    @property
    def is_successful(self) -> bool:
        """Whether observation completed without errors."""
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """Whether observation has warnings."""
        return len(self.warnings) > 0

    def with_additional_context(self, **kwargs: Any) -> "ObservationResult[Any]":
        """
        Create a new observation result with additional context.

        Returns a new ObservationResult with the same data plus additional context.
        """
        current = self.__dict__.copy()

        # Only update allowed fields
        allowed_updates = {
            "provenance",
            "errors",
            "warnings",
            "memory_usage_bytes",
            "cpu_time_ms",
        }

        for key, value in kwargs.items():
            if key in allowed_updates:
                if key == "errors" and isinstance(value, list):
                    current[key] = tuple(value)
                elif key == "warnings" and isinstance(value, list):
                    current[key] = tuple(value)
                else:
                    current[key] = value

        return ObservationResult(**current)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "confidence": self.confidence,
            "is_successful": self.is_successful,
            "has_warnings": self.has_warnings,
            "raw_payload": _to_mutable(self.raw_payload),
        }

        if self.provenance:
            result["provenance"] = {
                "observer_name": self.provenance.observer_name,
                "observer_version": self.provenance.observer_version,
                "observation_timestamp": self.provenance.observation_timestamp.isoformat(),
                "signature": self.provenance.signature,
            }

        if self.errors:
            result["errors"] = [error.to_dict() for error in self.errors]

        if self.warnings:
            result["warnings"] = list(self.warnings)

        if self.memory_usage_bytes is not None:
            result["memory_usage_bytes"] = self.memory_usage_bytes

        if self.cpu_time_ms is not None:
            result["cpu_time_ms"] = self.cpu_time_ms

        return result

    def to_json(self, indent: int | None = None) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


@runtime_checkable
class Eye(Protocol):
    """
    Protocol defining the interface for all observation eyes.

    An "Eye" is a sensor that observes one dimension of reality.
    All eyes must implement this protocol.
    """

    @property
    def name(self) -> str:
        """Unique name of this eye."""
        ...

    @property
    def version(self) -> str:
        """Version of this eye."""
        ...

    def observe(self, target: Path) -> ObservationResult:
        """
        Observe the target and return immutable facts.

        Args:
            target: Path to observe (file or directory)

        Returns:
            ObservationResult containing observed facts

        Raises:
            FileNotFoundError: If target doesn't exist
            PermissionError: If cannot access target
            ValueError: If target is invalid for this eye
        """
        ...

    def validate(self) -> bool:
        """
        Validate that this eye follows observation purity rules.

        Returns:
            True if eye passes validation, False otherwise

        Note:
            This is a runtime check for production safety.
            Eyes should implement specific checks for their domain.
        """
        ...

    def get_capabilities(self) -> dict[str, Any]:
        """
        Get metadata about what this eye can observe.

        Returns:
            Dictionary describing eye capabilities
        """
        ...


class AbstractEye(abc.ABC):
    """
    Abstract base class implementing the Eye protocol with common functionality.

    Concrete eyes should inherit from this class.
    """

    def __init__(self, name: str | None = None, version: str | None = None):
        """
        Initialize the eye.

        Args:
            name: Name of the eye (defaults to class name)
            version: Version of the eye (defaults to "1.0.0")
        """
        self._name = name or self.__class__.__name__.lower()
        self._version = version or "1.0.0"

    @property
    def name(self) -> str:
        """Unique name of this eye."""
        return self._name

    @property
    def version(self) -> str:
        """Version of this eye."""
        return self._version

    @abc.abstractmethod
    def observe(self, target: Path) -> ObservationResult:
        """
        Observe the target and return immutable facts.

        Must be implemented by concrete eyes.
        """
        pass

    def validate(self) -> bool:
        """
        Default validation: checks for common purity violations.

        Concrete eyes should override this with domain-specific checks.
        """
        # Import validation: ensure no prohibited imports
        import inspect

        # Get the concrete eye class
        eye_class = self.__class__

        # Check for prohibited module imports in the source
        try:
            source_file = Path(inspect.getfile(eye_class)).resolve()

            # Basic check for obvious violations
            # We mangle strings to avoid literal matches during self-validation
            prohibited_patterns = [
                "sub" + "process",
                "ex" + "ec(",
                "ev" + "al(",
                "com" + "pile(",
                "os.sys" + "tem",
                "os.po" + "pen",
                "open(" + '"w")',
                "open(" + '"a")',
                ".wri" + "te(",
                ".write" + "lines(",
            ]

            with open(source_file, encoding="utf-8") as f:
                content = f.read()

            for pattern in prohibited_patterns:
                if pattern in content:
                    return False

            # Check that all imports are allowed
            # This is a simplified check - in production you'd parse the AST

            # For now, return True if basic checks pass
            # Concrete eyes should implement more thorough validation

            return True

        except Exception:
            # If we can't validate, assume invalid for safety
            return False

    def get_capabilities(self) -> dict[str, Any]:
        """
        Get metadata about what this eye can observe.

        Default implementation returns basic info. Override for specific capabilities.
        """
        return {
            "name": self.name,
            "version": self.version,
            "class": self.__class__.__name__,
            "description": self.__doc__ or "No description provided",
            "input_types": ["Path"],
            "output_type": "ObservationResult",
            "deterministic": True,
            "side_effect_free": True,
        }

    def _create_provenance(
        self, target: Path, observation_time: datetime, duration_ms: int = 0
    ) -> Provenance:
        """Create provenance information for an observation."""
        # Create input hash
        try:
            if target.is_file():
                # Hash file content
                content = target.read_bytes()
                input_hash = hashlib.sha256(content).hexdigest()
            elif target.is_dir():
                # Hash directory structure (simplified)
                dir_info = f"{target.resolve()}|{target.stat().st_mtime}"
                input_hash = hashlib.sha256(dir_info.encode()).hexdigest()
            else:
                input_hash = None
        except OSError:
            input_hash = None

        # Create environment fingerprint
        import platform
        import sys

        env_info = f"{platform.python_version()}|{sys.platform}|{platform.machine()}"
        env_hash = hashlib.sha256(env_info.encode()).hexdigest()

        return Provenance(
            observer_name=self.name,
            observer_version=self.version,
            observation_timestamp=observation_time,
            observation_duration_ms=duration_ms,
            input_hash=input_hash,
            environment_fingerprint=env_hash,
        )

    def _observe_with_timing(self, target: Path) -> ObservationResult:
        """
        Wrapper around observe() that adds timing and provenance.

        Concrete eyes should call this from their observe() method.
        """
        import time

        start_time = time.perf_counter()
        timestamp = datetime.now(UTC)

        try:
            # Perform the actual observation
            result = self._observe_impl(target)

            # Calculate duration
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            # Add provenance
            provenance = self._create_provenance(target, timestamp, duration_ms)

            return result.with_additional_context(
                provenance=provenance,
                cpu_time_ms=duration_ms,
            )

        except Exception as e:
            # Create error result
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            return ObservationResult(
                source=str(target),
                timestamp=timestamp,
                version=self.version,
                confidence=0.0,
                raw_payload=None,
                provenance=self._create_provenance(target, timestamp, duration_ms),
                errors=(
                    ErrorContext(
                        error_type=ObservationError.INTERNAL_ERROR,
                        message=f"Observation failed: {str(e)}",
                        file_path=target,
                    ),
                ),
                cpu_time_ms=duration_ms,
            )

    @abc.abstractmethod
    def _observe_impl(self, target: Path) -> ObservationResult:
        """
        Internal implementation of observation.

        Concrete eyes must implement this. It should return a complete
        ObservationResult without provenance (which will be added by wrapper).
        """
        pass


# Type alias for cleaner type hints
T = TypeVar("T", covariant=True)


@dataclass(frozen=True)
class CompositeObservation:
    """
    Container for multiple observations from different eyes.

    Useful for observing the same target with multiple eyes.
    """

    target: Path
    timestamp: datetime
    observations: tuple[ObservationResult, ...] = field(default_factory=tuple)

    @property
    def successful_observations(self) -> tuple[ObservationResult, ...]:
        """Get only successful observations."""
        return tuple(obs for obs in self.observations if obs.is_successful)

    @property
    def confidence_score(self) -> float:
        """Overall confidence score (average of successful observations)."""
        successful = self.successful_observations
        if not successful:
            return 0.0
        return sum(obs.confidence for obs in successful) / len(successful)

    def get_observations_by_eye(self, eye_name: str) -> tuple[ObservationResult, ...]:
        """Get observations from a specific eye."""
        return tuple(
            obs
            for obs in self.observations
            if obs.provenance and obs.provenance.observer_name == eye_name
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "target": str(self.target),
            "timestamp": self.timestamp.isoformat(),
            "observation_count": len(self.observations),
            "successful_count": len(self.successful_observations),
            "overall_confidence": self.confidence_score,
            "observations": [obs.to_dict() for obs in self.observations],
        }


# Validation utilities


def validate_eye_purity(eye: Eye) -> tuple[bool, list[str]]:
    """
    Comprehensive purity validation for an eye.

    Returns:
        Tuple of (is_valid, list_of_violations)
    """
    violations: list[str] = []

    # 1. Check name and version
    if not eye.name or not isinstance(eye.name, str):
        violations.append("Eye must have a non-empty string name")

    if not eye.version or not isinstance(eye.version, str):
        violations.append("Eye must have a non-empty string version")

    # 2. Check capabilities
    try:
        caps = eye.get_capabilities()
        if not caps.get("deterministic", False):
            violations.append("Eye must be deterministic")
        if not caps.get("side_effect_free", False):
            violations.append("Eye must be side-effect free")
    except Exception as e:
        violations.append(f"Failed to get capabilities: {str(e)}")

    # 3. Run eye's own validation
    try:
        if not eye.validate():
            violations.append("Eye's own validation failed")
    except Exception as e:
        violations.append(f"Eye validation raised exception: {str(e)}")

    # 4. Test with a dummy file (if possible)
    try:
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test content")
            test_file = Path(f.name)

        try:
            result = eye.observe(test_file)

            # Check result invariants
            if not 0.0 <= result.confidence <= 1.0:
                violations.append(f"Confidence {result.confidence} outside [0,1]")

            if result.timestamp.tzinfo is None:
                violations.append("Timestamp must be timezone-aware")

            # Ensure result is immutable
            try:
                hash(result)
            except TypeError:
                violations.append("ObservationResult must be hashable (immutable)")

        except Exception as e:
            violations.append(f"Observation raised exception: {str(e)}")
        finally:
            test_file.unlink()

    except Exception as e:
        violations.append(f"Could not run test observation: {str(e)}")

    return len(violations) == 0, violations


# Example concrete eye for testing


class TestEye(AbstractEye):
    """
    Example eye for testing the base interface.

    Observes basic file properties without interpretation.
    """

    def __init__(self):
        super().__init__(name="test_eye", version="1.0.0")

    def observe(self, target: Path) -> ObservationResult:
        """Public interface that adds timing and provenance."""
        return self._observe_with_timing(target)

    def _observe_impl(self, target: Path) -> ObservationResult:
        """Internal observation implementation."""
        timestamp = datetime.now(UTC)

        if not target.exists():
            return ObservationResult(
                source=str(target),
                timestamp=timestamp,
                version=self.version,
                confidence=0.0,
                raw_payload=None,
                errors=(
                    ErrorContext(
                        error_type=ObservationError.FILE_NOT_FOUND,
                        message=f"File does not exist: {target}",
                        file_path=target,
                    ),
                ),
            )

        try:
            # Basic file properties
            stats = target.stat()

            observation_data = {
                "exists": True,
                "is_file": target.is_file(),
                "is_dir": target.is_dir(),
                "size_bytes": stats.st_size,
                "modified_time": datetime.fromtimestamp(
                    stats.st_mtime, tz=UTC
                ).isoformat(),
                "access_time": datetime.fromtimestamp(
                    stats.st_atime, tz=UTC
                ).isoformat(),
            }

            return ObservationResult(
                source=str(target),
                timestamp=timestamp,
                version=self.version,
                confidence=1.0,
                raw_payload=observation_data,
            )

        except PermissionError as e:
            return ObservationResult(
                source=str(target),
                timestamp=timestamp,
                version=self.version,
                confidence=0.0,
                raw_payload=None,
                errors=(
                    ErrorContext(
                        error_type=ObservationError.PERMISSION_DENIED,
                        message=f"Permission denied: {str(e)}",
                        file_path=target,
                    ),
                ),
            )
        except Exception as e:
            return ObservationResult(
                source=str(target),
                timestamp=timestamp,
                version=self.version,
                confidence=0.0,
                raw_payload=None,
                errors=(
                    ErrorContext(
                        error_type=ObservationError.INTERNAL_ERROR,
                        message=f"Unexpected error: {str(e)}",
                        file_path=target,
                    ),
                ),
            )
