"""
Uncertainty quantification for CodeMarshal.

This module tracks what we cannot see, what we skipped, and what we might have missed.
It prevents the dangerous lie of silence - showing gaps as first-class outputs.
"""

import math
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, FrozenSet
import datetime

# Import from observations layer (allowed per architecture)
from observations.limitations.declared import DeclaredLimitation, SystemBlindSpot
from observations.limitations.validation import ValidationResult


class UncertaintyType(Enum):
    """Types of uncertainty in the system.
    
    Each type corresponds to a different kind of knowledge gap.
    """
    MISSING_FILE = auto()          # File exists but we couldn't read it
    UNSUPPORTED_LANGUAGE = auto()  # Language we don't understand
    BINARY_FILE = auto()           # Non-text file
    SIZE_LIMIT_EXCEEDED = auto()   # File too large to process
    PERMISSION_DENIED = auto()     # Insufficient permissions
    DECLARED_BLIND_SPOT = auto()   # Explicitly declared as not observable
    PARTIAL_PARSING = auto()       # Parsed but with errors
    TIMEOUT = auto()               # Operation took too long
    ENCODING_ERROR = auto()        # Could not decode file
    SYMBOLIC_LINK = auto()         # Skipped due to symlink policy


@dataclass(frozen=True)
class UncertaintyMeasurement:
    """Quantified measurement of uncertainty for a specific type.
    
    This is a numeric representation of what we don't know.
    """
    uncertainty_type: UncertaintyType
    count: int  # Number of occurrences
    total_possible: Optional[int] = None  # Denominator for ratio
    coverage_ratio: Optional[float] = None  # 0.0 to 1.0, computed if total_possible provided
    confidence_dampener: float  # Multiplier for downstream confidence (0.0 to 1.0)
    
    @property
    def missing_count(self) -> int:
        """If this is a coverage gap, how many items are missing."""
        if self.total_possible is not None and self.coverage_ratio is not None:
            missing = int((1.0 - self.coverage_ratio) * self.total_possible)
            return max(0, missing)
        return 0


@dataclass(frozen=True)
class FileCoverage:
    """Coverage statistics for files in a directory."""
    total_files_found: int
    files_analyzed: int
    files_skipped: int
    skipped_by_type: Dict[UncertaintyType, int]
    
    @property
    def coverage_ratio(self) -> float:
        """Ratio of analyzed files to total files found."""
        if self.total_files_found == 0:
            return 1.0  # Nothing to cover
        return self.files_analyzed / self.total_files_found
    
    @property
    def uncertainty_ratio(self) -> float:
        """Ratio of skipped files to total files found."""
        if self.total_files_found == 0:
            return 0.0  # No uncertainty if nothing exists
        return self.files_skipped / self.total_files_found


@dataclass(frozen=True)
class BlindSpotDescriptor:
    """Description of a declared system limitation.
    
    This makes blind spots explicit and quantifiable.
    """
    identifier: str
    limitation_type: str  # e.g., "language", "filesize", "structure"
    description: str
    impact_domain: Tuple[str, ...]  # What kinds of observations are affected
    confidence_reduction: float  # How much to reduce confidence in affected areas (0.0 to 1.0)
    
    def to_dict(self) -> Dict:
        """Convert to serializable dict."""
        return {
            'identifier': self.identifier,
            'limitation_type': self.limitation_type,
            'description': self.description,
            'impact_domain': list(self.impact_domain),
            'confidence_reduction': self.confidence_reduction
        }


class UncertaintyCalculator:
    """Calculates and quantifies uncertainty in observations.
    
    This class is epistemic honesty embodied - it makes unknowns explicit.
    All outputs are numeric or structural, never prose.
    """
    
    def __init__(self, declared_limitations: Tuple[DeclaredLimitation, ...]):
        """Initialize with declared system limitations."""
        self._limitations = declared_limitations
        self._blind_spots = self._extract_blind_spots(declared_limitations)
    
    def calculate_file_coverage(
        self,
        analyzed_files: Set[Path],
        skipped_files: Dict[Path, UncertaintyType],
        total_files_found: int
    ) -> FileCoverage:
        """Calculate coverage statistics for file analysis.
        
        Args:
            analyzed_files: Set of files that were successfully analyzed
            skipped_files: Dict mapping skipped files to reason
            total_files_found: Total number of files discovered
        
        Returns:
            FileCoverage object with numeric statistics
        """
        files_analyzed = len(analyzed_files)
        files_skipped = len(skipped_files)
        
        # Count skipped files by type
        skipped_by_type: Dict[UncertaintyType, int] = {}
        for file_type in skipped_files.values():
            skipped_by_type[file_type] = skipped_by_type.get(file_type, 0) + 1
        
        # Validate consistency
        if files_analyzed + files_skipped != total_files_found:
            # This is a data inconsistency - treat as uncertainty
            discrepancy = total_files_found - (files_analyzed + files_skipped)
            skipped_by_type[UncertaintyType.MISSING_FILE] = (
                skipped_by_type.get(UncertaintyType.MISSING_FILE, 0) + abs(discrepancy)
            )
        
        return FileCoverage(
            total_files_found=total_files_found,
            files_analyzed=files_analyzed,
            files_skipped=files_skipped,
            skipped_by_type=skipped_by_type
        )
    
    def calculate_uncertainty_measurements(
        self,
        coverage: FileCoverage,
        parsing_errors: Optional[int] = None,
        validation_results: Optional[ValidationResult] = None
    ) -> Tuple[UncertaintyMeasurement, ...]:
        """Calculate all uncertainty measurements from analysis results.
        
        Returns:
            Tuple of UncertaintyMeasurement objects, one for each uncertainty type
        """
        measurements: List[UncertaintyMeasurement] = []
        
        # File coverage uncertainty
        if coverage.total_files_found > 0:
            measurements.append(UncertaintyMeasurement(
                uncertainty_type=UncertaintyType.MISSING_FILE,
                count=coverage.files_skipped,
                total_possible=coverage.total_files_found,
                coverage_ratio=coverage.coverage_ratio,
                confidence_dampener=coverage.coverage_ratio
            ))
        
        # Per-type uncertainty from skipped files
        for uncertainty_type, count in coverage.skipped_by_type.items():
            measurements.append(UncertaintyMeasurement(
                uncertainty_type=uncertainty_type,
                count=count,
                total_possible=coverage.total_files_found,
                coverage_ratio=None,
                confidence_dampener=0.5  # Medium confidence reduction for specific skips
            ))
        
        # Parsing uncertainty (if available)
        if parsing_errors is not None:
            # Estimate total possible parsing operations
            # This is approximate - actual number could be higher
            estimated_parses = coverage.files_analyzed
            if estimated_parses > 0:
                measurements.append(UncertaintyMeasurement(
                    uncertainty_type=UncertaintyType.PARTIAL_PARSING,
                    count=parsing_errors,
                    total_possible=estimated_parses,
                    coverage_ratio=1.0 - (parsing_errors / estimated_parses),
                    confidence_dampener=0.7  # Moderate reduction for parsing issues
                ))
        
        # Validation uncertainty (if available)
        if validation_results is not None:
            # Add validation-related uncertainty
            if validation_results.invalid_count > 0:
                measurements.append(UncertaintyMeasurement(
                    uncertainty_type=UncertaintyType.PARTIAL_PARSING,
                    count=validation_results.invalid_count,
                    total_possible=validation_results.total_count,
                    coverage_ratio=validation_results.valid_ratio,
                    confidence_dampener=validation_results.valid_ratio
                ))
        
        return tuple(measurements)
    
    def calculate_confidence_score(
        self,
        measurements: Tuple[UncertaintyMeasurement, ...],
        base_confidence: float = 1.0
    ) -> float:
        """Calculate overall confidence score from uncertainty measurements.
        
        This is a numeric indicator of how much we can trust the observations.
        Multiplicative approach ensures each uncertainty reduces confidence.
        
        Args:
            measurements: Uncertainty measurements to incorporate
            base_confidence: Starting confidence (1.0 = perfect)
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = base_confidence
        
        for measurement in measurements:
            # Multiply by dampener (already scaled 0.0-1.0)
            confidence *= measurement.confidence_dampener
        
        # Apply blind spot reductions
        for blind_spot in self._blind_spots:
            confidence *= (1.0 - blind_spot.confidence_reduction)
        
        return max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
    
    def get_blind_spots(self) -> Tuple[BlindSpotDescriptor, ...]:
        """Get all declared blind spots as descriptors."""
        return self._blind_spots
    
    def _extract_blind_spots(
        self, 
        limitations: Tuple[DeclaredLimitation, ...]
    ) -> Tuple[BlindSpotDescriptor, ...]:
        """Convert declared limitations to blind spot descriptors."""
        descriptors: List[BlindSpotDescriptor] = []
        
        for limitation in limitations:
            descriptor = BlindSpotDescriptor(
                identifier=limitation.identifier,
                limitation_type=limitation.category,
                description=limitation.description,
                impact_domain=tuple(limitation.affected_operations),
                confidence_reduction=limitation.confidence_impact
            )
            descriptors.append(descriptor)
        
        return tuple(descriptors)
    
    def generate_coverage_report(
        self,
        coverage: FileCoverage,
        measurements: Tuple[UncertaintyMeasurement, ...]
    ) -> Dict:
        """Generate structural coverage report without prose.
        
        Returns:
            Dict with numeric coverage data, suitable for programmatic use
        """
        # Calculate summary statistics
        total_uncertainty_items = sum(m.count for m in measurements)
        avg_confidence_dampener = (
            sum(m.confidence_dampener for m in measurements) / len(measurements)
            if measurements else 1.0
        )
        
        # Group measurements by type for easier consumption
        measurements_by_type: Dict[str, List[Dict]] = {}
        for measurement in measurements:
            type_name = measurement.uncertainty_type.name.lower()
            measurements_by_type.setdefault(type_name, []).append({
                'count': measurement.count,
                'total_possible': measurement.total_possible,
                'coverage_ratio': measurement.coverage_ratio,
                'confidence_dampener': measurement.confidence_dampener,
                'missing_count': measurement.missing_count
            })
        
        return {
            'file_coverage': {
                'total_files': coverage.total_files_found,
                'analyzed': coverage.files_analyzed,
                'skipped': coverage.files_skipped,
                'coverage_ratio': coverage.coverage_ratio,
                'uncertainty_ratio': coverage.uncertainty_ratio
            },
            'uncertainty_measurements': {
                'total_items': total_uncertainty_items,
                'by_type': measurements_by_type,
                'average_confidence_dampener': avg_confidence_dampener
            },
            'blind_spots': [spot.to_dict() for spot in self._blind_spots],
            'computed_at': datetime.datetime.now(datetime.timezone.utc).isoformat()
        }


def detect_missing_files(
    expected_files: Set[Path],
    analyzed_files: Set[Path]
) -> Tuple[Path, ...]:
    """Detect files that were expected but not analyzed.
    
    Returns:
        Tuple of missing file paths
    """
    missing = expected_files - analyzed_files
    return tuple(sorted(missing))


def calculate_uncertainty_metrics(
    analyzed_files: Set[Path],
    skipped_files: Dict[Path, UncertaintyType],
    total_files_found: int,
    declared_limitations: Optional[List[Dict]] = None,
    parsing_error_count: Optional[int] = None,
    validation_results: Optional[Dict] = None
) -> Dict:
    """Main uncertainty calculation function for pattern registry.
    
    This is the function that will be registered in patterns/__init__.py.
    
    Returns:
        Dict with numeric uncertainty metrics only
    """
    # Convert declared limitations
    limitations: List[DeclaredLimitation] = []
    if declared_limitations:
        for lim_dict in declared_limitations:
            try:
                limitation = DeclaredLimitation(
                    identifier=lim_dict['identifier'],
                    category=lim_dict['category'],
                    description=lim_dict['description'],
                    affected_operations=tuple(lim_dict.get('affected_operations', [])),
                    confidence_impact=lim_dict.get('confidence_impact', 0.1)
                )
                limitations.append(limitation)
            except (KeyError, TypeError):
                # Invalid limitation spec - skip it
                continue
    
    # Create calculator
    calculator = UncertaintyCalculator(tuple(limitations))
    
    # Calculate coverage
    coverage = calculator.calculate_file_coverage(
        analyzed_files, 
        skipped_files, 
        total_files_found
    )
    
    # Convert validation results if provided
    validation_result_obj: Optional[ValidationResult] = None
    if validation_results:
        validation_result_obj = ValidationResult(
            valid_count=validation_results.get('valid_count', 0),
            invalid_count=validation_results.get('invalid_count', 0),
            skipped_count=validation_results.get('skipped_count', 0),
            errors=tuple(validation_results.get('errors', []))
        )
    
    # Calculate uncertainty measurements
    measurements = calculator.calculate_uncertainty_measurements(
        coverage,
        parsing_error_count,
        validation_result_obj
    )
    
    # Calculate confidence score
    confidence_score = calculator.calculate_confidence_score(measurements)
    
    # Generate report
    report = calculator.generate_coverage_report(coverage, measurements)
    
    # Add confidence score to report
    report['confidence_score'] = confidence_score
    
    # Add missing files detection
    missing_files = detect_missing_files(
        set(skipped_files.keys()) | analyzed_files,  # All files we know about
        analyzed_files
    )
    report['missing_files'] = [str(p) for p in missing_files]
    report['missing_file_count'] = len(missing_files)
    
    return report


def validate_uncertainty_data(data: Dict) -> Tuple[bool, List[str]]:
    """Validate that uncertainty data maintains invariants.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors: List[str] = []
    
    # Check required structure
    required_sections = ['file_coverage', 'uncertainty_measurements', 'confidence_score']
    for section in required_sections:
        if section not in data:
            errors.append(f"Missing required section: {section}")
    
    # Check file_coverage types
    if 'file_coverage' in data:
        coverage = data['file_coverage']
        required_fields = ['total_files', 'analyzed', 'skipped', 'coverage_ratio']
        for field in required_fields:
            if field not in coverage:
                errors.append(f"Missing coverage field: {field}")
            elif not isinstance(coverage[field], (int, float)):
                errors.append(f"Coverage field {field} must be numeric")
    
    # Check confidence score range
    confidence = data.get('confidence_score', 1.0)
    if not isinstance(confidence, (int, float)):
        errors.append("Confidence score must be numeric")
    elif confidence < 0.0 or confidence > 1.0:
        errors.append(f"Confidence score out of range: {confidence}")
    
    # Check for prose in data
    prose_fields = ['recommendation', 'advice', 'suggestion', 'should', 'could']
    def check_for_prose(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if any(prose in key.lower() for prose in prose_fields):
                    errors.append(f"Prose-like field at {path}.{key}")
                check_for_prose(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_for_prose(item, f"{path}[{i}]")
    
    check_for_prose(data)
    
    return (len(errors) == 0, errors)


# Test function to verify invariants
def test_uncertainty_invariants() -> Tuple[bool, List[str]]:
    """Test that the module maintains its invariants.
    
    Returns:
        Tuple of (all_passed, list_of_failed_tests)
    """
    failures: List[str] = []
    
    try:
        # Test 1: All outputs are numeric or structural
        test_files = {Path("test.py")}
        test_skipped = {Path("binary.bin"): UncertaintyType.BINARY_FILE}
        
        result = calculate_uncertainty_metrics(
            analyzed_files=test_files,
            skipped_files=test_skipped,
            total_files_found=2
        )
        
        # Check structure
        if not isinstance(result, dict):
            failures.append("Result should be dict")
        
        # Check numeric fields
        coverage = result.get('file_coverage', {})
        if not isinstance(coverage.get('coverage_ratio'), float):
            failures.append("Coverage ratio should be float")
        
        if not isinstance(result.get('confidence_score'), float):
            failures.append("Confidence score should be float")
        
        # Test 2: No prose in outputs
        is_valid, errors = validate_uncertainty_data(result)
        if not is_valid:
            failures.extend(errors)
        
        # Test 3: Confidence bounded [0, 1]
        confidence = result['confidence_score']
        if confidence < 0.0 or confidence > 1.0:
            failures.append(f"Confidence score {confidence} out of bounds")
        
        # Test 4: Immutable data structures
        calculator = UncertaintyCalculator(())
        coverage_obj = calculator.calculate_file_coverage(
            test_files, test_skipped, 2
        )
        
        # Try to modify (should fail for frozen dataclass)
        try:
            coverage_obj.total_files_found = 3  # type: ignore
            failures.append("FileCoverage should be immutable")
        except (AttributeError, dataclasses.FrozenInstanceError):
            pass  # Expected
        
        # Test 5: Deterministic outputs
        result1 = calculate_uncertainty_metrics(test_files, test_skipped, 2)
        result2 = calculate_uncertainty_metrics(test_files, test_skipped, 2)
        
        import json
        if json.dumps(result1, sort_keys=True) != json.dumps(result2, sort_keys=True):
            failures.append("Results not deterministic")
        
    except Exception as e:
        failures.append(f"Test failed with exception: {e}")
    
    return (len(failures) == 0, failures)


# Import at bottom to avoid circular imports
import dataclasses

if __name__ == '__main__':
    # Run invariant tests when executed directly
    passed, failures = test_uncertainty_invariants()
    
    if passed:
        print("✓ All uncertainty invariants maintained")
        print("  - Outputs are numeric/structural only")
        print("  - No prose or interpretation")
        print("  - Confidence scores bounded [0, 1]")
        print("  - Data structures immutable")
        print("  - Results deterministic")
    else:
        print("✗ Uncertainty invariant failures:")
        for failure in failures:
            print(f"  - {failure}")
        exit(1)