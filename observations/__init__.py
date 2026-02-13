"""
observations/__init__.py - Layer 1: WHAT EXISTS

Purpose:
The reality layer. Contains only immutable facts about what exists in the codebase.
No inference, no interpretation, no judgment.

Core Principle:
Observations are sensors bolted onto reality. They read what is present,
not what it means, not whether it's good, not what it should be.

Architectural Position:
This is Layer 1. It never imports from higher layers (inquiry, lens, bridge).
It provides facts for higher layers to analyze and display.
"""

from pathlib import Path
from typing import Any

# Import base types for re-export
from .eyes import (
    BoundaryDefinition,
    BoundaryObservation,
    BoundarySight,
    BoundaryType,
    CompositeObservation,
    DefinitionType,
    DirectoryTree,
    EncodingConfidence,
    EncodingObservation,
    EncodingSight,
    ErrorContext,
    ExportDefinition,
    ExportSight,
    GoExportDefinition,
    GoImportStatement,
    GoObservation,
    GoSight,
    # Base interface
    Eye,
    # Type re-exports
    FileMetadata,
    # Concrete eye classes
    FileSight,
    ImportObservation,
    ImportSight,
    ImportStatement,
    JSImportExportObservation,
    JSImportStatement,
    JSExportStatement,
    JavaClassDefinition,
    JavaImportStatement,
    JavaObservation,
    JavaSight,
    JavaScriptSight,
    LanguageDetection,
    LanguageDetector,
    LineEndingType,
    ModuleExports,
    ObservationError,
    ObservationResult,
    TraversalConfig,
    Visibility,
    get_capabilities,
    # Common functions
    get_eye,
    list_eyes,
    observe_comprehensive,
    observe_python_directory,
    observe_python_file,
    observe_with,
    validate_all_eyes,
    validate_eye_purity,
)

# Import the eyes registry
from .eyes import registry as eyes_registry

# Import input validation utilities
from .input_validation import (
    is_safe_to_observe,
    validate_binary_file,
    validate_filesystem_access,
    validate_size_limits,
)

# Import limitations submodule
from .limitations import (
    Limitation as DeclaredLimitation,
)
from .limitations import (
    LimitationDoc as DocumentedLimitation,
)
from .limitations import (
    LimitationValidationError as ValidationRule,
)
from .limitations import (
    get_limitations_for_eye,
    validate_observation_scope,
)

# Import record submodule components
from .record import (
    Anchor,
    IntegrityRoot,
    Snapshot,
    SnapshotVersion,
    create_snapshot,
    load_snapshot,
    validate_snapshot,
)


class ObservationSystem:
    """
    Primary interface for the observation layer.

    Provides type-safe, validated access to all observation capabilities
    while enforcing purity constraints.
    """

    def __init__(self):
        """Initialize the observation system."""
        self.registry = eyes_registry
        self._cache: dict[str, Any] = {}

    def observe(
        self, target: str | Path, eye_name: str | None = None, **kwargs: Any
    ) -> ObservationResult:
        """
        Observe a target with a specific eye.

        Args:
            target: Path to observe (file or directory)
            eye_name: Name of the eye to use (None for auto-selection)
            **kwargs: Additional arguments for the eye

        Returns:
            ObservationResult containing observed facts

        Raises:
            FileNotFoundError: If target doesn't exist
            ValueError: If eye cannot be found or used
            PermissionError: If cannot access target
        """
        path = Path(target) if isinstance(target, str) else target

        # Validate target is safe to observe
        if not is_safe_to_observe(path):
            raise PermissionError(f"Target is not safe to observe: {path}")

        # Auto-select eye if not specified
        if eye_name is None:
            eye_name = self._select_eye_for_target(path)

        # Get the eye
        eye = self.registry.get_eye(eye_name)
        if not eye:
            available = self.registry.list_valid_eyes()
            raise ValueError(
                f"Eye '{eye_name}' not found or invalid. Available eyes: {available}"
            )

        # Validate observation scope
        validation_result = validate_observation_scope(eye_name, path)
        if not validation_result.is_valid:
            raise ValueError(
                f"Cannot observe target with {eye_name}: {validation_result.reason}"
            )

        # Perform observation
        return eye.observe(path)

    def observe_all(
        self,
        target: str | Path,
        eye_names: list[str] | None = None,
        skip_unsafe: bool = True,
    ) -> CompositeObservation:
        """
        Observe target with multiple eyes.

        Args:
            target: Path to observe
            eye_names: List of eye names to use (None for all valid eyes)
            skip_unsafe: Skip eyes that cannot safely observe this target

        Returns:
            CompositeObservation with results from all applicable eyes
        """
        path = Path(target) if isinstance(target, str) else target

        if eye_names is None:
            eye_names = self.registry.list_valid_eyes()

        # Filter out eyes that cannot safely observe this target
        if skip_unsafe:
            safe_eyes = []
            for eye_name in eye_names:
                validation = validate_observation_scope(eye_name, path)
                if validation.is_valid:
                    safe_eyes.append(eye_name)
                else:
                    # Log or handle unsafe eyes
                    pass
            eye_names = safe_eyes

        return self.registry.observe_with_all(path, eye_names)

    def create_snapshot(
        self,
        target: str | Path,
        name: str | None = None,
        description: str = "",
        include_eyes: list[str] | None = None,
        exclude_eyes: list[str] | None = None,
    ) -> Snapshot:
        """
        Create an immutable snapshot of observations.

        Args:
            target: Path to observe
            name: Optional name for the snapshot
            description: Description of what this snapshot captures
            include_eyes: Specific eyes to include (None for all)
            exclude_eyes: Eyes to exclude

        Returns:
            Snapshot containing all observations
        """
        path = Path(target) if isinstance(target, str) else target

        # Determine which eyes to use
        if include_eyes:
            eye_names = include_eyes
        else:
            eye_names = self.registry.list_valid_eyes()

        if exclude_eyes:
            eye_names = [e for e in eye_names if e not in exclude_eyes]

        # Collect observations
        composite = self.observe_all(path, eye_names, skip_unsafe=True)

        # Create snapshot
        return create_snapshot(
            composite=composite,
            name=name or f"snapshot_{path.name}",
            description=description,
        )

    def _select_eye_for_target(self, target: Path) -> str:
        """Select appropriate eye for a target based on type and content."""
        if not target.exists():
            raise FileNotFoundError(f"Target does not exist: {target}")

        # Directory
        if target.is_dir():
            # Check if directory contains Python files
            python_files = list(target.rglob("*.py"))
            if python_files:
                # Directory with Python code - suggest boundary sight
                return "boundary_sight"
            else:
                # Generic directory - use file sight
                return "file_sight"

        # File
        suffix = target.suffix.lower()

        # Python files
        if suffix == ".py":
            # For quick overview, use import sight
            return "import_sight"
        if suffix in {".js", ".jsx", ".ts", ".tsx"}:
            return "javascript_sight"
        if suffix == ".java":
            return "java_sight"
        if suffix == ".go":
            return "go_sight"

        # Text files
        text_extensions = {".txt", ".md", ".rst", ".json", ".yml", ".yaml", ".toml"}
        if suffix in text_extensions:
            return "encoding_sight"

        # Default to file sight for everything else
        return "file_sight"

    def get_available_eyes(self) -> dict[str, Any]:
        """Get all available eyes with their capabilities."""
        return self.registry.get_capabilities()

    def validate_system(self) -> dict[str, tuple[bool, list[str]]]:
        """
        Validate all components of the observation system.

        Returns:
            Dictionary with validation results for each component
        """
        results = {}

        # Validate all eyes
        eye_results = validate_all_eyes()
        all_eyes_valid = all(valid for valid, _ in eye_results.values())
        eye_errors = []
        for name, (valid, errs) in eye_results.items():
            if not valid:
                eye_errors.extend([f"{name}: {e}" for e in errs])
        results["eyes"] = (all_eyes_valid, eye_errors)

        # Validate record system
        record_valid = all(
            [Snapshot is not None, Anchor is not None, IntegrityRoot is not None]
        )
        results["record"] = (record_valid, [])

        # Validate limitations
        limitations_valid = True
        limitation_errors = []
        try:
            limitations = get_limitations_for_eye("file_sight")
            if not limitations:
                limitations_valid = False
                limitation_errors.append("No limitations defined for file_sight")
        except Exception as e:
            limitations_valid = False
            limitation_errors.append(f"Failed to get limitations: {e}")

        results["limitations"] = (limitations_valid, limitation_errors)

        return results


# Create singleton instance
_system = None


def get_system() -> ObservationSystem:
    """Get the singleton observation system instance."""
    global _system
    if _system is None:
        _system = ObservationSystem()
    return _system


# Convenience functions for common operations


def observe(
    target: str | Path, eye_name: str | None = None, **kwargs: Any
) -> ObservationResult:
    """
    Convenience function to observe a target.

    Args:
        target: Path to observe
        eye_name: Name of the eye to use
        **kwargs: Additional arguments for the eye

    Returns:
        ObservationResult
    """
    return get_system().observe(target, eye_name, **kwargs)


def snapshot(
    target: str | Path, name: str | None = None, description: str = ""
) -> Snapshot:
    """
    Create a snapshot of observations.

    Args:
        target: Path to observe
        name: Optional snapshot name
        description: Snapshot description

    Returns:
        Snapshot
    """
    return get_system().create_snapshot(target, name, description)


def validate() -> dict[str, tuple[bool, list[str]]]:
    """Validate the entire observation system."""
    return get_system().validate_system()


# Re-export commonly used types and functions
__all__ = [
    # System interface
    "ObservationSystem",
    "get_system",
    "observe",
    "snapshot",
    "validate",
    # Eyes and observation
    "Eye",
    "ObservationResult",
    "ObservationError",
    "ErrorContext",
    "CompositeObservation",
    "validate_eye_purity",
    "FileSight",
    "ImportSight",
    "ExportSight",
    "BoundarySight",
    "EncodingSight",
    "JavaScriptSight",
    "JavaSight",
    "GoSight",
    "get_eye",
    "list_eyes",
    "get_capabilities",
    "observe_with",
    "observe_comprehensive",
    "observe_python_file",
    "observe_python_directory",
    # Record system
    "Snapshot",
    "Anchor",
    "SnapshotVersion",
    "IntegrityRoot",
    "create_snapshot",
    "load_snapshot",
    "validate_snapshot",
    # Limitations
    "DeclaredLimitation",
    "DocumentedLimitation",
    "ValidationRule",
    "get_limitations_for_eye",
    "validate_observation_scope",
    # Input validation
    "validate_filesystem_access",
    "validate_binary_file",
    "validate_size_limits",
    "is_safe_to_observe",
    # Data types for type hints
    "FileMetadata",
    "DirectoryTree",
    "TraversalConfig",
    "ImportStatement",
    "ImportObservation",
    "ModuleExports",
    "ExportDefinition",
    "Visibility",
    "DefinitionType",
    "JSImportStatement",
    "JSExportStatement",
    "JSImportExportObservation",
    "JavaImportStatement",
    "JavaClassDefinition",
    "JavaObservation",
    "GoImportStatement",
    "GoExportDefinition",
    "GoObservation",
    "LanguageDetector",
    "LanguageDetection",
    "BoundaryObservation",
    "BoundaryDefinition",
    "BoundaryType",
    "EncodingObservation",
    "EncodingConfidence",
    "LineEndingType",
]


# System initialization and self-test
def _initialize() -> None:
    """Initialize the observation system and run basic checks."""
    import warnings

    system = get_system()

    # Run validation
    validation_results = system.validate_system()

    # Check for critical failures
    critical_failures = []
    for component, (is_valid, errors) in validation_results.items():
        if not is_valid:
            critical_failures.append(f"{component}: {errors}")

    if critical_failures:
        warning_msg = (
            f"Observation system has validation issues:\n"
            f"{chr(10).join(critical_failures)}"
        )

        # Don't raise exception - system should still work partially
        import warnings

        warnings.warn(warning_msg, RuntimeWarning, stacklevel=2)

    # Test that we can at least list eyes
    try:
        eyes = system.get_available_eyes()
        if not eyes:
            warnings.warn("No observation eyes available", RuntimeWarning, stacklevel=2)
    except Exception as e:
        warnings.warn(
            f"Failed to get available eyes: {e}", RuntimeWarning, stacklevel=2
        )


# Run initialization
if __name__ != "__main__":
    _initialize()


# Test the system
if __name__ == "__main__":
    print("=== Observation System Test ===\n")

    import tempfile

    # Initialize system
    system = get_system()

    # Test validation
    print("1. System Validation:")
    validation = system.validate_system()
    for component, (is_valid, errors) in validation.items():
        status = "✓" if is_valid else "✗"
        print(f"   {status} {component}")
        if errors:
            for error in errors:
                print(f"      - {error}")

    # Test available eyes
    print("\n2. Available Eyes:")
    eyes = system.get_available_eyes()
    for name, capability in eyes.items():
        print(f"   {name}: {capability.description}")

    # Test observation
    print("\n3. Test Observation:")
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(b'''
"""Test file for observation system."""
import os
from pathlib import Path

class TestClass:
    """Test class for observation."""

    def test_method(self) -> str:
        return "test"
''')
        test_file = Path(f.name)

    try:
        # Test single observation
        result = system.observe(test_file, "import_sight")
        print(f"   File: {test_file}")
        print("   Eye: import_sight")
        print(f"   Success: {result.is_successful}")
        print(f"   Confidence: {result.confidence:.2f}")

        # Test snapshot
        print("\n4. Test Snapshot:")
        snapshot = system.create_snapshot(
            test_file,
            name="test_snapshot",
            description="Test snapshot of a Python file",
        )
        print(f"   Snapshot ID: {snapshot.id}")
        print(f"   Observations: {len(snapshot.observations.observations)}")
        print(f"   Timestamp: {snapshot.created_at}")

        # Test validation
        print("\n5. Test Validation:")
        is_valid, errors = validate_snapshot(snapshot)
        print(f"   Valid: {is_valid}")
        if errors:
            for error in errors:
                print(f"      - {error}")

    finally:
        test_file.unlink()

    print("\n=== Test Complete ===")
