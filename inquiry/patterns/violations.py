"""
Boundary violation detection for CodeMarshal.

This module detects explicit boundary crossings based on declared rules.
It outputs boolean facts with evidence anchors - no interpretation, no ranking.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Tuple, Union, Set
import fnmatch

# Import from observations layer (allowed per architecture)
from observations.eyes.boundary_sight import BoundarySight
from observations.record.anchors import Anchor, EvidenceAnchor
from observations.record.snapshot import CodeSnapshot


@dataclass(frozen=True)
class BoundaryRule:
    """Immutable representation of a boundary rule.
    
    This is a data container, not a logic class.
    Rules are declared by users, not inferred by the system.
    """
    rule_id: str
    source_pattern: Pattern[str]
    target_pattern: Pattern[str]
    description: str
    evidence_requirements: Tuple[str, ...]  # Required evidence types
    
    @classmethod
    def from_config(cls, rule_data: Dict) -> 'BoundaryRule':
        """Create a rule from configuration data."""
        return cls(
            rule_id=rule_data['id'],
            source_pattern=re.compile(rule_data['source_pattern']),
            target_pattern=re.compile(rule_data['target_pattern']),
            description=rule_data.get('description', ''),
            evidence_requirements=tuple(rule_data.get('evidence_requirements', []))
        )


@dataclass(frozen=True)
class BoundaryViolation:
    """Immutable record of a single boundary crossing.
    
    Contains only:
    - Rule ID that was violated
    - Evidence anchors showing the violation
    - No severity, no ranking, no recommendations
    """
    rule_id: str
    evidence: Tuple[EvidenceAnchor, ...]  # Multiple anchors for full context
    boundary_type: str  # e.g., "import", "call", "reference"
    
    def to_dict(self) -> Dict:
        """Convert to serializable dict without interpretation."""
        return {
            'rule_id': self.rule_id,
            'evidence': [anchor.to_dict() for anchor in self.evidence],
            'boundary_type': self.boundary_type,
            'detected_at': self.evidence[0].timestamp.isoformat() if self.evidence else None
        }


class BoundaryViolationDetector:
    """Detects boundary crossings based on declared rules.
    
    This class:
    - Applies rules to observations
    - Returns boolean facts with evidence
    - Never interprets or ranks
    - Never suggests fixes
    - Never attaches blame
    
    All methods return immutable data structures.
    """
    
    def __init__(self, rules: Tuple[BoundaryRule, ...]):
        """Initialize with immutable rule set."""
        self._rules = rules
        self._boundary_sight = BoundarySight()
    
    def detect_all(self, snapshot: CodeSnapshot) -> Tuple[BoundaryViolation, ...]:
        """Detect all boundary violations in a snapshot.
        
        Returns:
            Tuple of violations, each with rule ID and evidence.
            Empty tuple if no violations found.
        """
        violations: List[BoundaryViolation] = []
        
        # Get boundary observations from the snapshot
        boundary_observations = self._boundary_sight.observe(snapshot)
        
        for rule in self._rules:
            rule_violations = self._detect_rule_violations(
                rule, 
                boundary_observations,
                snapshot
            )
            violations.extend(rule_violations)
        
        return tuple(violations)
    
    def _detect_rule_violations(
        self,
        rule: BoundaryRule,
        boundaries: Dict[str, List[EvidenceAnchor]],
        snapshot: CodeSnapshot
    ) -> List[BoundaryViolation]:
        """Detect violations of a specific rule."""
        violations: List[BoundaryViolation] = []
        
        # Check each boundary type that has evidence requirements for this rule
        for boundary_type in rule.evidence_requirements:
            if boundary_type in boundaries:
                for anchor in boundaries[boundary_type]:
                    if self._is_rule_violation(rule, anchor, snapshot):
                        violations.append(BoundaryViolation(
                            rule_id=rule.rule_id,
                            evidence=(anchor,),
                            boundary_type=boundary_type
                        ))
        
        return violations
    
    def _is_rule_violation(
        self,
        rule: BoundaryRule,
        anchor: EvidenceAnchor,
        snapshot: CodeSnapshot
    ) -> bool:
        """Check if a single anchor violates a rule.
        
        Returns:
            True if the anchor violates the rule, False otherwise.
            This is a pure boolean fact - no interpretation.
        """
        try:
            # Get source and target from the anchor
            source_path = anchor.metadata.get('source_path', '')
            target_path = anchor.metadata.get('target_path', '')
            
            # Convert to strings if they're Path objects
            source_str = str(source_path) if isinstance(source_path, Path) else source_path
            target_str = str(target_path) if isinstance(target_path, Path) else target_path
            
            # Apply the rule patterns
            source_matches = bool(rule.source_pattern.match(source_str))
            target_matches = bool(rule.target_pattern.match(target_str))
            
            # Both must match for a violation
            return source_matches and target_matches
            
        except (AttributeError, KeyError, TypeError):
            # If we can't check, it's not a violation
            # This maintains the invariant: "when in doubt, no violation"
            return False
    
    def detect_import_violations(
        self, 
        import_edges: List[Tuple[str, str, EvidenceAnchor]]
    ) -> Dict[str, List[EvidenceAnchor]]:
        """Detect import-based boundary violations.
        
        Args:
            import_edges: List of (source_module, target_module, anchor)
            
        Returns:
            Dictionary mapping rule_id to list of evidence anchors.
            Empty dict if no violations.
        """
        violations: Dict[str, List[EvidenceAnchor]] = {}
        
        for source, target, anchor in import_edges:
            for rule in self._rules:
                if self._matches_import_rule(rule, source, target):
                    violations.setdefault(rule.rule_id, []).append(anchor)
        
        return violations
    
    def _matches_import_rule(
        self, 
        rule: BoundaryRule, 
        source: str, 
        target: str
    ) -> bool:
        """Check if an import edge matches a rule pattern.
        
        Returns:
            True if the import violates the rule, False otherwise.
        """
        try:
            source_matches = bool(rule.source_pattern.match(source))
            target_matches = bool(rule.target_pattern.match(target))
            return source_matches and target_matches
        except (AttributeError, re.error):
            return False
    
    def detect_path_violations(
        self,
        file_paths: List[Tuple[str, EvidenceAnchor]]
    ) -> Dict[str, List[EvidenceAnchor]]:
        """Detect file path boundary violations.
        
        Useful for detecting files in wrong directories, etc.
        """
        violations: Dict[str, List[EvidenceAnchor]] = {}
        
        for path_str, anchor in file_paths:
            for rule in self._rules:
                if self._matches_path_rule(rule, path_str):
                    violations.setdefault(rule.rule_id, []).append(anchor)
        
        return violations
    
    def _matches_path_rule(self, rule: BoundaryRule, path: str) -> bool:
        """Check if a file path matches a rule pattern."""
        try:
            # Try regex first
            if rule.source_pattern.pattern:  # Check if pattern is not empty
                return bool(rule.source_pattern.match(path))
            return False
        except (AttributeError, re.error):
            # Fall back to fnmatch for simpler patterns
            try:
                return fnmatch.fnmatch(path, rule.source_pattern.pattern)
            except (AttributeError, TypeError):
                return False


def load_rules_from_config(config_path: Path) -> Tuple[BoundaryRule, ...]:
    """Load boundary rules from a configuration file.
    
    This is a factory function, not a method of the detector.
    Rules are configuration, not logic.
    """
    import json
    
    if not config_path.exists():
        return ()
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    rules: List[BoundaryRule] = []
    
    for rule_data in config.get('boundary_rules', []):
        try:
            rule = BoundaryRule.from_config(rule_data)
            rules.append(rule)
        except (KeyError, re.error) as e:
            # Log but continue - invalid rules don't stop detection
            print(f"Warning: Invalid rule configuration: {e}")
            continue
    
    return tuple(rules)


def validate_rules(rules: Tuple[BoundaryRule, ...]) -> Tuple[bool, List[str]]:
    """Validate that rules are properly formed.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
        Empty error list if valid.
    """
    errors: List[str] = []
    rule_ids: Set[str] = set()
    
    for rule in rules:
        # Check for duplicate rule IDs
        if rule.rule_id in rule_ids:
            errors.append(f"Duplicate rule ID: {rule.rule_id}")
        rule_ids.add(rule.rule_id)
        
        # Check rule ID format
        if not re.match(r'^[a-z_][a-z0-9_]*$', rule.rule_id):
            errors.append(f"Invalid rule ID format: {rule.rule_id}")
        
        # Check patterns are compileable (they already are, but verify)
        try:
            re.compile(rule.source_pattern.pattern)
        except re.error as e:
            errors.append(f"Invalid source pattern for rule {rule.rule_id}: {e}")
        
        try:
            re.compile(rule.target_pattern.pattern)
        except re.error as e:
            errors.append(f"Invalid target pattern for rule {rule.rule_id}: {e}")
    
    return (len(errors) == 0, errors)


# Export for pattern registry
def calculate_violations(
    snapshot: CodeSnapshot,
    rules_config: Optional[Dict] = None
) -> Dict[str, Union[bool, List[Dict]]]:
    """Pattern calculator function for the registry.
    
    This is the function that will be registered in patterns/__init__.py.
    
    Args:
        snapshot: The code snapshot to analyze
        rules_config: Optional rules configuration
        
    Returns:
        Dict with:
        - 'has_violations': boolean
        - 'violations': list of violation dicts (empty if none)
        - 'rule_ids': list of rule IDs that were checked
        
    Note: This function never returns prose or interpretations.
    """
    if rules_config is None:
        # Return empty result, not an error
        return {
            'has_violations': False,
            'violations': [],
            'rule_ids': [],
            'rule_count': 0
        }
    
    # Convert config to rules
    rules: List[BoundaryRule] = []
    for rule_data in rules_config.get('boundary_rules', []):
        try:
            rule = BoundaryRule.from_config(rule_data)
            rules.append(rule)
        except (KeyError, re.error):
            continue
    
    # Create detector
    detector = BoundaryViolationDetector(tuple(rules))
    
    # Detect violations
    violations = detector.detect_all(snapshot)
    
    # Convert to serializable format
    violation_dicts = [violation.to_dict() for violation in violations]
    
    return {
        'has_violations': len(violations) > 0,
        'violation_count': len(violations),
        'violations': violation_dicts,
        'rule_ids': [rule.rule_id for rule in rules],
        'rule_count': len(rules),
        'checked_at': snapshot.timestamp.isoformat()
    }


# Test function to verify invariants
def test_boundary_violation_invariants() -> Tuple[bool, List[str]]:
    """Test that the module maintains its invariants.
    
    Returns:
        Tuple of (all_passed, list_of_failed_tests)
    """
    failures: List[str] = []
    
    # Test 1: Rules are immutable
    try:
        rule = BoundaryRule(
            rule_id='test_rule',
            source_pattern=re.compile(r'^source.*'),
            target_pattern=re.compile(r'^target.*'),
            description='Test rule',
            evidence_requirements=('import',)
        )
        
        # Try to modify (should raise AttributeError for frozen dataclass)
        try:
            rule.rule_id = 'modified'  # type: ignore
            failures.append("Rule should be immutable (frozen)")
        except (AttributeError, dataclasses.FrozenInstanceError):
            pass  # Expected
            
    except Exception as e:
        failures.append(f"Rule creation failed: {e}")
    
    # Test 2: Violation detection returns boolean only
    detector = BoundaryViolationDetector(())
    empty_snapshot = CodeSnapshot(
        timestamp=datetime.now(timezone.utc),
        root_path=Path('.'),
        observations={}
    )
    
    violations = detector.detect_all(empty_snapshot)
    
    # Should be a tuple (immutable)
    if not isinstance(violations, tuple):
        failures.append("Violations should be returned as immutable tuple")
    
    # Test 3: calculate_violations returns only allowed types
    result = calculate_violations(empty_snapshot, None)
    
    allowed_keys = {'has_violations', 'violations', 'rule_ids', 
                   'rule_count', 'violation_count', 'checked_at'}
    
    for key in result.keys():
        if key not in allowed_keys:
            failures.append(f"calculate_violations returned unexpected key: {key}")
    
    # Check value types
    if not isinstance(result['has_violations'], bool):
        failures.append("has_violations must be boolean")
    
    if not isinstance(result['violations'], list):
        failures.append("violations must be list")
    
    # Test 4: No prose in outputs
    violation = BoundaryViolation(
        rule_id='test',
        evidence=(),
        boundary_type='import'
    )
    
    violation_dict = violation.to_dict()
    
    # Check for prose-like fields
    prose_fields = {'recommendation', 'fix', 'severity', 'blame', 'advice'}
    if any(field in violation_dict for field in prose_fields):
        failures.append("Violation dict contains prose fields")
    
    return (len(failures) == 0, failures)


# Import at bottom to avoid circular imports
import dataclasses
from datetime import datetime, timezone

if __name__ == '__main__':
    # Run invariant tests when executed directly
    passed, failures = test_boundary_violation_invariants()
    
    if passed:
        print("✓ All boundary violation invariants maintained")
    else:
        print("✗ Boundary violation invariant failures:")
        for failure in failures:
            print(f"  - {failure}")
        exit(1)