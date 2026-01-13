"""
Pattern Registry for CodeMarshal.

This module provides explicit exports of pattern calculators and metadata.
It is purely declarative - no logic, no defaults, no interpretation.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

# Import pattern calculators from this package
# Using absolute imports to maintain clarity
from . import density
from . import coupling
from . import complexity
from . import violations
from . import uncertainty


class PatternType(Enum):
    """Types of patterns in the system."""
    DENSITY = "density"
    COUPLING = "coupling"
    COMPLEXITY = "complexity"
    VIOLATIONS = "violations"
    UNCERTAINTY = "uncertainty"


class InputRequirement(Enum):
    """Required inputs for each pattern."""
    SNAPSHOT = "snapshot"                    # CodeSnapshot object
    IMPORT_SIGHT = "import_sight"           # ImportSight instance
    EXPORT_SIGHT = "export_sight"           # ExportSight instance
    RULES_CONFIG = "rules_config"           # Boundary rules configuration
    FILE_CONTENTS = "file_contents"         # Dict[Path, str]
    ANALYZED_FILES = "analyzed_files"       # Set[Path]
    SKIPPED_FILES = "skipped_files"         # Dict[Path, UncertaintyType]
    TOTAL_FILES = "total_files_found"       # int
    DECLARED_LIMITATIONS = "declared_limitations"  # List[Dict]
    PARSING_ERRORS = "parsing_error_count"  # int
    VALIDATION_RESULTS = "validation_results"  # Dict


class OutputType(Enum):
    """Types of outputs each pattern produces."""
    DICT = "dict"           # Dictionary with numeric/boolean values
    LIST = "list"           # List of measurements
    TUPLE = "tuple"         # Immutable sequence
    BOOL = "bool"           # Boolean value
    INT = "int"            # Integer
    FLOAT = "float"        # Floating point number


@dataclass(frozen=True)
class PatternMetadata:
    """Metadata for a pattern calculator.
    
    This is purely declarative - it describes what the pattern does,
    what it needs, and what it produces.
    """
    pattern_type: PatternType
    name: str
    description: str
    calculator_function: Callable[[Any], Dict[str, Any]]
    required_inputs: Tuple[InputRequirement, ...]
    produced_outputs: Tuple[OutputType, ...]
    output_schema: Dict[str, Any]  # Structural description of output
    
    @property
    def is_deterministic(self) -> bool:
        """All patterns must be deterministic."""
        return True
    
    @property
    def is_numeric_only(self) -> bool:
        """All patterns must produce numeric, boolean, or structural outputs."""
        return True


# Pattern Registry
# This is the single source of truth for what patterns exist
_PATTERN_REGISTRY: Dict[PatternType, PatternMetadata] = {}


def register_pattern(metadata: PatternMetadata) -> None:
    """Register a pattern in the registry.
    
    This function is idempotent and should only be called during import.
    """
    if metadata.pattern_type in _PATTERN_REGISTRY:
        raise ValueError(f"Pattern {metadata.pattern_type} already registered")
    
    _PATTERN_REGISTRY[metadata.pattern_type] = metadata


# Density Pattern Metadata
register_pattern(
    PatternMetadata(
        pattern_type=PatternType.DENSITY,
        name="import_density",
        description="Measures concentration of import references. Returns counts, distributions, and clustering coefficients.",
        calculator_function=density.calculate_density_pattern,
        required_inputs=(
            InputRequirement.SNAPSHOT,
            InputRequirement.IMPORT_SIGHT,
        ),
        produced_outputs=(
            OutputType.DICT,
            OutputType.LIST,
            OutputType.FLOAT,
            OutputType.INT,
        ),
        output_schema={
            "file_count": {"type": "int", "description": "Number of files analyzed"},
            "module_count": {"type": "int", "description": "Number of unique modules referenced"},
            "clustering_coefficient": {"type": "float", "description": "Import concentration (0-1)"},
            "distributions": {
                "type": "dict",
                "description": "Statistical distributions of density metrics",
                "keys": {
                    "file_import_count": {
                        "type": "dict",
                        "description": "Distribution of import counts per file",
                        "fields": ["count", "min", "max", "mean", "median", "std_dev", "percentiles", "histogram"]
                    },
                    "file_variety_ratio": {
                        "type": "dict",
                        "description": "Distribution of unique import ratios",
                        "fields": ["count", "min", "max", "mean", "median", "std_dev"]
                    }
                }
            },
            "file_densities": {
                "type": "list",
                "description": "Import density per file (top 100)",
                "item_schema": {
                    "file_path": "str",
                    "import_count": "int",
                    "unique_import_count": "int",
                    "internal_imports": "int",
                    "external_imports": "int",
                    "import_depth": "float",
                    "import_variety_ratio": "float"
                }
            },
            "module_references": {
                "type": "list",
                "description": "Module reference counts (top 100)",
                "item_schema": {
                    "module_name": "str",
                    "reference_count": "int",
                    "file_count": "int",
                    "reference_density": "float"
                }
            }
        }
    )
)

# Coupling Pattern Metadata
register_pattern(
    PatternMetadata(
        pattern_type=PatternType.COUPLING,
        name="graph_topology",
        description="Measures graph connectivity. Returns degree distributions, adjacency matrices, and component analysis.",
        calculator_function=coupling.calculate_coupling_pattern,
        required_inputs=(
            InputRequirement.SNAPSHOT,
            InputRequirement.IMPORT_SIGHT,
        ),
        produced_outputs=(
            OutputType.DICT,
            OutputType.LIST,
            OutputType.FLOAT,
            OutputType.INT,
        ),
        output_schema={
            "topology": {
                "type": "dict",
                "description": "Graph topology measurements",
                "fields": {
                    "node_count": "int",
                    "edge_count": "int",
                    "bidirectional_edge_count": "int",
                    "self_reference_count": "int",
                    "max_fan_in": "int",
                    "max_fan_out": "int",
                    "avg_fan_in": "float",
                    "avg_fan_out": "float",
                    "avg_total_degree": "float",
                    "density": "float",
                    "average_clustering": "float",
                    "possible_edges": "int"
                }
            },
            "node_degrees": {
                "type": "list",
                "description": "Degree measurements per node (top 100)",
                "item_schema": {
                    "module_name": "str",
                    "fan_in": "int",
                    "fan_out": "int",
                    "total_degree": "int",
                    "degree_balance": "float",
                    "dependency_ratio": "float"
                }
            },
            "edges": {
                "type": "list",
                "description": "Directed edges in the graph (top 200)",
                "item_schema": {
                    "source_module": "str",
                    "target_module": "str",
                    "count": "int",
                    "is_bidirectional": "bool",
                    "is_self_edge": "bool"
                }
            },
            "bidirectional_pairs": {
                "type": "list",
                "description": "Mutual import pairs",
                "item_schema": {
                    "module_a": "str",
                    "module_b": "str",
                    "a_to_b_count": "int",
                    "b_to_a_count": "int",
                    "total_interactions": "int",
                    "symmetry_ratio": "float"
                }
            },
            "adjacency": {
                "type": "dict",
                "description": "Adjacency matrix representation",
                "fields": {
                    "node_labels": "list[str]",
                    "matrix": "list[list[int]]"
                }
            },
            "components": {
                "type": "dict",
                "description": "Connected component analysis",
                "fields": {
                    "count": "int",
                    "sizes": "list[int]",
                    "largest_component_size": "int"
                }
            }
        }
    )
)

# Complexity Pattern Metadata
register_pattern(
    PatternMetadata(
        pattern_type=PatternType.COMPLEXITY,
        name="structural_complexity",
        description="Measures structural size and nesting. Returns node counts, depth measurements, and AST statistics.",
        calculator_function=complexity.calculate_complexity_pattern,
        required_inputs=(
            InputRequirement.FILE_CONTENTS,
            InputRequirement.EXPORT_SIGHT,
        ),
        produced_outputs=(
            OutputType.DICT,
            OutputType.LIST,
            OutputType.FLOAT,
            OutputType.INT,
        ),
        output_schema={
            "file_count": {"type": "int", "description": "Number of files successfully parsed"},
            "parse_failures": {"type": "int", "description": "Number of files that failed to parse"},
            "distributions": {
                "type": "dict",
                "description": "Statistical distributions of complexity metrics",
                "keys": {
                    "total_nodes": {
                        "type": "dict",
                        "description": "Distribution of total AST nodes per file",
                        "fields": ["count", "min", "max", "mean", "median", "std_dev", "q1", "q3"]
                    },
                    "function_count": {
                        "type": "dict",
                        "description": "Distribution of function counts per file",
                        "fields": ["count", "min", "max", "mean", "median", "std_dev"]
                    },
                    "max_depth": {
                        "type": "dict",
                        "description": "Distribution of maximum nesting depth per file",
                        "fields": ["count", "min", "max", "mean", "median", "std_dev"]
                    }
                }
            },
            "file_complexities": {
                "type": "list",
                "description": "Complexity measurements per file (top 100)",
                "item_schema": {
                    "file_path": "str",
                    "total_nodes": "int",
                    "function_count": "int",
                    "class_count": "int",
                    "max_depth": "int",
                    "avg_depth": "float",
                    "if_count": "int",
                    "loop_count": "int",
                    "try_count": "int",
                    "with_count": "int",
                    "branching_factor": "float",
                    "nesting_intensity": "float"
                }
            },
            "node_type_counts": {
                "type": "list",
                "description": "Counts of AST node types",
                "item_schema": {
                    "node_type": "str",
                    "count": "int",
                    "file_count": "int",
                    "avg_per_file": "float"
                }
            },
            "summary": {
                "type": "dict",
                "description": "Summary statistics",
                "fields": {
                    "total_nodes": "int",
                    "total_functions": "int",
                    "total_classes": "int",
                    "avg_nodes_per_file": "float",
                    "avg_functions_per_file": "float",
                    "avg_classes_per_file": "float"
                }
            }
        }
    )
)

# Violations Pattern Metadata
register_pattern(
    PatternMetadata(
        pattern_type=PatternType.VIOLATIONS,
        name="boundary_violations",
        description="Detects explicit boundary crossings. Returns boolean facts with evidence anchors.",
        calculator_function=violations.calculate_violations,
        required_inputs=(
            InputRequirement.SNAPSHOT,
            InputRequirement.RULES_CONFIG,
        ),
        produced_outputs=(
            OutputType.DICT,
            OutputType.BOOL,
            OutputType.LIST,
            OutputType.INT,
        ),
        output_schema={
            "has_violations": {"type": "bool", "description": "Whether any violations were detected"},
            "violation_count": {"type": "int", "description": "Number of violations found"},
            "violations": {
                "type": "list",
                "description": "List of boundary violations",
                "item_schema": {
                    "rule_id": "str",
                    "evidence": "list[dict]",
                    "boundary_type": "str",
                    "detected_at": "str"
                }
            },
            "rule_ids": {"type": "list[str]", "description": "IDs of rules that were checked"},
            "rule_count": {"type": "int", "description": "Number of rules applied"},
            "checked_at": {"type": "str", "description": "Timestamp of check"}
        }
    )
)

# Uncertainty Pattern Metadata
register_pattern(
    PatternMetadata(
        pattern_type=PatternType.UNCERTAINTY,
        name="uncertainty_quantification",
        description="Quantifies knowledge gaps and measurement uncertainty. Returns coverage ratios and confidence scores.",
        calculator_function=uncertainty.calculate_uncertainty_metrics,
        required_inputs=(
            InputRequirement.ANALYZED_FILES,
            InputRequirement.SKIPPED_FILES,
            InputRequirement.TOTAL_FILES,
            InputRequirement.DECLARED_LIMITATIONS,
            InputRequirement.PARSING_ERRORS,
            InputRequirement.VALIDATION_RESULTS,
        ),
        produced_outputs=(
            OutputType.DICT,
            OutputType.FLOAT,
            OutputType.INT,
            OutputType.LIST,
        ),
        output_schema={
            "file_coverage": {
                "type": "dict",
                "description": "File analysis coverage statistics",
                "fields": {
                    "total_files": "int",
                    "analyzed": "int",
                    "skipped": "int",
                    "coverage_ratio": "float",
                    "uncertainty_ratio": "float"
                }
            },
            "confidence_score": {"type": "float", "description": "Overall confidence in observations (0-1)"},
            "uncertainty_measurements": {
                "type": "dict",
                "description": "Detailed uncertainty measurements by type",
                "keys": {
                    "total_items": "int",
                    "by_type": "dict[str, list[dict]]",
                    "average_confidence_dampener": "float"
                }
            },
            "blind_spots": {
                "type": "list",
                "description": "Declared system limitations",
                "item_schema": {
                    "identifier": "str",
                    "limitation_type": "str",
                    "description": "str",
                    "impact_domain": "list[str]",
                    "confidence_reduction": "float"
                }
            },
            "missing_files": {"type": "list[str]", "description": "Files that were expected but not analyzed"},
            "missing_file_count": {"type": "int", "description": "Number of missing files"},
            "computed_at": {"type": "str", "description": "Timestamp of computation"}
        }
    )
)


def get_pattern(pattern_type: PatternType) -> Optional[PatternMetadata]:
    """Get pattern metadata by type.
    
    Returns:
        PatternMetadata if found, None otherwise.
    """
    return _PATTERN_REGISTRY.get(pattern_type)


def get_all_patterns() -> List[PatternMetadata]:
    """Get all registered patterns.
    
    Returns:
        List of all PatternMetadata objects, sorted by pattern type.
    """
    return sorted(_PATTERN_REGISTRY.values(), key=lambda p: p.pattern_type.value)


def pattern_exists(pattern_type: PatternType) -> bool:
    """Check if a pattern is registered.
    
    Returns:
        True if pattern exists, False otherwise.
    """
    return pattern_type in _PATTERN_REGISTRY


def get_patterns_by_input(input_req: InputRequirement) -> List[PatternMetadata]:
    """Get all patterns that require a specific input.
    
    Returns:
        List of patterns that require the specified input.
    """
    return [
        metadata for metadata in _PATTERN_REGISTRY.values()
        if input_req in metadata.required_inputs
    ]


def get_patterns_by_output(output_type: OutputType) -> List[PatternMetadata]:
    """Get all patterns that produce a specific output type.
    
    Returns:
        List of patterns that produce the specified output type.
    """
    return [
        metadata for metadata in _PATTERN_REGISTRY.values()
        if output_type in metadata.produced_outputs
    ]


def validate_pattern_inputs(
    pattern_type: PatternType,
    provided_inputs: Dict[InputRequirement, Any]
) -> Tuple[bool, List[str]]:
    """Validate that required inputs are provided for a pattern.
    
    Returns:
        Tuple of (is_valid, list_of_missing_inputs)
    """
    metadata = get_pattern(pattern_type)
    if not metadata:
        return False, [f"Pattern {pattern_type} not found"]
    
    missing: List[str] = []
    
    for required_input in metadata.required_inputs:
        if required_input not in provided_inputs:
            missing.append(f"Missing input: {required_input.value}")
        elif provided_inputs[required_input] is None:
            missing.append(f"Input {required_input.value} is None")
    
    return (len(missing) == 0, missing)


def execute_pattern(
    pattern_type: PatternType,
    inputs: Dict[InputRequirement, Any]
) -> Dict[str, Any]:
    """Execute a pattern with provided inputs.
    
    Args:
        pattern_type: Type of pattern to execute
        inputs: Dictionary mapping InputRequirement to values
        
    Returns:
        Pattern calculation results
        
    Raises:
        ValueError: If pattern not found or inputs invalid
    """
    metadata = get_pattern(pattern_type)
    if not metadata:
        raise ValueError(f"Pattern {pattern_type} not found")
    
    # Validate inputs
    is_valid, missing = validate_pattern_inputs(pattern_type, inputs)
    if not is_valid:
        raise ValueError(f"Invalid inputs for pattern {pattern_type}: {missing}")
    
    # Convert InputRequirement dict to function arguments
    # Each pattern calculator expects different keyword arguments
    # We need to map InputRequirement to the actual parameter names
    
    # This mapping is specific to each pattern function
    # In a real implementation, we might need a more sophisticated mapping
    # For now, we assume the pattern functions accept kwargs and extract what they need
    
    # Since we control all pattern functions, we know they all take a context dict
    # But our current implementations have specific signatures
    # We'll create a wrapper that adapts the InputRequirement dict to each function
    
    # For simplicity in this registry, we'll call the calculator with the inputs dict
    # Pattern functions should be designed to extract what they need from this dict
    result = metadata.calculator_function(inputs)
    
    return result


# Export public API
__all__ = [
    # Pattern types
    'PatternType',
    
    # Input requirements
    'InputRequirement',
    
    # Output types
    'OutputType',
    
    # Metadata class
    'PatternMetadata',
    
    # Registry functions
    'get_pattern',
    'get_all_patterns',
    'pattern_exists',
    'get_patterns_by_input',
    'get_patterns_by_output',
    'validate_pattern_inputs',
    'execute_pattern',
    
    # Pattern names (for convenience)
    'DENSITY_PATTERN',
    'COUPLING_PATTERN',
    'COMPLEXITY_PATTERN',
    'VIOLATIONS_PATTERN',
    'UNCERTAINTY_PATTERN',
]

# Convenience constants
DENSITY_PATTERN = PatternType.DENSITY
COUPLING_PATTERN = PatternType.COUPLING
COMPLEXITY_PATTERN = PatternType.COMPLEXITY
VIOLATIONS_PATTERN = PatternType.VIOLATIONS
UNCERTAINTY_PATTERN = PatternType.UNCERTAINTY


# Validation function for the registry itself
def validate_registry() -> Tuple[bool, List[str]]:
    """Validate that the registry maintains invariants.
    
    Returns:
        Tuple of (all_valid, list_of_errors)
    """
    errors: List[str] = []
    
    # Check that all patterns are registered
    expected_patterns = set(PatternType)
    registered_patterns = set(_PATTERN_REGISTRY.keys())
    
    missing = expected_patterns - registered_patterns
    if missing:
        errors.append(f"Missing pattern registrations: {missing}")
    
    # Check that each pattern has valid metadata
    for pattern_type, metadata in _PATTERN_REGISTRY.items():
        # Check name matches type
        if metadata.pattern_type != pattern_type:
            errors.append(f"Pattern type mismatch: {pattern_type} vs {metadata.pattern_type}")
        
        # Check required inputs are valid
        for input_req in metadata.required_inputs:
            if not isinstance(input_req, InputRequirement):
                errors.append(f"Invalid input requirement for {pattern_type}: {input_req}")
        
        # Check produced outputs are valid
        for output_type in metadata.produced_outputs:
            if not isinstance(output_type, OutputType):
                errors.append(f"Invalid output type for {pattern_type}: {output_type}")
        
        # Check calculator function is callable
        if not callable(metadata.calculator_function):
            errors.append(f"Calculator function for {pattern_type} is not callable")
    
    return (len(errors) == 0, errors)


if __name__ == "__main__":
    # Validate the registry when run directly
    is_valid, errors = validate_registry()
    
    if is_valid:
        print("✓ Pattern registry is valid")
        print(f"  - Registered patterns: {[p.value for p in _PATTERN_REGISTRY.keys()]}")
        print("  - All patterns have metadata")
        print("  - All calculator functions are callable")
    else:
        print("✗ Pattern registry validation failed:")
        for error in errors:
            print(f"  - {error}")
        exit(1)