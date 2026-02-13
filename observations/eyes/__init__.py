"""
eyes/__init__.py - Observation Sensors Registry

Purpose:
Central registry and management of all observation eyes. Provides a clean,
type-safe API for discovering, loading, and using eyes while maintaining
strict purity constraints.

Core Principles:
1. Eyes are registered, not dynamically discovered (deterministic)
2. All eyes must pass purity validation before use
3. Registry is immutable after initialization
4. No side effects in registry operations
"""

import inspect
import warnings
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

# Import base interface
from .base import (
    CompositeObservation,
    ErrorContext,
    Eye,
    ObservationError,
    ObservationResult,
    validate_eye_purity,
)
from .boundary_sight import (
    BoundaryDefinition,
    BoundaryObservation,
    BoundarySight,
    BoundaryType,
    create_layer_boundary,
    create_package_boundary,
    observe_boundaries,
)
from .encoding_sight import (
    EncodingConfidence,
    EncodingObservation,
    EncodingSight,
    LineEndingType,
    check_line_endings,
    detect_encoding,
)
from .export_sight import (
    DefinitionType,
    ExportDefinition,
    ExportSight,
    ModuleExports,
    Visibility,
    observe_exports,
)
from .go_sight import (
    GoExportDefinition,
    GoImportStatement,
    GoObservation,
    GoSight,
)
from .java_sight import (
    JavaClassDefinition,
    JavaImportStatement,
    JavaObservation,
    JavaSight,
)
from .javascript_sight import (
    JSImportExportObservation,
    JSImportStatement,
    JSExportStatement,
    JavaScriptSight,
)
from .language_detector import LanguageDetection, LanguageDetector

# Import all concrete eyes
from .file_sight import (
    DirectoryTree,
    FileMetadata,
    FileSight,
    TraversalConfig,
    observe_directory,
    observe_file,
)
from .import_sight import (
    ImportObservation,
    ImportSight,
    ImportStatement,
    observe_imports,
)


@dataclass(frozen=True)
class EyeCapability:
    """Immutable description of what an eye can observe."""

    name: str
    description: str
    input_types: tuple[str, ...]
    output_type: str
    deterministic: bool
    side_effect_free: bool
    version: str
    configurable: bool = False

    @property
    def signature(self) -> str:
        """Unique signature for this capability."""
        components = [
            self.name,
            self.version,
            ",".join(sorted(self.input_types)),
            self.output_type,
            str(self.deterministic),
            str(self.side_effect_free),
        ]
        return "|".join(components)


@dataclass
class RegisteredEye:
    """Registry entry for an eye (mutable to allow lazy instantiation)."""

    eye_class: type[Eye]
    instance: Eye | None = None
    validated: bool = False
    validation_errors: tuple[str, ...] = field(default_factory=tuple)

    @property
    def name(self) -> str:
        """Get the eye's name."""
        if self.instance:
            return self.instance.name
        # Try to get name from class
        try:
            temp_instance = self.eye_class()
            return temp_instance.name
        except Exception:
            return self.eye_class.__name__.lower()

    @property
    def version(self) -> str:
        """Get the eye's version."""
        if self.instance:
            return self.instance.version
        return "1.0.0"  # Default

    def get_or_create_instance(self) -> Eye:
        """Get or create an instance of this eye."""
        if self.instance is None:
            self.instance = self.eye_class()
        return self.instance

    def get_capability(self) -> EyeCapability:
        """Get capability description for this eye."""
        instance = self.get_or_create_instance()
        caps = instance.get_capabilities()

        return EyeCapability(
            name=caps.get("name", self.name),
            description=caps.get("description", "No description"),
            input_types=tuple(caps.get("input_types", ["Path"])),
            output_type=caps.get("output_type", "ObservationResult"),
            deterministic=caps.get("deterministic", True),
            side_effect_free=caps.get("side_effect_free", True),
            version=caps.get("version", self.version),
            configurable=caps.get("configurable", False),
        )


class EyeRegistry:
    """
    Central registry for all observation eyes.

    This is a singleton that maintains a registry of available eyes.
    All eyes must pass purity validation before being registered.
    """

    _instance: Optional["EyeRegistry"] = None
    _registry: dict[str, RegisteredEye] = {}
    _initialized: bool = False

    def __new__(cls) -> "EyeRegistry":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize registry with built-in eyes."""
        if not self._initialized:
            self._registry = {}
            self._register_builtin_eyes()
            self._initialized = True

    def _register_builtin_eyes(self) -> None:
        """Register all built-in eyes with validation."""
        builtin_eyes: list[tuple[type[Eye], str]] = [
            (FileSight, "file_sight"),
            (ImportSight, "import_sight"),
            (ExportSight, "export_sight"),
            (BoundarySight, "boundary_sight"),
            (EncodingSight, "encoding_sight"),
            (JavaScriptSight, "javascript_sight"),
            (JavaSight, "java_sight"),
            (GoSight, "go_sight"),
        ]

        for eye_class, name in builtin_eyes:
            self.register_eye(eye_class, name)

    def register_eye(self, eye_class: type[Eye], name: str | None = None) -> bool:
        """
        Register a new eye after validation.

        Args:
            eye_class: The Eye class to register
            name: Optional custom name (defaults to class name)

        Returns:
            True if registration successful, False otherwise
        """
        if not inspect.isclass(eye_class):
            raise TypeError(f"Expected class, got {type(eye_class)}")

        # Create instance for validation
        try:
            instance = eye_class()
        except Exception as e:
            warnings.warn(f"Cannot instantiate {eye_class.__name__}: {e}", stacklevel=2)
            return False

        eye_name = name or instance.name

        # Check for duplicates
        if eye_name in self._registry:
            warnings.warn(f"Eye '{eye_name}' already registered", stacklevel=2)
            return False

        # Validate purity
        is_valid, violations = validate_eye_purity(instance)

        # Create registry entry
        entry = RegisteredEye(
            eye_class=eye_class,
            instance=instance,
            validated=is_valid,
            validation_errors=tuple(violations),
        )

        # Register
        self._registry[eye_name] = entry

        return is_valid

    def get_eye(self, name: str) -> Eye | None:
        """
        Get an eye instance by name.

        Args:
            name: Name of the eye

        Returns:
            Eye instance if found and valid, None otherwise
        """
        entry = self._registry.get(name)
        if not entry:
            return None

        # Only return if validated
        if not entry.validated:
            warnings.warn(f"Eye '{name}' failed purity validation", stacklevel=2)
            return None

        return entry.get_or_create_instance()

    def get_eye_class(self, name: str) -> type[Eye] | None:
        """Get eye class by name."""
        entry = self._registry.get(name)
        return entry.eye_class if entry else None

    def list_eyes(self) -> list[str]:
        """Get list of all registered eye names."""
        return sorted(self._registry.keys())

    def list_valid_eyes(self) -> list[str]:
        """Get list of eye names that passed validation."""
        return [name for name, entry in self._registry.items() if entry.validated]

    def get_capabilities(self) -> dict[str, EyeCapability]:
        """Get capabilities of all valid eyes."""
        return {
            name: entry.get_capability()
            for name, entry in self._registry.items()
            if entry.validated
        }

    def get_validation_status(self, name: str) -> tuple[bool, tuple[str, ...]]:
        """Get validation status for an eye."""
        entry = self._registry.get(name)
        if not entry:
            return False, ("Eye not registered",)
        return entry.validated, entry.validation_errors

    def observe_with_all(
        self, target: Path, eye_names: list[str] | None = None
    ) -> CompositeObservation:
        """
        Observe target with all (or specified) valid eyes.

        Args:
            target: Path to observe
            eye_names: Optional list of specific eyes to use

        Returns:
            CompositeObservation containing results from all eyes
        """
        if eye_names is None:
            eye_names = self.list_valid_eyes()

        observations: list[ObservationResult] = []
        timestamp = datetime.now(UTC)

        for name in eye_names:
            eye = self.get_eye(name)
            if eye:
                try:
                    result = eye.observe(target)
                    observations.append(result)
                except Exception as e:
                    # Create error observation
                    error_result = ObservationResult(
                        source=str(target),
                        timestamp=timestamp,
                        version="0.0.0",
                        confidence=0.0,
                        raw_payload=None,
                        errors=(
                            ErrorContext(
                                error_type=ObservationError.INTERNAL_ERROR,
                                message=f"Eye '{name}' failed: {str(e)}",
                                file_path=target,
                            ),
                        ),
                    )
                    observations.append(error_result)

        return CompositeObservation(
            target=target, timestamp=timestamp, observations=tuple(observations)
        )


# Singleton instance
registry = EyeRegistry()


def get_eye(name: str) -> Eye | None:
    """Get an eye instance by name (convenience function)."""
    return registry.get_eye(name)


def list_eyes() -> list[str]:
    """List all registered eyes (convenience function)."""
    return registry.list_eyes()


def get_capabilities() -> dict[str, EyeCapability]:
    """Get capabilities of all valid eyes (convenience function)."""
    return registry.get_capabilities()


def observe_with(
    target: str | Path, eye_name: str, **kwargs: Any
) -> ObservationResult | None:
    """
    Observe target with a specific eye.

    Args:
        target: Path to observe
        eye_name: Name of the eye to use
        **kwargs: Additional arguments to pass to eye constructor

    Returns:
        ObservationResult if successful, None otherwise
    """
    path = Path(target) if isinstance(target, str) else target

    eye_class = registry.get_eye_class(eye_name)
    if not eye_class:
        return None

    try:
        # Create eye instance with kwargs if provided
        if kwargs:
            eye = eye_class(**kwargs)
            # Validate the instance
            is_valid, _ = validate_eye_purity(eye)
            if not is_valid:
                return None
        else:
            eye = registry.get_eye(eye_name)
            if not eye:
                return None

        return eye.observe(path)

    except Exception as e:
        warnings.warn(f"Observation failed with {eye_name}: {e}", stacklevel=2)
        return None


def observe_comprehensive(
    target: str | Path, eye_names: list[str] | None = None
) -> CompositeObservation:
    """
    Observe target with multiple eyes.

    Args:
        target: Path to observe
        eye_names: Optional list of specific eyes to use

    Returns:
        CompositeObservation with results from all eyes
    """
    path = Path(target) if isinstance(target, str) else target
    return registry.observe_with_all(path, eye_names)


def validate_all_eyes() -> dict[str, tuple[bool, list[str]]]:
    """
    Validate all registered eyes and return results.

    Returns:
        Dictionary mapping eye names to (is_valid, violations)
    """
    results: dict[str, tuple[bool, list[str]]] = {}

    for name in registry.list_eyes():
        is_valid, violations = registry.get_validation_status(name)
        results[name] = (is_valid, list(violations))

    return results


def get_eye_for_file_type(file_path: Path) -> list[str]:
    """
    Suggest appropriate eyes for a given file type.

    Args:
        file_path: Path to file

    Returns:
        List of suggested eye names
    """
    suggestions: list[str] = []

    if not file_path.exists():
        return suggestions

    # File extension-based suggestions
    ext = file_path.suffix.lower()

    if ext == ".py":
        suggestions.extend(["import_sight", "export_sight", "encoding_sight"])
    elif ext in {".js", ".jsx", ".ts", ".tsx"}:
        suggestions.extend(["javascript_sight", "encoding_sight"])
    elif ext == ".java":
        suggestions.extend(["java_sight", "encoding_sight"])
    elif ext == ".go":
        suggestions.extend(["go_sight", "encoding_sight"])

    # Always include file_sight for basic metadata
    suggestions.append("file_sight")

    # For directories, include boundary_sight
    if file_path.is_dir():
        suggestions.append("boundary_sight")

    # Remove duplicates while preserving order
    seen: set[str] = set()
    unique_suggestions: list[str] = []
    for eye in suggestions:
        if eye not in seen:
            seen.add(eye)
            unique_suggestions.append(eye)

    return unique_suggestions


# Convenience functions for common operations


def observe_python_file(file_path: str | Path) -> CompositeObservation:
    """
    Comprehensive observation of a Python file.

    Uses: file_sight, import_sight, export_sight, encoding_sight
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path
    eyes = ["file_sight", "import_sight", "export_sight", "encoding_sight"]
    return observe_comprehensive(path, eyes)


def observe_python_directory(dir_path: str | Path) -> CompositeObservation:
    """
    Comprehensive observation of a Python directory.

    Uses: file_sight, boundary_sight (if boundaries defined)
    """
    path = Path(dir_path) if isinstance(dir_path, str) else dir_path
    eyes = ["file_sight"]

    # Only include boundary_sight if we're looking at a directory with Python files
    if path.is_dir():
        # Check if there are Python files
        python_files = list(path.rglob("*.py"))
        if python_files:
            eyes.append("boundary_sight")

    return observe_comprehensive(path, eyes)


def export_observations_to_dict(composite: CompositeObservation) -> dict[str, Any]:
    """
    Export composite observations to a serializable dictionary.

    Args:
        composite: CompositeObservation to export

    Returns:
        Dictionary suitable for JSON serialization
    """
    return composite.to_dict()


# Re-export commonly used functions and classes for convenience
__all__ = [
    # Registry functions
    "get_eye",
    "list_eyes",
    "get_capabilities",
    "observe_with",
    "observe_comprehensive",
    "validate_all_eyes",
    "get_eye_for_file_type",
    "observe_python_file",
    "observe_python_directory",
    "export_observations_to_dict",
    # Concrete eye classes
    "FileSight",
    "ImportSight",
    "ExportSight",
    "BoundarySight",
    "EncodingSight",
    "JavaScriptSight",
    "JavaSight",
    "GoSight",
    # Base classes and types
    "Eye",
    "ObservationResult",
    "ObservationError",
    "ErrorContext",
    "CompositeObservation",
    "validate_eye_purity",
    # Convenience functions from eyes
    "observe_file",
    "observe_directory",
    "observe_imports",
    "observe_exports",
    "observe_boundaries",
    "detect_encoding",
    "check_line_endings",
    # Boundary helpers and types
    "BoundaryDefinition",
    "BoundaryObservation",
    "BoundaryType",
    "create_layer_boundary",
    "create_package_boundary",
    # Export helpers and types
    "DefinitionType",
    "ExportDefinition",
    "ModuleExports",
    "Visibility",
    # JS sight types
    "JSImportStatement",
    "JSExportStatement",
    "JSImportExportObservation",
    # Java sight types
    "JavaImportStatement",
    "JavaClassDefinition",
    "JavaObservation",
    # Go sight types
    "GoImportStatement",
    "GoExportDefinition",
    "GoObservation",
    # Language detection
    "LanguageDetector",
    "LanguageDetection",
    # File sight types
    "DirectoryTree",
    "FileMetadata",
    "TraversalConfig",
    # Encoding sight types
    "EncodingConfidence",
    "EncodingObservation",
    "LineEndingType",
    # Import sight types
    "ImportObservation",
    "ImportStatement",
]


# Test the registry
if __name__ == "__main__":
    print("=== Eye Registry Test ===\n")

    import tempfile

    # Test registry initialization
    print("1. Registry Initialization:")
    print(f"   Available eyes: {list_eyes()}")
    print(f"   Valid eyes: {registry.list_valid_eyes()}")

    # Test capabilities
    print("\n2. Eye Capabilities:")
    caps = get_capabilities()
    for name, cap in caps.items():
        print(f"   {name}:")
        print(f"     Description: {cap.description}")
        print(f"     Inputs: {cap.input_types}")
        print(f"     Version: {cap.version}")
        print(f"     Deterministic: {cap.deterministic}")
        print(f"     Side-effect free: {cap.side_effect_free}")

    # Test validation
    print("\n3. Validation Status:")
    for name in list_eyes():
        is_valid, errors = registry.get_validation_status(name)
        status = "✓" if is_valid else "✗"
        print(f"   {status} {name}")
        if errors:
            for error in errors:
                print(f"      - {error}")

    # Test file observation
    print("\n4. Test File Observation:")
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(b'''
"""Test file for observation."""
import os
from pathlib import Path

def test_function(arg: str) -> str:
    return arg.upper()
''')
        test_file = Path(f.name)

    try:
        # Single eye observation
        print(f"   Testing file: {test_file}")
        result = observe_with(test_file, "import_sight")
        if result and result.raw_payload:
            import_obs = result.raw_payload
            print(f"   Import count: {len(import_obs.statements)}")

        # Comprehensive observation
        print("\n5. Comprehensive Python File Observation:")
        composite = observe_python_file(test_file)
        print(f"   Total observations: {len(composite.observations)}")
        print(f"   Successful: {len(composite.successful_observations)}")
        print(f"   Overall confidence: {composite.confidence_score:.2f}")

        # Export to dict
        print("\n6. Export to Dictionary:")
        export_dict = export_observations_to_dict(composite)
        print(f"   Keys in export: {list(export_dict.keys())}")
        print(f"   Observation count: {export_dict.get('observation_count')}")

    finally:
        test_file.unlink()

    # Test directory observation
    print("\n7. Test Directory Observation:")
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create a simple Python project
        (root / "module1.py").write_text("def func1(): pass")
        (root / "module2.py").write_text("from module1 import func1")
        (root / "__init__.py").write_text("")

        composite_dir = observe_python_directory(root)
        print(f"   Directory: {root}")
        print(f"   Observations: {len(composite_dir.observations)}")

        # Check for boundary_sight results
        for obs in composite_dir.observations:
            if obs.provenance and obs.provenance.observer_name == "boundary_sight":
                if obs.raw_payload:
                    print("   Boundary analysis completed")

    # Test eye suggestions
    print("\n8. Eye Suggestions:")
    test_files = [
        Path("/tmp/test.py"),
        Path("/tmp/test.txt"),
        Path("/tmp/project/"),
    ]

    for test_path in test_files:
        suggestions = get_eye_for_file_type(test_path)
        print(f"   {test_path}: {suggestions}")

    print("\n=== Test Complete ===")
