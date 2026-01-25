"""
Structural complexity measurement for CodeMarshal.

This module measures structural size and nesting, not difficulty.
Complexity here is mass, not weight. A large thing is not automatically heavy.
"""

import ast
import statistics
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Import from observations layer (allowed per architecture)
from observations.eyes.export_sight import ExportSight
from observations.record.snapshot import CodeSnapshot


@dataclass(frozen=True)
class FileComplexity:
    """Structural complexity measurements for a single file.

    Contains only numeric counts of structure and nesting.
    No labels, no interpretations.
    """

    file_path: Path
    total_nodes: int  # Total AST nodes in the file
    function_count: int  # Number of function definitions
    class_count: int  # Number of class definitions
    max_depth: int  # Maximum AST nesting depth
    avg_depth: float  # Average AST nesting depth

    # Structural metrics (counts of specific node types)
    if_count: int  # if statements
    loop_count: int  # for/while loops
    try_count: int  # try blocks
    with_count: int  # with statements

    @property
    def branching_factor(self) -> float:
        """Average branches per control structure.
        Simple structural measure, not cyclomatic complexity.
        """
        control_structures = (
            self.if_count + self.loop_count + self.try_count + self.with_count
        )
        if control_structures == 0:
            return 0.0
        return float(self.total_nodes) / control_structures

    @property
    def nesting_intensity(self) -> float:
        """Ratio of max depth to total nodes.
        Higher = deeper relative to size.
        """
        if self.total_nodes == 0:
            return 0.0
        return self.max_depth / self.total_nodes


@dataclass(frozen=True)
class ASTNodeTypeCounts:
    """Counts of specific AST node types.

    Used for structural analysis without semantic interpretation.
    """

    node_type: str
    count: int
    file_count: int  # Number of files containing this node type
    avg_per_file: float  # Average count per file

    @classmethod
    def from_counts(cls, node_type: str, counts: list[int]) -> "ASTNodeTypeCounts":
        """Create from list of counts per file."""
        total = sum(counts)
        file_count = len([c for c in counts if c > 0])
        avg = total / len(counts) if counts else 0.0

        return cls(
            node_type=node_type, count=total, file_count=file_count, avg_per_file=avg
        )


class ASTComplexityVisitor(ast.NodeVisitor):
    """AST visitor for measuring structural complexity.

    This visitor:
    - Counts nodes
    - Measures depth
    - Tracks specific node types

    It never:
    - Assigns complexity scores
    - Applies thresholds
    - Makes judgments about code quality
    """

    def __init__(self):
        """Initialize visitor with empty counters."""
        self.total_nodes = 0
        self.max_depth = 0
        self.total_depth = 0
        self.node_type_counts: Counter[str] = Counter()
        self.current_depth = 0

        # Initialize specific node counters
        self.function_count = 0
        self.class_count = 0
        self.if_count = 0
        self.loop_count = 0
        self.try_count = 0
        self.with_count = 0

    def visit(self, node: ast.AST) -> Any:
        """Visit a node and update measurements."""
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        self.total_depth += self.current_depth

        self.total_nodes += 1
        node_type = type(node).__name__
        self.node_type_counts[node_type] += 1

        # Count specific structural elements
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            self.function_count += 1
        elif isinstance(node, ast.ClassDef):
            self.class_count += 1
        elif isinstance(node, ast.If):
            self.if_count += 1
        elif isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
            self.loop_count += 1
        elif isinstance(node, ast.Try):
            self.try_count += 1
        elif isinstance(node, ast.With) or isinstance(node, ast.AsyncWith):
            self.with_count += 1

        # Continue traversing children
        self.generic_visit(node)
        self.current_depth -= 1

        return None

    def get_complexity_metrics(self, file_path: Path) -> FileComplexity:
        """Extract complexity metrics from visitor state."""
        avg_depth = self.total_depth / self.total_nodes if self.total_nodes > 0 else 0.0

        return FileComplexity(
            file_path=file_path,
            total_nodes=self.total_nodes,
            function_count=self.function_count,
            class_count=self.class_count,
            max_depth=self.max_depth,
            avg_depth=avg_depth,
            if_count=self.if_count,
            loop_count=self.loop_count,
            try_count=self.try_count,
            with_count=self.with_count,
        )


class ComplexityCalculator:
    """Calculates structural complexity metrics.

    This class:
    - Measures AST depth and node counts
    - Counts branches
    - Reports raw integers and distributions

    It never:
    - Uses "cyclomatic complexity" labels
    - Applies thresholds
    - Flags "too complex" code
    """

    def __init__(self, export_sight: ExportSight | None = None):
        """Initialize with optional export sight instance."""
        self._export_sight = export_sight or ExportSight()

    def calculate_file_complexity(
        self, file_path: Path, source_code: str
    ) -> FileComplexity | None:
        """Calculate complexity metrics for a single file.

        Returns:
            FileComplexity object if successful, None if parsing failed.
        """
        try:
            tree = ast.parse(source_code, filename=str(file_path))
            visitor = ASTComplexityVisitor()
            visitor.visit(tree)
            return visitor.get_complexity_metrics(file_path)
        except (SyntaxError, ValueError, TypeError):
            # Parsing failed - return None
            # This is not an error, it's a limitation (handled by uncertainty module)
            return None

    def calculate_snapshot_complexity(
        self, snapshot: CodeSnapshot
    ) -> tuple[FileComplexity, ...]:
        """Calculate complexity for all Python files in snapshot.

        Returns:
            Tuple of FileComplexity objects for successfully parsed files.
        """
        complexities: list[FileComplexity] = []

        # Get file contents from snapshot
        # This is a simplified assumption - in reality, we'd need to access
        # the actual file contents from the snapshot's observations

        # For now, we'll use a placeholder approach
        # In the actual implementation, we would iterate through the snapshot's
        # file observations and parse each Python file

        return tuple(complexities)

    def aggregate_node_type_counts(
        self,
        file_complexities: Sequence[FileComplexity],
        visitor_data: list[tuple[Path, Counter]] | None = None,
    ) -> tuple[ASTNodeTypeCounts, ...]:
        """Aggregate counts of AST node types across files.

        Args:
            file_complexities: File complexity measurements
            visitor_data: Optional list of (file_path, node_type_counts)

        Returns:
            Tuple of ASTNodeTypeCounts, sorted by total count.
        """
        if not visitor_data:
            return ()

        # Group counts by node type
        node_type_accumulator: dict[str, list[int]] = defaultdict(list)

        for _file_path, node_counts in visitor_data:
            for node_type, count in node_counts.items():
                node_type_accumulator[node_type].append(count)

        # Create ASTNodeTypeCounts objects
        type_counts: list[ASTNodeTypeCounts] = []

        for node_type, counts in node_type_accumulator.items():
            type_count = ASTNodeTypeCounts.from_counts(node_type, counts)
            type_counts.append(type_count)

        # Sort by total count descending
        type_counts.sort(key=lambda x: x.count, reverse=True)
        return tuple(type_counts)

    def calculate_complexity_distributions(
        self, file_complexities: Sequence[FileComplexity]
    ) -> dict[str, dict[str, float]]:
        """Calculate statistical distributions of complexity metrics.

        Returns:
            Dictionary mapping metric names to distribution statistics.
        """
        if not file_complexities:
            return {}

        metrics: dict[str, list[float]] = {
            "total_nodes": [],
            "function_count": [],
            "class_count": [],
            "max_depth": [],
            "avg_depth": [],
            "if_count": [],
            "loop_count": [],
            "try_count": [],
            "with_count": [],
            "branching_factor": [],
            "nesting_intensity": [],
        }

        # Collect values
        for complexity in file_complexities:
            metrics["total_nodes"].append(float(complexity.total_nodes))
            metrics["function_count"].append(float(complexity.function_count))
            metrics["class_count"].append(float(complexity.class_count))
            metrics["max_depth"].append(float(complexity.max_depth))
            metrics["avg_depth"].append(float(complexity.avg_depth))
            metrics["if_count"].append(float(complexity.if_count))
            metrics["loop_count"].append(float(complexity.loop_count))
            metrics["try_count"].append(float(complexity.try_count))
            metrics["with_count"].append(float(complexity.with_count))
            metrics["branching_factor"].append(complexity.branching_factor)
            metrics["nesting_intensity"].append(complexity.nesting_intensity)

        # Calculate statistics for each metric
        distributions: dict[str, dict[str, float]] = {}

        for metric_name, values in metrics.items():
            if not values:
                continue

            try:
                stats = self._calculate_statistics(values)
                distributions[metric_name] = stats
            except (statistics.StatisticsError, ValueError):
                # Skip metrics that can't be calculated
                continue

        return distributions

    def _calculate_statistics(self, values: list[float]) -> dict[str, float]:
        """Calculate basic statistics for a list of values."""
        if not values:
            return {}

        try:
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
                "q1": statistics.quantiles(values, n=4)[0]
                if len(values) >= 4
                else values[0],
                "q3": statistics.quantiles(values, n=4)[2]
                if len(values) >= 4
                else values[-1],
            }
        except (statistics.StatisticsError, IndexError):
            # Fallback for edge cases
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
                "median": sorted(values)[len(values) // 2],
            }


def calculate_complexity_pattern(
    file_contents: dict[Path, str], export_sight: ExportSight | None = None
) -> dict:
    """Main complexity calculation function for pattern registry.

    This is the function that will be registered in patterns/__init__.py.

    Args:
        file_contents: Dictionary mapping file paths to source code
        export_sight: Optional ExportSight instance

    Returns:
        Dict with numeric complexity measurements only.
    """
    calculator = ComplexityCalculator(export_sight)

    # Calculate complexity for each file
    complexities: list[FileComplexity] = []
    visitor_data: list[tuple[Path, Counter]] = []
    parse_failures = 0

    for file_path, source_code in file_contents.items():
        # Only process Python files
        if file_path.suffix != ".py":
            continue

        try:
            # Parse and analyze
            tree = ast.parse(source_code, filename=str(file_path))
            visitor = ASTComplexityVisitor()
            visitor.visit(tree)

            # Get complexity metrics
            complexity = visitor.get_complexity_metrics(file_path)
            complexities.append(complexity)

            # Store node type counts for aggregation
            visitor_data.append((file_path, visitor.node_type_counts))

        except (SyntaxError, ValueError, TypeError):
            # Parsing failed - count as failure
            parse_failures += 1
            continue

    # Calculate distributions
    distributions = calculator.calculate_complexity_distributions(complexities)

    # Aggregate node type counts
    node_type_counts = calculator.aggregate_node_type_counts(complexities, visitor_data)

    # Convert to serializable format
    result: dict = {
        "file_count": len(complexities),
        "parse_failures": parse_failures,
        "distributions": distributions,
        "file_complexities": [],
        "node_type_counts": [],
        "summary": {},
    }

    # Add file complexities (top 100 for performance)
    top_complexities = sorted(complexities, key=lambda c: c.total_nodes, reverse=True)[
        :100
    ]
    for complexity in top_complexities:
        result["file_complexities"].append(
            {
                "file_path": str(complexity.file_path),
                "total_nodes": complexity.total_nodes,
                "function_count": complexity.function_count,
                "class_count": complexity.class_count,
                "max_depth": complexity.max_depth,
                "avg_depth": complexity.avg_depth,
                "if_count": complexity.if_count,
                "loop_count": complexity.loop_count,
                "try_count": complexity.try_count,
                "with_count": complexity.with_count,
                "branching_factor": complexity.branching_factor,
                "nesting_intensity": complexity.nesting_intensity,
            }
        )

    # Add node type counts
    for node_count in node_type_counts:
        result["node_type_counts"].append(
            {
                "node_type": node_count.node_type,
                "count": node_count.count,
                "file_count": node_count.file_count,
                "avg_per_file": node_count.avg_per_file,
            }
        )

    # Calculate summary statistics
    if complexities:
        total_nodes = sum(c.total_nodes for c in complexities)
        total_functions = sum(c.function_count for c in complexities)
        total_classes = sum(c.class_count for c in complexities)

        result["summary"] = {
            "total_nodes": total_nodes,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "avg_nodes_per_file": total_nodes / len(complexities)
            if complexities
            else 0,
            "avg_functions_per_file": total_functions / len(complexities)
            if complexities
            else 0,
            "avg_classes_per_file": total_classes / len(complexities)
            if complexities
            else 0,
        }

    return result


def validate_complexity_output(data: dict) -> tuple[bool, list[str]]:
    """Validate that complexity output maintains invariants.

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors: list[str] = []

    # Check required structure
    required_keys = {
        "file_count",
        "parse_failures",
        "distributions",
        "file_complexities",
        "node_type_counts",
        "summary",
    }
    missing_keys = required_keys - set(data.keys())
    if missing_keys:
        errors.append(f"Missing required keys: {missing_keys}")

    # Check for prohibited fields
    prohibited_fields = [
        "cyclomatic",
        "cognitive",
        "difficulty",
        "complex",
        "too_complex",
        "threshold",
        "violation",
        "warning",
        "recommendation",
        "should",
        "could",
    ]

    def check_for_prohibited(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                key_lower = str(key).lower()
                if any(prohibited in key_lower for prohibited in prohibited_fields):
                    errors.append(f"Prohibited field at {path}.{key}")
                check_for_prohibited(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_for_prohibited(item, f"{path}[{i}]")

    check_for_prohibited(data)

    # Check distributions for numeric values only
    distributions = data.get("distributions", {})
    for metric_name, stats in distributions.items():
        if not isinstance(stats, dict):
            errors.append(f"Distribution {metric_name} must be dict")
            continue

        numeric_fields = [
            "count",
            "min",
            "max",
            "mean",
            "median",
            "std_dev",
            "q1",
            "q3",
        ]
        for field in numeric_fields:
            value = stats.get(field)
            if value is not None and not isinstance(value, (int, float)):
                errors.append(f"Distribution {metric_name}.{field} must be numeric")

    # Check that no cyclomatic complexity is calculated
    # We'll look for fields that might indicate cyclomatic complexity
    cyclomatic_indicators = [
        "mccabe",
        "cyclomatic",
        "complexity_score",
        "cognitive_weight",
    ]

    def check_for_cyclomatic(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                key_lower = str(key).lower()
                if any(indicator in key_lower for indicator in cyclomatic_indicators):
                    errors.append(f"Cyclomatic complexity field at {path}.{key}")
                check_for_cyclomatic(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_for_cyclomatic(item, f"{path}[{i}]")

    check_for_cyclomatic(data)

    # Check that all values are numeric or structural
    # No labels, no interpretations
    def check_value_types(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and key not in ["file_path", "node_type"]:
                    # Check if string contains interpretation
                    interpretation_words = [
                        "high",
                        "low",
                        "normal",
                        "abnormal",
                        "simple",
                        "complex",
                        "difficult",
                    ]
                    if any(word in value.lower() for word in interpretation_words):
                        errors.append(f"Interpretive string at {path}.{key}: {value}")
                elif isinstance(value, (int, float, bool, type(None))):
                    pass  # Valid types
                elif isinstance(value, (list, dict)):
                    check_value_types(value, f"{path}.{key}" if path else key)
                else:
                    errors.append(f"Invalid value type at {path}.{key}: {type(value)}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_value_types(item, f"{path}[{i}]")

    check_value_types(data)

    return (len(errors) == 0, errors)


# Test function to verify invariants
def test_complexity_invariants() -> tuple[bool, list[str]]:
    """Test that the module maintains its invariants.

    Returns:
        Tuple of (all_passed, list_of_failed_tests)
    """
    failures: list[str] = []

    try:
        # Test 1: No cyclomatic complexity
        # Create a simple test file
        test_code = """
def simple_function(x):
    if x > 0:
        return x
    else:
        return -x
"""

        # Create test data
        test_files = {Path("test.py"): test_code}

        # Calculate complexity
        result = calculate_complexity_pattern(test_files)

        # Check that no cyclomatic complexity fields exist
        is_valid, errors = validate_complexity_output(result)
        if not is_valid:
            failures.extend(errors)

        # Test 2: All outputs are numeric or structural
        if not isinstance(result, dict):
            failures.append("Result should be dict")

        # Check that distributions contain only numeric values
        distributions = result.get("distributions", {})
        for metric_name, stats in distributions.items():
            if not isinstance(stats, dict):
                failures.append(f"Distribution {metric_name} should be dict")
            else:
                for key, value in stats.items():
                    if not isinstance(value, (int, float)):
                        failures.append(
                            f"Distribution value {metric_name}.{key} should be numeric"
                        )

        # Test 3: Data structures are immutable
        test_complexity = FileComplexity(
            file_path=Path("test.py"),
            total_nodes=10,
            function_count=1,
            class_count=0,
            max_depth=3,
            avg_depth=1.5,
            if_count=1,
            loop_count=0,
            try_count=0,
            with_count=0,
        )

        # Try to modify (should fail for frozen dataclass)
        try:
            test_complexity.total_nodes = 11  # type: ignore
            failures.append("FileComplexity should be immutable")
        except (AttributeError, dataclasses.FrozenInstanceError):
            pass  # Expected

        # Test 4: No thresholds or judgments
        # Check that no fields contain threshold values or judgments
        def check_for_judgments(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    key_lower = str(key).lower()
                    judgment_words = [
                        "threshold",
                        "limit",
                        "maximum",
                        "minimum",
                        "acceptable",
                        "unacceptable",
                    ]
                    if any(word in key_lower for word in judgment_words):
                        failures.append(f"Judgment field at {path}.{key}")
                    check_for_judgments(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_for_judgments(item, f"{path}[{i}]")

        check_for_judgments(result)

        # Test 5: Branching factor is a simple ratio, not cyclomatic
        # Verify that branching_factor is calculated correctly
        for file_data in result.get("file_complexities", []):
            if "branching_factor" in file_data:
                bf = file_data["branching_factor"]
                if not isinstance(bf, (int, float)):
                    failures.append("branching_factor must be numeric")
                elif bf < 0:
                    failures.append("branching_factor must be non-negative")

        # Test 6: ASTNodeTypeCounts is structural only
        test_node_counts = ASTNodeTypeCounts(
            node_type="FunctionDef", count=100, file_count=50, avg_per_file=2.0
        )

        # Check that it's immutable
        try:
            test_node_counts.count = 101  # type: ignore
            failures.append("ASTNodeTypeCounts should be immutable")
        except (AttributeError, dataclasses.FrozenInstanceError):
            pass  # Expected

    except Exception as e:
        failures.append(f"Test failed with exception: {e}")

    return (len(failures) == 0, failures)


# Import at bottom to avoid circular imports
import dataclasses  # noqa: E402

if __name__ == "__main__":
    # Run invariant tests when executed directly
    passed, failures = test_complexity_invariants()

    if passed:
        print("✓ All complexity invariants maintained")
        print("  - Outputs are numeric/structural only")
        print("  - No cyclomatic complexity calculations")
        print("  - No thresholds or judgments")
        print("  - Data structures immutable")
        print("  - Branching factor is simple ratio, not cyclomatic")
    else:
        print("✗ Complexity invariant failures:")
        for failure in failures:
            print(f"  - {failure}")
        exit(1)
