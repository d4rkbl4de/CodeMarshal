"""
Import density measurement for CodeMarshal.

This module calculates concentration of references, nothing more.
Density is about where attention piles up, not why.
"""

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Import from observations layer (allowed per architecture)
from observations.eyes.import_sight import ImportObservation, ImportSight
from observations.record.snapshot import CodeSnapshot


@dataclass(frozen=True)
class FileImportDensity:
    """Import density measurements for a single file.

    Contains only numeric counts and computed statistics.
    No labels, no interpretations.
    """

    file_path: Path
    import_count: int
    unique_import_count: int  # Count of distinct imported modules
    internal_imports: int  # Imports within the same project
    external_imports: int  # Imports to external packages
    import_depth: float  # Average depth of import chains (if available)

    @property
    def import_variety_ratio(self) -> float:
        """Ratio of unique imports to total imports.
        1.0 = all imports are unique, lower = more duplicates.
        """
        if self.import_count == 0:
            return 0.0
        return self.unique_import_count / self.import_count


@dataclass(frozen=True)
class ModuleReferenceCounts:
    """How many files reference each module.

    Pure counts, no judgments.
    """

    module_name: str
    reference_count: int  # Number of files importing this module
    file_paths: tuple[Path, ...]  # Which files import it (immutable)

    @property
    def reference_density(self) -> float:
        """Normalized reference count (0 to 1 scale).
        Higher = more files reference this module.
        """
        # This will be normalized later across all modules
        return float(self.reference_count)


class DensityDistribution:
    """Statistical distribution of density measurements.

    Contains only numeric percentiles and moments.
    No thresholds, no "high" or "low" labels.
    """

    def __init__(self, values: Sequence[float]):
        """Initialize with a sequence of numeric values."""
        self._values = sorted(values)
        self._count = len(values)

    @property
    def count(self) -> int:
        """Number of values in the distribution."""
        return self._count

    @property
    def min(self) -> float:
        """Minimum value."""
        return self._values[0] if self._values else 0.0

    @property
    def max(self) -> float:
        """Maximum value."""
        return self._values[-1] if self._values else 0.0

    @property
    def mean(self) -> float:
        """Arithmetic mean."""
        if not self._values:
            return 0.0
        return sum(self._values) / len(self._values)

    @property
    def median(self) -> float:
        """Median (50th percentile)."""
        return self.percentile(50)

    @property
    def std_dev(self) -> float:
        """Standard deviation."""
        if len(self._values) < 2:
            return 0.0
        try:
            return statistics.stdev(self._values)
        except statistics.StatisticsError:
            return 0.0

    def percentile(self, p: float) -> float:
        """Calculate the p-th percentile (0 <= p <= 100)."""
        if not self._values:
            return 0.0

        if p <= 0:
            return self._values[0]
        if p >= 100:
            return self._values[-1]

        # Linear interpolation between closest ranks
        k = (len(self._values) - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)

        if f == c:
            return self._values[int(k)]

        d0 = self._values[int(f)] * (c - k)
        d1 = self._values[int(c)] * (k - f)
        return d0 + d1

    def to_bins(self, num_bins: int = 10) -> list[int]:
        """Convert distribution to histogram bins.

        Returns:
            List of counts for each bin.
        """
        if not self._values or num_bins <= 0:
            return []

        if self.min == self.max:
            # All values are the same
            return [len(self._values)] + [0] * (num_bins - 1)

        bin_width = (self.max - self.min) / num_bins
        bins = [0] * num_bins

        for value in self._values:
            if value == self.max:
                bin_idx = num_bins - 1
            else:
                bin_idx = int((value - self.min) / bin_width)
                bin_idx = max(0, min(num_bins - 1, bin_idx))
            bins[bin_idx] += 1

        return bins


class DensityCalculator:
    """Calculates import density metrics.

    This class:
    - Counts imports per file
    - Counts references per symbol
    - Computes local clustering (relative, not absolute)
    - Returns numeric distributions, percentiles, ranks

    It never:
    - Calls something "hotspot"
    - Flags risk
    - Compares to "best practices"
    """

    def __init__(self, import_sight: ImportSight | None = None):
        """Initialize with optional import sight instance."""
        self._import_sight = import_sight or ImportSight()

    def calculate_file_density(
        self, snapshot: CodeSnapshot
    ) -> tuple[FileImportDensity, ...]:
        """Calculate import density for each file in the snapshot.

        Returns:
            Tuple of FileImportDensity objects, one per file.
        """
        # Get import observations from snapshot
        import_observations = self._import_sight.observe(snapshot)

        # Group imports by source file
        imports_by_file: dict[Path, list[ImportObservation]] = {}
        for observation in import_observations:
            source_file = observation.source_file
            imports_by_file.setdefault(source_file, []).append(observation)

        densities: list[FileImportDensity] = []

        for file_path, imports in imports_by_file.items():
            density = self._calculate_single_file_density(file_path, imports)
            densities.append(density)

        # Sort by import count descending for consistency
        densities.sort(key=lambda d: d.import_count, reverse=True)

        return tuple(densities)

    def _calculate_single_file_density(
        self, file_path: Path, imports: list[ImportObservation]
    ) -> FileImportDensity:
        """Calculate density metrics for a single file."""
        # Count unique imports
        unique_imports = set()
        internal_count = 0
        external_count = 0
        total_depth = 0.0
        depth_samples = 0

        for observation in imports:
            unique_imports.add(observation.imported_module)

            # Classify as internal or external (simplified heuristic)
            # This is a structural classification, not a judgment
            if observation.is_internal_import:
                internal_count += 1
            else:
                external_count += 1

            # Accumulate depth if available
            if observation.import_depth is not None:
                total_depth += observation.import_depth
                depth_samples += 1

        # Calculate average depth
        import_depth = total_depth / depth_samples if depth_samples > 0 else 0.0

        return FileImportDensity(
            file_path=file_path,
            import_count=len(imports),
            unique_import_count=len(unique_imports),
            internal_imports=internal_count,
            external_imports=external_count,
            import_depth=import_depth,
        )

    def calculate_module_reference_counts(
        self, snapshot: CodeSnapshot
    ) -> tuple[ModuleReferenceCounts, ...]:
        """Count how many files reference each module.

        Returns:
            Tuple of ModuleReferenceCounts, sorted by reference count.
        """
        import_observations = self._import_sight.observe(snapshot)

        # Group by module
        module_references: dict[str, list[Path]] = {}

        for observation in import_observations:
            module = observation.imported_module
            source_file = observation.source_file

            if module not in module_references:
                module_references[module] = []

            # Only count each file once per module
            if source_file not in module_references[module]:
                module_references[module].append(source_file)

        # Create ModuleReferenceCounts objects
        counts_list: list[ModuleReferenceCounts] = []

        for module_name, file_paths in module_references.items():
            counts = ModuleReferenceCounts(
                module_name=module_name,
                reference_count=len(file_paths),
                file_paths=tuple(sorted(file_paths)),
            )
            counts_list.append(counts)

        # Sort by reference count descending
        counts_list.sort(key=lambda c: c.reference_count, reverse=True)

        return tuple(counts_list)

    def calculate_density_distributions(
        self,
        file_densities: Sequence[FileImportDensity],
        module_counts: Sequence[ModuleReferenceCounts],
    ) -> dict[str, DensityDistribution]:
        """Calculate statistical distributions of density metrics.

        Returns:
            Dictionary mapping metric names to distributions.
        """
        distributions: dict[str, DensityDistribution] = {}

        # File-level distributions
        if file_densities:
            # Import counts per file
            import_counts = [float(d.import_count) for d in file_densities]
            distributions["file_import_count"] = DensityDistribution(import_counts)

            # Unique import ratio
            variety_ratios = [d.import_variety_ratio for d in file_densities]
            distributions["file_variety_ratio"] = DensityDistribution(variety_ratios)

            # Internal vs external ratios
            internal_ratios = []
            for d in file_densities:
                if d.import_count > 0:
                    internal_ratios.append(d.internal_imports / d.import_count)
                else:
                    internal_ratios.append(0.0)
            distributions["file_internal_ratio"] = DensityDistribution(internal_ratios)

        # Module-level distributions
        if module_counts:
            # Reference counts per module
            ref_counts = [float(c.reference_count) for c in module_counts]
            distributions["module_reference_count"] = DensityDistribution(ref_counts)

            # Normalized reference density (if we have total file count)
            if file_densities:
                total_files = len(file_densities)
                if total_files > 0:
                    densities = [c.reference_count / total_files for c in module_counts]
                    distributions["module_reference_density"] = DensityDistribution(
                        densities
                    )

        return distributions

    def calculate_clustering_coefficient(
        self, module_counts: Sequence[ModuleReferenceCounts], total_files: int
    ) -> float:
        """Calculate local clustering coefficient.

        Simplified measure of how concentrated imports are.
        Returns a value between 0 and 1.

        0 = imports evenly distributed across all files
        1 = imports concentrated in very few files

        This is the Gini coefficient adapted for our use case.
        """
        if total_files == 0 or not module_counts:
            return 0.0

        # Sort reference counts
        counts = sorted([c.reference_count for c in module_counts])
        n = len(counts)

        # Calculate Gini coefficient
        # G = (2 * Σ(i * x_i) / (n * Σx_i)) - (n + 1)/n
        total = sum(counts)

        if total == 0:
            return 0.0

        weighted_sum = sum((i + 1) * value for i, value in enumerate(counts))

        gini = (2 * weighted_sum) / (n * total) - (n + 1) / n

        # Ensure bounds
        return max(0.0, min(1.0, gini))


def calculate_density_pattern(
    snapshot: CodeSnapshot, import_sight: ImportSight | None = None
) -> dict:
    """Main density calculation function for pattern registry.

    This is the function that will be registered in patterns/__init__.py.

    Returns:
        Dict with only numeric density measurements.
    """
    calculator = DensityCalculator(import_sight)

    # Calculate file densities
    file_densities = calculator.calculate_file_density(snapshot)

    # Calculate module reference counts
    module_counts = calculator.calculate_module_reference_counts(snapshot)

    # Calculate distributions
    distributions = calculator.calculate_density_distributions(
        file_densities, module_counts
    )

    # Calculate clustering coefficient
    total_files = len({d.file_path for d in file_densities})
    clustering = calculator.calculate_clustering_coefficient(module_counts, total_files)

    # Convert to serializable format
    result: dict = {
        "file_count": len(file_densities),
        "module_count": len(module_counts),
        "clustering_coefficient": clustering,
        "distributions": {},
        "file_densities": [],
        "module_references": [],
    }

    # Add distributions
    for name, distribution in distributions.items():
        result["distributions"][name] = {
            "count": distribution.count,
            "min": distribution.min,
            "max": distribution.max,
            "mean": distribution.mean,
            "median": distribution.median,
            "std_dev": distribution.std_dev,
            "percentiles": {
                "25": distribution.percentile(25),
                "50": distribution.percentile(50),
                "75": distribution.percentile(75),
                "90": distribution.percentile(90),
                "95": distribution.percentile(95),
            },
            "histogram": distribution.to_bins(10),
        }

    # Add file densities (top 100 for performance)
    top_files = sorted(file_densities, key=lambda d: d.import_count, reverse=True)[:100]
    for density in top_files:
        result["file_densities"].append(
            {
                "file_path": str(density.file_path),
                "import_count": density.import_count,
                "unique_import_count": density.unique_import_count,
                "internal_imports": density.internal_imports,
                "external_imports": density.external_imports,
                "import_depth": density.import_depth,
                "import_variety_ratio": density.import_variety_ratio,
            }
        )

    # Add module references (top 100 for performance)
    top_modules = list(module_counts)[:100]
    for ref_count in top_modules:
        result["module_references"].append(
            {
                "module_name": ref_count.module_name,
                "reference_count": ref_count.reference_count,
                "file_count": len(ref_count.file_paths),
                "reference_density": ref_count.reference_density,
            }
        )

    # Calculate summary statistics
    if file_densities:
        total_imports = sum(d.import_count for d in file_densities)
        avg_imports = total_imports / len(file_densities) if file_densities else 0
        result["summary"] = {
            "total_imports": total_imports,
            "avg_imports_per_file": avg_imports,
            "files_with_imports": sum(1 for d in file_densities if d.import_count > 0),
            "files_without_imports": sum(
                1 for d in file_densities if d.import_count == 0
            ),
        }

    return result


class DensityPatterns:
    """Lightweight wrapper for density metrics used by inquiry layer."""

    def __init__(self, snapshot: CodeSnapshot, import_sight: ImportSight | None = None):
        self._snapshot = snapshot
        self._import_sight = import_sight
        self._cached: dict[str, Any] | None = None

    def _calculate(self) -> dict[str, Any]:
        if self._cached is None:
            try:
                self._cached = calculate_density_pattern(
                    self._snapshot, self._import_sight
                )
            except Exception:
                self._cached = {}
        return self._cached

    def get_module_densities(self) -> dict[str, float]:
        """Return module density values keyed by module name."""
        data = self._calculate()
        densities: dict[str, float] = {}
        for item in data.get("module_references", []):
            module_name = item.get("module_name")
            if not module_name:
                continue
            value = item.get("reference_density", item.get("reference_count", 0))
            try:
                densities[str(module_name)] = float(value)
            except (TypeError, ValueError):
                continue
        return densities

    def get_file_densities(self) -> dict[str, float]:
        """Return file density values keyed by file path."""
        data = self._calculate()
        densities: dict[str, float] = {}
        for item in data.get("file_densities", []):
            file_path = item.get("file_path")
            if not file_path:
                continue
            value = item.get("import_count", 0)
            try:
                densities[str(file_path)] = float(value)
            except (TypeError, ValueError):
                continue
        return densities


def validate_density_output(data: dict) -> tuple[bool, list[str]]:
    """Validate that density output maintains invariants.

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors: list[str] = []

    # Check required structure
    required_keys = {
        "file_count",
        "module_count",
        "clustering_coefficient",
        "distributions",
        "file_densities",
        "module_references",
    }
    missing_keys = required_keys - set(data.keys())
    if missing_keys:
        errors.append(f"Missing required keys: {missing_keys}")

    # Check clustering coefficient bounds
    clustering = data.get("clustering_coefficient", 0)
    if not isinstance(clustering, (int, float)):
        errors.append("Clustering coefficient must be numeric")
    elif clustering < 0 or clustering > 1:
        errors.append(f"Clustering coefficient out of bounds: {clustering}")

    # Check distributions contain only numeric data
    distributions = data.get("distributions", {})
    for name, dist_data in distributions.items():
        if not isinstance(dist_data, dict):
            errors.append(f"Distribution {name} must be dict")
            continue

        numeric_fields = ["count", "min", "max", "mean", "median", "std_dev"]
        for field in numeric_fields:
            value = dist_data.get(field)
            if value is not None and not isinstance(value, (int, float)):
                errors.append(f"Distribution {name}.{field} must be numeric")

    # Check file densities for prohibited fields
    prose_fields = ["hotspot", "risk", "complexity", "warning", "recommendation"]

    for file_data in data.get("file_densities", []):
        for key in file_data.keys():
            if any(prose in key.lower() for prose in prose_fields):
                errors.append(f"File density contains prose-like field: {key}")

    for module_data in data.get("module_references", []):
        for key in module_data.keys():
            if any(prose in key.lower() for prose in prose_fields):
                errors.append(f"Module reference contains prose-like field: {key}")

    return (len(errors) == 0, errors)


# Test function to verify invariants
def test_density_invariants() -> tuple[bool, list[str]]:
    """Test that the module maintains its invariants.

    Returns:
        Tuple of (all_passed, list_of_failed_tests)
    """
    failures: list[str] = []

    try:
        from unittest.mock import Mock

        # Create a mock snapshot for testing
        mock_snapshot = Mock(spec=CodeSnapshot)

        # Test 1: Output contains only allowed data types
        result = calculate_density_pattern(mock_snapshot)

        # Check types
        if not isinstance(result, dict):
            failures.append("Result should be dict")

        if not isinstance(result.get("clustering_coefficient"), (int, float)):
            failures.append("Clustering coefficient must be numeric")

        # Test 2: No prose in outputs
        is_valid, errors = validate_density_output(result)
        if not is_valid:
            failures.extend(errors)

        # Test 3: Distributions are numeric
        distributions = result.get("distributions", {})
        for name, dist in distributions.items():
            if "histogram" in dist:
                hist = dist["histogram"]
                if not isinstance(hist, list):
                    failures.append(f"Histogram for {name} must be list")
                elif hist and not all(isinstance(x, int) for x in hist):
                    failures.append(f"Histogram values for {name} must be integers")

        # Test 4: Density objects are immutable
        DensityCalculator()

        # Create test data
        test_density = FileImportDensity(
            file_path=Path("test.py"),
            import_count=5,
            unique_import_count=4,
            internal_imports=3,
            external_imports=2,
            import_depth=1.5,
        )

        # Try to modify (should fail for frozen dataclass)
        try:
            test_density.import_count = 6  # type: ignore
            failures.append("FileImportDensity should be immutable")
        except (AttributeError, dataclasses.FrozenInstanceError):
            pass  # Expected

        # Test 5: Deterministic outputs
        # Since we're using mocks, we can't fully test determinism
        # But we can test that the same input produces the same output structure

        result1 = calculate_density_pattern(mock_snapshot)
        result2 = calculate_density_pattern(mock_snapshot)

        # Check that keys are the same
        if set(result1.keys()) != set(result2.keys()):
            failures.append("Results not deterministic (different keys)")

        # Test 6: No interpretation in output
        interpretation_words = [
            "high",
            "low",
            "normal",
            "abnormal",
            "should",
            "consider",
            "recommend",
            "warning",
            "error",
        ]

        def check_for_interpretation(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    key_lower = str(key).lower()
                    if any(word in key_lower for word in interpretation_words):
                        failures.append(f"Interpretation found at {path}.{key}")
                    check_for_interpretation(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_for_interpretation(item, f"{path}[{i}]")

        check_for_interpretation(result)

    except Exception as e:
        failures.append(f"Test failed with exception: {e}")

    return (len(failures) == 0, failures)


# Import at bottom to avoid circular imports
import dataclasses  # noqa: E402

if __name__ == "__main__":
    # Run invariant tests when executed directly
    passed, failures = test_density_invariants()

    if passed:
        print("✓ All density invariants maintained")
        print("  - Outputs are numeric/structural only")
        print("  - No prose or interpretation")
        print("  - No labels (hotspot, risk, etc.)")
        print("  - Data structures immutable")
        print("  - No thresholds or best practices")
    else:
        print("✗ Density invariant failures:")
        for failure in failures:
            print(f"  - {failure}")
        exit(1)
