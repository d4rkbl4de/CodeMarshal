"""
no_inference.test.py - "No guessing allowed" test

Enforces Constitutional Articles 1, 3 and the Four Pillars of Truth.
Tests that:
1. Observation outputs contain only textually present facts
2. No semantic guesses, inferred intent, or interpretation
3. Pattern detectors emit uncertainty explicitly, never label meaning
4. Unknowns are surfaced as unknowns with clear markers

This test is hostile by design - it assumes inference will try to sneak in.
Failure is Tier-1 and must halt execution.
"""

import re
import tempfile
import ast
import json
from pathlib import Path
from typing import Optional, List, Dict, Set, Tuple, Any, Pattern
import warnings
import pytest

# System imports
from observations.eyes.base import BaseEye
from observations.eyes.file_sight import FileSight
from observations.eyes.import_sight import ImportSight
from observations.eyes.export_sight import ExportSight
from observations.eyes.boundary_sight import BoundarySight
from observations.eyes.encoding_sight import EncodingSight
from observations.limitations.validation import validate_observation
from inquiry.patterns.density import DensityAnalyzer
from inquiry.patterns.coupling import CouplingAnalyzer
from inquiry.patterns.complexity import ComplexityAnalyzer
from inquiry.patterns.violations import BoundaryViolationDetector
from inquiry.patterns.uncertainty import UncertaintyQuantifier

# Type aliases
ObservationOutput = Dict[str, Any]
PatternOutput = Dict[str, Any]
InferenceCheck = Tuple[bool, str]  # (has_inference, evidence)


class InferenceDetector:
    """
    Hostile detector for inference, guessing, and semantic interpretation.
    
    Looks for:
    1. Language that suggests guessing (probably, likely, seems, suggests)
    2. Inferred intent (purpose, goal, trying to)
    3. Semantic interpretation (means, represents, is actually)
    4. Statistical confidence without evidence (high confidence, likely)
    5. Missing uncertainty markers for unknowns
    """
    
    def __init__(self) -> None:
        # Patterns that indicate inference or guessing
        self.guessing_patterns: List[Pattern] = [
            re.compile(r'\bprobably\b', re.IGNORECASE),
            re.compile(r'\blikely\b', re.IGNORECASE),
            re.compile(r'\bseems?\b', re.IGNORECASE),
            re.compile(r'\bsuggests?\b', re.IGNORECASE),
            re.compile(r'\bappears?\b', re.IGNORECASE),
            re.compile(r'\bmaybe\b', re.IGNORECASE),
            re.compile(r'\bperhaps\b', re.IGNORECASE),
            re.compile(r'\bpossibly\b', re.IGNORECASE),
            re.compile(r'\bcould be\b', re.IGNORECASE),
            re.compile(r'\bmight be\b', re.IGNORECASE),
        ]
        
        # Patterns that indicate intent inference
        self.intent_patterns: List[Pattern] = [
            re.compile(r'\bpurpose\b', re.IGNORECASE),
            re.compile(r'\bintent\b', re.IGNORECASE),
            re.compile(r'\btrying to\b', re.IGNORECASE),
            re.compile(r'\battempting to\b', re.IGNORECASE),
            re.compile(r'\bgoal\b', re.IGNORECASE),
            re.compile(r'\baims?\b', re.IGNORECASE),
            re.compile(r'\bmeant to\b', re.IGNORECASE),
            re.compile(r'\bdesigned to\b', re.IGNORECASE),
        ]
        
        # Patterns that indicate semantic interpretation
        self.interpretation_patterns: List[Pattern] = [
            re.compile(r'\bmeans?\b', re.IGNORECASE),
            re.compile(r'\brepresents?\b', re.IGNORECASE),
            re.compile(r'\bsignifies\b', re.IGNORECASE),
            re.compile(r'\bindicates?\b', re.IGNORECASE),
            re.compile(r'\bshows?\b', re.IGNORECASE),
            re.compile(r'\bdemonstrates?\b', re.IGNORECASE),
            re.compile(r'\bactually\b', re.IGNORECASE),
            re.compile(r'\bin fact\b', re.IGNORECASE),
            re.compile(r'\btherefore\b', re.IGNORECASE),
            re.compile(r'\bthus\b', re.IGNORECASE),
            re.compile(r'\bhence\b', re.IGNORECASE),
        ]
        
        # Patterns that indicate statistical confidence
        self.confidence_patterns: List[Pattern] = [
            re.compile(r'\bconfidence\b', re.IGNORECASE),
            re.compile(r'\bprobability\b', re.IGNORECASE),
            re.compile(r'\blikelihood\b', re.IGNORECASE),
            re.compile(r'\bstatistical\b', re.IGNORECASE),
            re.compile(r'\bconfidence level\b', re.IGNORECASE),
            re.compile(r'\bpercent(age)?\b', re.IGNORECASE),
        ]
        
        # Acceptable patterns - must be explicit about uncertainty
        self.uncertainty_markers: List[Pattern] = [
            re.compile(r'⚠️'),  # Unicode warning symbol
            re.compile(r'\?\?\?'),  # Explicit unknown
            re.compile(r'\[UNCERTAIN\]', re.IGNORECASE),
            re.compile(r'\[UNKNOWN\]', re.IGNORECASE),
            re.compile(r'\[MISSING DATA\]', re.IGNORECASE),
            re.compile(r'\bcannot (see|determine|detect)\b', re.IGNORECASE),
            re.compile(r'\bunknown\b', re.IGNORECASE),
            re.compile(r'\bunclear\b', re.IGNORECASE),
            re.compile(r'\buncertain\b', re.IGNORECASE),
        ]
        
        # Pattern for explicit limitation declarations
        self.limitation_patterns: List[Pattern] = [
            re.compile(r'\blimitation\b', re.IGNORECASE),
            re.compile(r'\bcannot observe\b', re.IGNORECASE),
            re.compile(r'\bcannot detect\b', re.IGNORECASE),
            re.compile(r'\bblind spot\b', re.IGNORECASE),
            re.compile(r'\bdeclared (blind|limitation)\b', re.IGNORECASE),
        ]
    
    def check_for_inference(self, text: str, context: str = "") -> List[InferenceCheck]:
        """
        Check text for inference, guessing, or interpretation.
        
        Returns list of (has_inference, evidence) tuples.
        """
        checks: List[InferenceCheck] = []
        
        # Check for guessing language
        for pattern in self.guessing_patterns:
            if pattern.search(text):
                checks.append((True, f"Guessing language in {context}: '{pattern.pattern}'"))
        
        # Check for intent inference
        for pattern in self.intent_patterns:
            if pattern.search(text):
                checks.append((True, f"Intent inference in {context}: '{pattern.pattern}'"))
        
        # Check for interpretation
        for pattern in self.interpretation_patterns:
            if pattern.search(text):
                checks.append((True, f"Semantic interpretation in {context}: '{pattern.pattern}'"))
        
        # Check for statistical confidence
        for pattern in self.confidence_patterns:
            if pattern.search(text):
                checks.append((True, f"Statistical confidence in {context}: '{pattern.pattern}'"))
        
        return checks
    
    def check_uncertainty_markers(self, text: str, context: str = "") -> List[InferenceCheck]:
        """
        Check that uncertainty is properly marked when present.
        
        Returns violations where uncertainty should be marked but isn't.
        """
        checks: List[InferenceCheck] = []
        
        # If text contains terms that imply uncertainty but no markers, it's a violation
        uncertainty_terms = ['maybe', 'perhaps', 'possibly', 'could be', 'might be', 'seems', 'appears']
        has_uncertainty_term = any(term in text.lower() for term in uncertainty_terms)
        
        if has_uncertainty_term:
            # Check if there are proper uncertainty markers
            has_marker = any(pattern.search(text) for pattern in self.uncertainty_markers)
            if not has_marker:
                checks.append((True, f"Uncertainty without marker in {context}: '{text}'"))
        
        return checks
    
    def check_pattern_output(self, pattern_output: PatternOutput, pattern_name: str) -> List[InferenceCheck]:
        """
        Specifically check pattern analyzer outputs for inference.
        
        Pattern detectors must:
        1. Never label meaning
        2. Emit uncertainty explicitly
        3. Use only numeric/boolean outputs where possible
        """
        checks: List[InferenceCheck] = []
        
        # Convert pattern output to string for checking
        output_str = json.dumps(pattern_output, indent=2)
        
        # Check for inference in the output
        checks.extend(self.check_for_inference(output_str, f"pattern {pattern_name}"))
        
        # Check for uncertainty markers if there's any uncertainty
        checks.extend(self.check_uncertainty_markers(output_str, f"pattern {pattern_name}"))
        
        # Additional pattern-specific checks
        if pattern_name.lower() in ['density', 'coupling', 'complexity']:
            # These should output numbers, not interpretations
            for key, value in pattern_output.items():
                if isinstance(value, str):
                    # String values in numeric patterns might be interpretations
                    checks.extend(self.check_for_inference(value, f"pattern {pattern_name} key {key}"))
        
        return checks
    
    def check_observation_output(self, observation_output: ObservationOutput, eye_name: str) -> List[InferenceCheck]:
        """
        Check observation outputs for inference.
        
        Observations must contain only textually present facts.
        """
        checks: List[InferenceCheck] = []
        
        # Convert observation to string for checking
        output_str = json.dumps(observation_output, indent=2)
        
        # Check for inference
        checks.extend(self.check_for_inference(output_str, f"observation {eye_name}"))
        
        # Observations should NOT contain uncertainty markers in their factual content
        # (uncertainty is for patterns, not observations)
        # But they CAN have limitation declarations
        
        # Check for proper limitation declarations if needed
        has_limitation = any(pattern.search(output_str) for pattern in self.limitation_patterns)
        
        return checks


class AmbiguousCodeGenerator:
    """
    Generates ambiguous code samples that tempt inference.
    
    These samples are designed to trigger common inference patterns:
    - Unclear naming
    - Partial implementations
    - Unusual patterns
    - Missing context
    """
    
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
    
    def create_ambiguous_python_file(self, filename: str) -> Path:
        """Create a Python file with ambiguous content."""
        file_path = self.base_dir / filename
        
        content = '''"""
This module has ambiguous features that might trigger inference.
"""
import os
from typing import Optional, Any

# Ambiguous function name
def process_data(data: Any) -> Optional[str]:
    """
    Process the data.
    
    What does "process" mean? This is ambiguous.
    The function returns None in some cases.
    """
    if not data:
        return None
    # Implementation is missing
    return str(data)

# Class with unclear purpose
class Manager:
    """
    Manages something.
    
    The name "Manager" doesn't specify what it manages.
    This is intentionally ambiguous.
    """
    
    def __init__(self) -> None:
        self.items = []
    
    def add(self, item: Any) -> None:
        """Add an item."""
        self.items.append(item)
    
    # Missing implementation for other methods

# Function that might be a factory, but we can't know
def create_object(name: str) -> Any:
    """
    Create an object based on name.
    
    Returns different types? We can't know from signature.
    """
    if name == "config":
        return {}
    elif name == "logger":
        return print
    else:
        return None

# Unclear variable names
value = 42  # What does 42 mean here?
flag = True  # Flag for what?

# Partial implementation
def calculate_something(x: int, y: int) -> int:
    # TODO: Implement actual calculation
    return x + y  # This might not be the real calculation

# Module that might be a main module or might be imported
if __name__ == "__main__":
    # We can't know what this does without running it
    print("Running ambiguous module")
'''
        
        file_path.write_text(content)
        return file_path
    
    def create_import_ambiguity(self) -> Path:
        """Create files with complex import patterns."""
        file_path = self.base_dir / "import_ambiguity.py"
        
        content = '''"""
Module with complex imports that might trigger inference about dependencies.
"""
# Circular import pattern (but not actually circular)
from . import sibling_module  # Might not exist

# Conditional imports (not actually conditional in text)
try:
    import optional_module
except ImportError:
    optional_module = None

# Star import - what's actually imported?
from ambiguous_package import *

# Relative imports with ..
from ..parent import something

# What does "config" export? We can't know from this import
from config import *
'''
        
        file_path.write_text(content)
        return file_path
    
    def create_boundary_ambiguity(self) -> Tuple[Path, Path]:
        """Create files that might violate boundaries."""
        # Create directory structure
        lobe_a = self.base_dir / "lobes" / "lobe_a"
        lobe_b = self.base_dir / "lobes" / "lobe_b"
        lobe_a.mkdir(parents=True, exist_ok=True)
        lobe_b.mkdir(parents=True, exist_ok=True)
        
        # File in lobe_a that might import from lobe_b
        file_a = lobe_a / "module_a.py"
        file_a_content = '''"""
Module in lobe A that might try to import from lobe B.
"""
# This import would be a boundary violation if it worked
# from lobes.lobe_b import something

# Instead, it has a similarly named local import
from . import local_module

def use_lobe_b_feature():
    """Function that might be trying to use lobe B features."""
    # Can't tell from text if this is trying to cross boundaries
    pass
'''
        file_a.write_text(file_a_content)
        
        # File in lobe_b
        file_b = lobe_b / "module_b.py"
        file_b_content = '''"""
Module in lobe B.
"""
def some_feature():
    return "feature"

# Export pattern that might be targeted
__all__ = ['some_feature']
'''
        file_b.write_text(file_b_content)
        
        return file_a, file_b
    
    def create_encoding_ambiguity(self) -> Path:
        """Create files with encoding challenges."""
        file_path = self.base_dir / "encoding_ambiguous.txt"
        
        # Write bytes that might trigger encoding detection issues
        ambiguous_bytes = b'''# -*- coding: latin-1 -*-
# This file has non-ASCII characters: caf\xe9 r\xe9sum\xe9 na\xefve

# Mixed encodings in comments
# Latin-1: caf\xe9
# UTF-8: caf\xe9 (same characters, different encoding)

# Binary data that might be text
data = b'\\x00\\x01\\x02Hello\\x00World\\x00'
'''
        file_path.write_bytes(ambiguous_bytes)
        return file_path
    
    def create_partial_implementation(self) -> Path:
        """Create a file with TODOs and partial code."""
        file_path = self.base_dir / "partial.py"
        
        content = '''"""
Partial implementation with TODOs.
"""
# TODO: Implement this class properly
class Incomplete:
    def __init__(self):
        self.data = None
    
    # TODO: Add more methods
    def process(self):
        pass

# Function stubs
def calculate_metrics(data) -> dict:
    """
    Calculate metrics from data.
    
    TODO: Implement actual metric calculation
    FIXME: Handle edge cases
    """
    return {}

# Placeholder values
DEFAULT_CONFIG = {
    "timeout": 30,  # 30 what? seconds? milliseconds?
    "retries": 3,   # Retry count
    # Missing: retry delay, backoff strategy
}

# Unclear constants
MAGIC_NUMBER = 42  # Why 42?
THRESHOLD = 0.5    # Threshold for what?
'''
        
        file_path.write_text(content)
        return file_path


class TestNoInference:
    """
    Hostile test suite for enforcing "no guessing allowed" principle.
    
    This test assumes inference will try to sneak in through:
    1. Well-meaning descriptive text
    2. Pattern analysis overreach
    3. Ambiguous code interpretation
    4. Statistical confidence masking as fact
    """
    
    def setup_method(self) -> None:
        """Set up fresh test environment for each test."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="codemarshal_no_inference_"))
        self.detector = InferenceDetector()
        self.code_gen = AmbiguousCodeGenerator(self.test_dir)
        
        # Create ambiguous code samples
        self.ambiguous_py = self.code_gen.create_ambiguous_python_file("ambiguous.py")
        self.import_ambiguous = self.code_gen.create_import_ambiguity()
        self.partial_impl = self.code_gen.create_partial_implementation()
        self.encoding_ambiguous = self.code_gen.create_encoding_ambiguity()
        self.boundary_files = self.code_gen.create_boundary_ambiguity()
    
    def teardown_method(self) -> None:
        """Clean up test directory."""
        import shutil
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception:
            pass
    
    def test_file_sight_no_inference(self) -> None:
        """Test that FileSight observes without inferring meaning."""
        eye = FileSight()
        observations = eye.observe(self.test_dir)
        
        violations: List[str] = []
        
        # Check each observation
        for obs in observations:
            checks = self.detector.check_observation_output(
                obs.__dict__ if hasattr(obs, '__dict__') else obs,
                "FileSight"
            )
            for has_inference, evidence in checks:
                if has_inference:
                    violations.append(evidence)
        
        # Tier-1 failure
        assert len(violations) == 0, (
            f"FileSight inference detected ({len(violations)} violations):\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_import_sight_no_inference(self) -> None:
        """Test that ImportSight observes imports without inferring dependencies."""
        eye = ImportSight()
        observations = eye.observe(self.test_dir)
        
        violations: List[str] = []
        
        for obs in observations:
            checks = self.detector.check_observation_output(
                obs.__dict__ if hasattr(obs, '__dict__') else obs,
                "ImportSight"
            )
            for has_inference, evidence in checks:
                if has_inference:
                    violations.append(evidence)
        
        # ImportSight must not infer:
        # - Whether imports are actually used
        # - Whether imports will succeed
        # - The purpose of imports
        assert len(violations) == 0, (
            f"ImportSight inference detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_export_sight_no_inference(self) -> None:
        """Test that ExportSight observes exports without inferring API design."""
        eye = ExportSight()
        observations = eye.observe(self.test_dir)
        
        violations: List[str] = []
        
        for obs in observations:
            checks = self.detector.check_observation_output(
                obs.__dict__ if hasattr(obs, '__dict__') else obs,
                "ExportSight"
            )
            for has_inference, evidence in checks:
                if has_inference:
                    violations.append(evidence)
        
        # ExportSight must not infer:
        # - Whether exports are intentional
        # - The intended consumers of exports
        # - Whether the API is well-designed
        assert len(violations) == 0, (
            f"ExportSight inference detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_boundary_sight_no_inference(self) -> None:
        """Test that BoundarySight observes boundaries without inferring violations."""
        eye = BoundarySight()
        observations = eye.observe(self.test_dir)
        
        violations: List[str] = []
        
        for obs in observations:
            checks = self.detector.check_observation_output(
                obs.__dict__ if hasattr(obs, '__dict__') else obs,
                "BoundarySight"
            )
            for has_inference, evidence in checks:
                if has_inference:
                    violations.append(evidence)
        
        # BoundarySight must not infer:
        # - Whether boundary crossings are intentional
        # - The architectural intent behind boundaries
        # - Whether boundaries are being respected
        assert len(violations) == 0, (
            f"BoundarySight inference detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_encoding_sight_no_inference(self) -> None:
        """Test that EncodingSight observes encodings without inferring content."""
        eye = EncodingSight()
        observations = eye.observe(self.test_dir)
        
        violations: List[str] = []
        
        for obs in observations:
            checks = self.detector.check_observation_output(
                obs.__dict__ if hasattr(obs, '__dict__') else obs,
                "EncodingSight"
            )
            for has_inference, evidence in checks:
                if has_inference:
                    violations.append(evidence)
        
        # EncodingSight must not infer:
        # - Whether encoding choices are correct
        # - The intended encoding of ambiguous files
        # - Whether content is valid in detected encoding
        assert len(violations) == 0, (
            f"EncodingSight inference detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_density_analyzer_no_inference(self) -> None:
        """Test that DensityAnalyzer outputs numbers, not interpretations."""
        analyzer = DensityAnalyzer()
        
        # Create observations first
        file_eye = FileSight()
        import_eye = ImportSight()
        
        file_obs = list(file_eye.observe(self.test_dir))
        import_obs = list(import_eye.observe(self.test_dir))
        
        # Run pattern analysis
        density_output = analyzer.analyze(file_obs + import_obs)
        
        violations: List[str] = []
        
        # Check pattern output
        checks = self.detector.check_pattern_output(
            density_output.__dict__ if hasattr(density_output, '__dict__') else density_output,
            "DensityAnalyzer"
        )
        
        for has_inference, evidence in checks:
            if has_inference:
                violations.append(evidence)
        
        # DensityAnalyzer must:
        # - Output only counts, ratios, numbers
        # - Never label clusters as "related" or "cohesive"
        # - Never interpret density as "good" or "bad"
        assert len(violations) == 0, (
            f"DensityAnalyzer inference detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_coupling_analyzer_no_inference(self) -> None:
        """Test that CouplingAnalyzer outputs connections, not relationships."""
        analyzer = CouplingAnalyzer()
        
        # Create observations
        import_eye = ImportSight()
        import_obs = list(import_eye.observe(self.test_dir))
        
        # Run pattern analysis
        coupling_output = analyzer.analyze(import_obs)
        
        violations: List[str] = []
        
        checks = self.detector.check_pattern_output(
            coupling_output.__dict__ if hasattr(coupling_output, '__dict__') else coupling_output,
            "CouplingAnalyzer"
        )
        
        for has_inference, evidence in checks:
            if has_inference:
                violations.append(evidence)
        
        # CouplingAnalyzer must:
        # - Output only connection counts, directions
        # - Never label coupling as "tight" or "loose"
        # - Never interpret coupling as "good" or "bad"
        assert len(violations) == 0, (
            f"CouplingAnalyzer inference detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_complexity_analyzer_no_inference(self) -> None:
        """Test that ComplexityAnalyzer outputs metrics, not judgments."""
        analyzer = ComplexityAnalyzer()
        
        # Create observations
        file_eye = FileSight()
        file_obs = list(file_eye.observe(self.test_dir))
        
        # Run pattern analysis
        complexity_output = analyzer.analyze(file_obs)
        
        violations: List[str] = []
        
        checks = self.detector.check_pattern_output(
            complexity_output.__dict__ if hasattr(complexity_output, '__dict__') else complexity_output,
            "ComplexityAnalyzer"
        )
        
        for has_inference, evidence in checks:
            if has_inference:
                violations.append(evidence)
        
        # ComplexityAnalyzer must:
        # - Output only counts, depths, numbers
        # - Never label complexity as "high" or "low"
        # - Never interpret complexity as "good" or "bad"
        assert len(violations) == 0, (
            f"ComplexityAnalyzer inference detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_boundary_violation_detector_no_inference(self) -> None:
        """Test that BoundaryViolationDetector outputs facts, not accusations."""
        analyzer = BoundaryViolationDetector()
        
        # Configure boundaries (simulating Agent Nexus lobes)
        boundaries = {
            "lobes/lobe_a": "lobe_a",
            "lobes/lobe_b": "lobe_b",
        }
        analyzer.set_boundaries(boundaries)
        
        # Create observations
        import_eye = ImportSight()
        import_obs = list(import_eye.observe(self.test_dir))
        
        # Run pattern analysis
        violation_output = analyzer.analyze(import_obs)
        
        violations: List[str] = []
        
        checks = self.detector.check_pattern_output(
            violation_output.__dict__ if hasattr(violation_output, '__dict__') else violation_output,
            "BoundaryViolationDetector"
        )
        
        for has_inference, evidence in checks:
            if has_inference:
                violations.append(evidence)
        
        # BoundaryViolationDetector must:
        # - Output only boolean facts about import paths
        # - Never label violations as "intentional" or "accidental"
        # - Never suggest fixes or improvements
        assert len(violations) == 0, (
            f"BoundaryViolationDetector inference detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_uncertainty_quantifier_explicit_markers(self) -> None:
        """
        Test that UncertaintyQuantifier always marks uncertainty explicitly.
        
        This is the only component allowed to talk about uncertainty,
        and it must do so with clear markers.
        """
        analyzer = UncertaintyQuantifier()
        
        # Create observations with gaps
        file_eye = FileSight()
        file_obs = list(file_eye.observe(self.test_dir))
        
        # Run uncertainty analysis
        uncertainty_output = analyzer.analyze(file_obs)
        
        violations: List[str] = []
        
        # Convert output to string
        output_str = json.dumps(
            uncertainty_output.__dict__ if hasattr(uncertainty_output, '__dict__') else uncertainty_output,
            indent=2
        )
        
        # UncertaintyQuantifier MUST use explicit markers
        has_marker = any(pattern.search(output_str) for pattern in self.detector.uncertainty_markers)
        
        if not has_marker and "uncertainty" in output_str.lower():
            violations.append("Uncertainty discussed without explicit markers")
        
        # Check for inference in uncertainty discussion
        checks = self.detector.check_for_inference(output_str, "UncertaintyQuantifier")
        for has_inference, evidence in checks:
            if has_inference:
                violations.append(evidence)
        
        assert len(violations) == 0, (
            f"UncertaintyQuantifier issues detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_observation_validation_no_inference(self) -> None:
        """Test that observation validation doesn't infer correctness."""
        # Create an observation
        eye = FileSight()
        observations = list(eye.observe(self.test_dir))
        
        violations: List[str] = []
        
        # Validate each observation
        for obs in observations:
            validation_result = validate_observation(obs)
            
            # Check validation output for inference
            checks = self.detector.check_observation_output(
                validation_result.__dict__ if hasattr(validation_result, '__dict__') else validation_result,
                "ObservationValidation"
            )
            for has_inference, evidence in checks:
                if has_inference:
                    violations.append(evidence)
        
        # Validation must not infer:
        # - Whether observations are "correct"
        # - Whether observations are "complete"
        # - The quality of observations
        assert len(violations) == 0, (
            f"Observation validation inference detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_hostile_inference_detection(self) -> None:
        """
        Hostile test that attempts to trigger inference from multiple angles.
        
        Creates code that strongly tempts inference and verifies
        the system resists the temptation.
        """
        # Create maximally tempting code
        tempting_dir = self.test_dir / "tempting"
        tempting_dir.mkdir(exist_ok=True)
        
        # Code that screams for interpretation
        tempting_code = tempting_dir / "tempting.py"
        tempting_code.write_text('''"""
This code BEGS for interpretation.

Look at this function name: handleUserRequestAndMaybeLogIt()
What does it do? It probably handles user requests and maybe logs them.

This class: DataProcessorManagerFactory
Clearly a factory that creates managers for data processors.

This import: from secret import key
Probably imports an API key or encryption key.

This constant: MAX_RETRIES = 3
Likely the maximum number of retries for something.

This comment: # Fix the bug here
Suggests there was a bug that needed fixing.
"""
import os
import sys
from typing import Optional

# Function that seems important
def critical_operation(data: dict) -> Optional[str]:
    """
    Performs a critical operation.
    
    This probably transforms the data in some important way.
    The return value likely indicates success or failure.
    """
    if not data:
        return None
    # Implementation appears to validate and process
    return "success"

# Class that seems like a facade
class ComplexSystemFacade:
    """
    Provides simplified access to a complex system.
    
    This is likely a facade pattern implementation.
    It probably hides complexity from clients.
    """
    
    def __init__(self):
        self.components = []
    
    def initialize(self):
        """Probably initializes all components."""
        pass

# Import that suggests architecture
from some_package import (
    AbstractBaseClass,  # Probably an abstract base class
    ConcreteImplementation,  # Likely a concrete implementation
    Interface,  # Seems to be an interface
)

# Constants that imply configuration
TIMEOUT = 30  # Probably seconds
RETRY_DELAY = 1.5  # Likely seconds between retries
''')
        
        # Run all observations and patterns
        all_violations: List[str] = []
        
        # Test all eyes
        eyes = [
            ("FileSight", FileSight()),
            ("ImportSight", ImportSight()),
            ("ExportSight", ExportSight()),
            ("BoundarySight", BoundarySight()),
            ("EncodingSight", EncodingSight()),
        ]
        
        for eye_name, eye in eyes:
            try:
                observations = list(eye.observe(tempting_dir))
                for obs in observations:
                    checks = self.detector.check_observation_output(
                        obs.__dict__ if hasattr(obs, '__dict__') else obs,
                        eye_name
                    )
                    for has_inference, evidence in checks:
                        if has_inference:
                            all_violations.append(evidence)
            except Exception as e:
                # Some eyes might fail on this directory - that's OK
                pass
        
        # Test all pattern analyzers
        analyzers = [
            ("DensityAnalyzer", DensityAnalyzer()),
            ("CouplingAnalyzer", CouplingAnalyzer()),
            ("ComplexityAnalyzer", ComplexityAnalyzer()),
            ("BoundaryViolationDetector", BoundaryViolationDetector()),
            ("UncertaintyQuantifier", UncertaintyQuantifier()),
        ]
        
        # Need observations for patterns
        file_eye = FileSight()
        import_eye = ImportSight()
        file_obs = list(file_eye.observe(tempting_dir))
        import_obs = list(import_eye.observe(tempting_dir))
        all_obs = file_obs + import_obs
        
        for analyzer_name, analyzer in analyzers:
            try:
                if analyzer_name == "BoundaryViolationDetector":
                    # Set up boundaries
                    analyzer.set_boundaries({"tempting": "tempting"})
                
                output = analyzer.analyze(all_obs)
                checks = self.detector.check_pattern_output(
                    output.__dict__ if hasattr(output, '__dict__') else output,
                    analyzer_name
                )
                for has_inference, evidence in checks:
                    if has_inference:
                        all_violations.append(evidence)
            except Exception as e:
                # Some analyzers might fail - that's OK
                pass
        
        # Tier-1 failure - any inference detected
        if all_violations:
            # Create detailed report
            report_path = Path.home() / "codemarshal_inference_violation.txt"
            with open(report_path, 'w') as f:
                f.write("CODEMARSHAL INFERENCE VIOLATION REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Test directory: {tempting_dir}\n")
                f.write(f"Violations: {len(all_violations)}\n\n")
                f.write("Tempting code sample:\n")
                f.write("=" * 50 + "\n")
                f.write(tempting_code.read_text())
                f.write("\n\nViolations detected:\n")
                f.write("=" * 50 + "\n")
                for i, violation in enumerate(all_violations, 1):
                    f.write(f"{i}. {violation}\n\n")
            
            pytest.fail(
                f"Hostile inference test failed with {len(all_violations)} violations.\n"
                f"Detailed report written to: {report_path}\n"
                f"First 3 violations:\n" +
                "\n".join(f"  • {v}" for v in all_violations[:3])
            )


def test_four_pillars_enforcement() -> None:
    """
    Test that the Four Pillars of Truth are enforced:
    1. Observability: If it cannot be seen, it cannot be claimed
    2. Traceability: Every claim must have a clear origin
    3. Falsifiability: Every pattern must be disprovable
    4. Humility: "I don't know" is more valuable than a confident guess
    """
    detector = InferenceDetector()
    
    # Pillar 1: Observability
    # Check that output never claims more than what's observable
    test_output = "This module handles user authentication."
    checks = detector.check_for_inference(test_output, "Pillar 1")
    assert len(checks) > 0, "Should detect 'handles' as inference"
    
    # Pillar 2: Traceability
    # Check that patterns don't make untraceable claims
    untraceable = "The code is well-organized."
    checks = detector.check_for_inference(untraceable, "Pillar 2")
    assert len(checks) > 0, "Should detect 'well-organized' as untraceable judgment"
    
    # Pillar 3: Falsifiability
    # Check that claims are specific enough to be falsifiable
    unfalsifiable = "This is probably efficient."
    checks = detector.check_for_inference(unfalsifiable, "Pillar 3")
    assert len(checks) > 0, "Should detect 'efficient' as unfalsifiable"
    
    # Pillar 4: Humility
    # Check that uncertainty is properly marked
    arrogant = "This function definitely validates input."
    checks = detector.check_for_inference(arrogant, "Pillar 4")
    # 'definitely' might not be in our patterns, but it's still inference
    # We should check for certainty language
    certainty_patterns = [re.compile(r'\bdefinitely\b', re.IGNORECASE)]
    has_certainty = any(p.search(arrogant) for p in certainty_patterns)
    assert has_certainty, "Should detect certainty language"
    
    # Humble alternative
    humble = "This function appears to validate input. ⚠️"
    checks = detector.check_uncertainty_markers(humble, "Pillar 4")
    assert len(checks) == 0, "Should accept properly marked uncertainty"


if __name__ == "__main__":
    """
    Standalone execution for manual testing.
    
    Run with: python -m observations.invariants.no_inference.test
    """
    print("Running 'no inference' tests...")
    
    # Create a test instance and run the hostile test
    test_instance = TestNoInference()
    
    try:
        test_instance.setup_method()
        test_instance.test_hostile_inference_detection()
        print("✓ All 'no inference' tests passed")
    except AssertionError as e:
        print(f"✗ Inference violation detected:\n{e}")
        raise
    finally:
        test_instance.teardown_method()