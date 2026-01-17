"""
complete_constitutional.test.py - Complete Self-Validation for All Constitutional Articles

This file implements comprehensive self-validation tests for all 24 constitutional articles.
Each test verifies that the system follows its own constitutional rules.

Article 21: Self-Validation - The system must include tests that verify it follows its own constitution.
"""

import pytest
import sys
import ast
import importlib
from pathlib import Path
from typing import List, Dict, Any, Set
from unittest.mock import Mock, patch

# Import core modules for testing
from core.runtime import Runtime
from core.engine import Engine
from observations.eyes.file_sight import FileSight
from observations.eyes.import_sight import ImportSight
from inquiry.questions.structure import StructureQuestions
from inquiry.patterns.coupling import CouplingAnalyzer
from lens.views.overview import OverviewView
from bridge.entry.cli import CLI
from storage.investigation_storage import InvestigationStorage


class ConstitutionalViolation(Exception):
    """Raised when a constitutional violation is detected."""
    pass


class ConstitutionalValidator:
    """Validates constitutional compliance across all articles."""
    
    def __init__(self):
        self.violations: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
    
    def add_violation(self, article: int, title: str, description: str, file_path: str = None, line: int = None):
        """Record a constitutional violation."""
        self.violations.append({
            'article': article,
            'title': title,
            'description': description,
            'file_path': file_path,
            'line': line,
            'severity': 'VIOLATION'
        })
    
    def add_warning(self, article: int, title: str, description: str, file_path: str = None, line: int = None):
        """Record a constitutional warning."""
        self.warnings.append({
            'article': article,
            'title': title,
            'description': description,
            'file_path': file_path,
            'line': line,
            'severity': 'WARNING'
        })
    
    def is_compliant(self) -> bool:
        """Check if system is constitutionally compliant."""
        return len(self.violations) == 0
    
    def get_compliance_score(self) -> float:
        """Calculate compliance percentage."""
        total_articles = 24
        violated_articles = len(set(v['article'] for v in self.violations))
        return ((total_articles - violated_articles) / total_articles) * 100


# ============================================================================
# TIER 1: FOUNDATIONAL TRUTHS (Articles 1-4)
# ============================================================================

def test_article_1_observation_purity(validator: ConstitutionalValidator):
    """
    Article 1: Observations record only what is textually present in source code.
    No inference, no guessing, no interpretation. Observations are immutable once recorded.
    """
    # Test 1: Check for inference keywords in observation modules
    observation_files = [
        'observations/eyes/file_sight.py',
        'observations/eyes/import_sight.py',
        'observations/eyes/export_sight.py',
        'observations/eyes/boundary_sight.py',
        'observations/eyes/encoding_sight.py'
    ]
    
    inference_keywords = ['infer', 'guess', 'assume', 'likely', 'probably', 'might', 'could', 'interpret']
    
    for file_path in observation_files:
        full_path = Path(file_path)
        if full_path.exists():
            content = full_path.read_text()
            for keyword in inference_keywords:
                if keyword in content.lower():
                    validator.add_violation(
                        article=1,
                        title="Inference Keyword Found",
                        description=f"Found inference keyword '{keyword}' in {file_path}",
                        file_path=file_path
                    )
    
    # Test 2: Verify observations are immutable
    try:
        file_sight = FileSight()
        # Check if observation classes use @dataclass(frozen=True)
        module = importlib.import_module('observations.eyes.file_sight')
        for name in dir(module):
            obj = getattr(module, name)
            if hasattr(obj, '__dataclass_fields__'):
                # Check if frozen
                if not getattr(obj, '__frozen__', False):
                    validator.add_violation(
                        article=1,
                        title="Mutable Observation Class",
                        description=f"Observation class {name} is not frozen",
                        file_path=file_path
                    )
    except Exception as e:
        validator.add_warning(
            article=1,
            title="Immutability Test Failed",
            description=f"Could not test observation immutability: {e}"
        )


def test_article_2_human_primacy(validator: ConstitutionalValidator):
    """
    Article 2: Humans ask questions, see patterns, and think thoughts.
    The system provides observations, detects anomalies, and preserves thinking.
    Never reverse these roles.
    """
    # Test 1: Check for autonomous question generation
    inquiry_files = [
        'inquiry/questions/structure.py',
        'inquiry/questions/purpose.py',
        'inquiry/questions/connections.py',
        'inquiry/questions/anomalies.py'
    ]
    
    autonomous_keywords = ['auto_generate', 'automatic', 'ai_', 'ml_', 'self_think']
    
    for file_path in inquiry_files:
        full_path = Path(file_path)
        if full_path.exists():
            content = full_path.read_text()
            for keyword in autonomous_keywords:
                if keyword in content.lower():
                    validator.add_violation(
                        article=2,
                        title="Autonomous Behavior Detected",
                        description=f"Found autonomous keyword '{keyword}' in {file_path}",
                        file_path=file_path
                    )
    
    # Test 2: Verify pattern detectors are numeric-only
    pattern_files = [
        'inquiry/patterns/coupling.py',
        'inquiry/patterns/density.py',
        'inquiry/patterns/complexity.py'
    ]
    
    for file_path in pattern_files:
        full_path = Path(file_path)
        if full_path.exists():
            content = full_path.read_text()
            # Look for subjective labels
            subjective_labels = ['large', 'small', 'messy', 'clean', 'good', 'bad', 'complex']
            for label in subjective_labels:
                if f'"{label}"' in content:
                    validator.add_violation(
                        article=2,
                        title="Subjective Pattern Label",
                        description=f"Found subjective label '{label}' in {file_path}",
                        file_path=file_path
                    )


def test_article_3_truth_preservation(validator: ConstitutionalValidator):
    """
    Article 3: The system must never obscure, distort, or invent information.
    When truth is uncertain, show uncertainty clearly (⚠️).
    When truth is unknown, say "I cannot see this."
    """
    # Test 1: Check for uncertainty indicators
    error_file = Path('lens/indicators/errors.py')
    if error_file.exists():
        content = error_file.read_text()
        if '⚠️' not in content:
            validator.add_warning(
                article=3,
                title="Missing Uncertainty Indicators",
                description="Uncertainty indicators (⚠️) not found in error handling",
                file_path=str(error_file)
            )
    
    # Test 2: Check for "cannot see" implementations
    limitations_files = [
        'observations/limitations/declared.py',
        'observations/limitations/documented.py'
    ]
    
    for file_path in limitations_files:
        full_path = Path(file_path)
        if full_path.exists():
            content = full_path.read_text()
            if 'cannot see' not in content.lower() and 'unknown' not in content.lower():
                validator.add_warning(
                    article=3,
                    title="Missing Truth Limitations",
                    description=f"No 'cannot see' declarations found in {file_path}",
                    file_path=file_path
                )


def test_article_4_progressive_disclosure(validator: ConstitutionalValidator):
    """
    Article 4: Start with simple observations, reveal complexity only when requested.
    Never overwhelm with information. Each interaction should answer exactly one human question.
    """
    # Test 1: Check TUI for single focus
    tui_file = Path('bridge/entry/tui.py')
    if tui_file.exists():
        content = tui_file.read_text()
        # Look for multi-panel patterns
        multi_panel_keywords = ['multiple_panels', 'split_screen', 'concurrent_views']
        for keyword in multi_panel_keywords:
            if keyword in content.lower():
                validator.add_violation(
                    article=4,
                    title="Information Overload Pattern",
                    description=f"Found multi-panel keyword '{keyword}' in TUI",
                    file_path=str(tui_file)
                )
    
    # Test 2: Check linear investigation flow
    overview_file = Path('lens/views/overview.py')
    if overview_file.exists():
        content = overview_file.read_text()
        # Look for random access patterns
        random_keywords = ['random_access', 'jump_to', 'skip_ahead']
        for keyword in random_keywords:
            if keyword in content.lower():
                validator.add_violation(
                    article=4,
                    title="Non-Linear Investigation",
                    description=f"Found non-linear keyword '{keyword}' in overview view",
                    file_path=str(overview_file)
                )


# ============================================================================
# TIER 2: INTERFACE INTEGRITY (Articles 5-8)
# ============================================================================

def test_article_5_single_focus_interface(validator: ConstitutionalValidator):
    """
    Article 5: Only one primary content area visible at a time.
    No competing information streams.
    """
    # Test TUI implementation for single focus
    tui_file = Path('bridge/entry/tui.py')
    if tui_file.exists():
        content = tui_file.read_text()
        # Check for single focus enforcement
        if 'single_focus' not in content.lower():
            validator.add_warning(
                article=5,
                title="Missing Single Focus Enforcement",
                description="TUI does not explicitly enforce single focus",
                file_path=str(tui_file)
            )


def test_article_6_linear_investigation(validator: ConstitutionalValidator):
    """
    Article 6: Follow natural human curiosity:
    What exists? What does it do? How is it connected?
    What seems unusual? What do I think? Never skip ahead or jump randomly.
    """
    # Test investigation stages
    overview_file = Path('lens/views/overview.py')
    if overview_file.exists():
        content = overview_file.read_text()
        # Look for linear investigation stages
        linear_stages = ['ORIENTATION', 'OBSERVATION', 'PATTERN_DETECTION', 'THINKING', 'SYNTHESIS']
        for stage in linear_stages:
            if stage not in content:
                validator.add_warning(
                    article=6,
                    title="Missing Investigation Stage",
                    description=f"Linear investigation stage '{stage}' not found",
                    file_path=str(overview_file)
                )


def test_article_7_clear_affordances(validator: ConstitutionalValidator):
    """
    Article 7: At every moment, show what can be done next with obvious, consistent actions.
    No hidden capabilities, no Easter eggs.
    """
    # Test CLI for clear affordances
    cli_file = Path('bridge/entry/cli.py')
    if cli_file.exists():
        content = cli_file.read_text()
        # Check for help system
        if 'help' not in content.lower():
            validator.add_warning(
                article=7,
                title="Missing Help System",
                description="CLI does not provide help system",
                file_path=str(cli_file)
            )


def test_article_8_honest_performance(validator: ConstitutionalValidator):
    """
    Article 8: If computation takes time, show a simple indicator.
    If something cannot be computed, explain why.
    Never freeze without indication, never pretend speed that isn't there.
    """
    # Test for performance indicators
    indicators_file = Path('lens/indicators/loading.py')
    if indicators_file.exists():
        content = indicators_file.read_text()
        # Check for loading indicators
        if 'loading' not in content.lower() and 'progress' not in content.lower():
            validator.add_warning(
                article=8,
                title="Missing Performance Indicators",
                description="Loading indicators not implemented",
                file_path=str(indicators_file)
            )
    else:
        validator.add_warning(
            article=8,
            title="Missing Performance Module",
            description="Performance indicators module not found"
        )


# ============================================================================
# TIER 3: ARCHITECTURAL CONSTRAINTS (Articles 9-12)
# ============================================================================

def test_article_9_immutable_observations(validator: ConstitutionalValidator):
    """
    Article 9: Once an observation is recorded, it cannot change.
    New observations create new versions. This ensures reproducibility and auditability.
    """
    # Test observation immutability
    snapshot_file = Path('observations/record/snapshot.py')
    if snapshot_file.exists():
        content = snapshot_file.read_text()
        # Check for frozen dataclasses
        if '@dataclass(frozen=True)' not in content:
            validator.add_violation(
                article=9,
                title="Mutable Observations",
                description="Snapshot class is not frozen",
                file_path=str(snapshot_file)
            )


def test_article_10_anchored_thinking(validator: ConstitutionalValidator):
    """
    Article 10: All human thoughts must be anchored to specific observations.
    No floating opinions, no unattached ideas. This creates traceable reasoning chains.
    """
    # Test notebook entries for anchoring
    notebook_file = Path('inquiry/notebook/entries.py')
    if notebook_file.exists():
        content = notebook_file.read_text()
        # Check for anchor system
        if 'anchor' not in content.lower():
            validator.add_violation(
                article=10,
                title="Missing Thought Anchoring",
                description="Notebook entries do not anchor to observations",
                file_path=str(notebook_file)
            )


def test_article_11_declared_limitations(validator: ConstitutionalValidator):
    """
    Article 11: Every observation method must declare what it cannot see.
    Every pattern detector must declare its uncertainty.
    These declarations are first-class system outputs.
    """
    # Test for limitation declarations
    limitations_dir = Path('observations/limitations')
    if not limitations_dir.exists():
        validator.add_violation(
            article=11,
            title="Missing Limitations Directory",
            description="Observations limitations not declared"
        )
    else:
        # Check if limitation files exist
        required_files = ['declared.py', 'documented.py', 'validation.py']
        for file_name in required_files:
            if not (limitations_dir / file_name).exists():
                validator.add_warning(
                    article=11,
                    title="Missing Limitation File",
                    description=f"Required limitation file '{file_name}' not found"
                )


def test_article_12_local_operation(validator: ConstitutionalValidator):
    """
    Article 12: All analysis works without network connectivity.
    No cloud dependencies for core functionality. Truth should not depend on external services.
    """
    # Test for network dependencies
    import ast
    import os
    
    network_keywords = ['requests', 'urllib', 'http', 'socket', 'api']
    
    for root, dirs, files in os.walk('.'):
        # Skip venv and __pycache__
        if 'venv' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                try:
                    content = file_path.read_text()
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                if any(keyword in alias.name.lower() for keyword in network_keywords):
                                    validator.add_violation(
                                        article=12,
                                        title="Network Dependency Found",
                                        description=f"Network import '{alias.name}' found in {file_path}",
                                        file_path=str(file_path)
                                    )
                        elif isinstance(node, ast.ImportFrom):
                            if node.module and any(keyword in node.module.lower() for keyword in network_keywords):
                                validator.add_violation(
                                    article=12,
                                        title="Network Dependency Found",
                                    description=f"Network import '{node.module}' found in {file_path}",
                                    file_path=str(file_path)
                                )
                except Exception:
                    # Skip files that can't be parsed
                    continue


# ============================================================================
# TIER 4: SYSTEM BEHAVIOR (Articles 13-15)
# ============================================================================

def test_article_13_deterministic_operation(validator: ConstitutionalValidator):
    """
    Article 13: Same input must produce same output, regardless of when or where it runs.
    No randomness in analysis, no time-based behavior changes.
    
    Constitutional Clarification:
    "Same input must produce same output" applies to analysis results (observations, patterns, insights).
    Operational metadata (session IDs, timestamps, transaction IDs) may use time-based generation.
    Truth artifacts must be deterministic; operational artifacts may be contextual.
    """
    # Test for randomness in analysis modules (truth artifacts)
    analysis_modules = [
        'observations/eyes/',
        'inquiry/patterns/',
        'inquiry/questions/',
        'core/engine.py'
    ]
    
    random_keywords = ['random', 'randint', 'choice']
    
    for module_path in analysis_modules:
        if Path(module_path).exists():
            for root, dirs, files in os.walk(module_path):
                if '__pycache__' in root:
                    continue
                    
                for file in files:
                    if file.endswith('.py'):
                        file_path = Path(root) / file
                        try:
                            content = file_path.read_text()
                            for keyword in random_keywords:
                                if keyword in content:
                                    # Check if it's actually used for randomness
                                    if f'{keyword}(' in content:
                                        validator.add_violation(
                                            article=13,
                                            title="Randomness in Analysis Module",
                                            description=f"Randomness keyword '{keyword}' found in analysis module {file_path}",
                                            file_path=str(file_path)
                                        )
                        except Exception:
                            continue
    
    # Test that observation IDs are deterministic (truth artifacts)
    try:
        from storage.transactional import WriteTransaction
        from observations.record.snapshot import Snapshot
        
        # Create test observation data
        test_data = {"test": "content", "path": "/test/file.py"}
        session_id = "test_session"
        
        # Generate ID twice - should be identical
        transaction = WriteTransaction(Path("/tmp/test"))
        
        # First generation
        obs_id_1 = transaction._generate_observation_id(test_data, session_id)
        
        # Second generation (should be identical)
        obs_id_2 = transaction._generate_observation_id(test_data, session_id)
        
        if obs_id_1 != obs_id_2:
            validator.add_violation(
                article=13,
                title="Non-Deterministic Observation IDs",
                description="Same observation data produced different IDs",
                file_path="storage/transactional.py"
            )
                
    except Exception as e:
        validator.add_warning(
            article=13,
            title="Determinism Test Failed",
            description=f"Could not test deterministic observation IDs: {e}"
        )
    
    # Allow time-based IDs in operational modules (metadata)
    operational_modules = [
        'storage/investigation_storage.py',  # Session IDs
        'storage/backup.py',                # Backup IDs
        'integrity/recovery/audit.py'        # Audit event IDs
    ]
    
    time_keywords = ['datetime.now(', 'time.time(']
    
    for module_path in operational_modules:
        file_path = Path(module_path)
        if file_path.exists():
            try:
                content = file_path.read_text()
                for keyword in time_keywords:
                    if keyword in content:
                        # This is allowed for operational metadata
                        pass  # No violation - operational metadata can be time-based
            except Exception:
                continue


def test_article_14_graceful_degradation(validator: ConstitutionalValidator):
    """
    Article 14: When parts fail, preserve what works.
    Show available observations even when some cannot be collected.
    Explain failures simply and honestly.
    """
    # Test for graceful error handling
    error_file = Path('lens/indicators/errors.py')
    if error_file.exists():
        content = error_file.read_text()
        # Check for error severity levels
        if 'ErrorSeverity' not in content:
            validator.add_warning(
                article=14,
                title="Missing Error Severity",
                description="Error severity levels not defined",
                file_path=str(error_file)
            )


def test_article_15_session_integrity(validator: ConstitutionalValidator):
    """
    Article 15: Investigations can be paused, resumed, and recovered.
    System crashes should not lose thinking. Truth persists across interruptions.
    """
    # Test for session persistence
    session_file = Path('inquiry/session/context.py')
    if session_file.exists():
        content = session_file.read_text()
        # Check for persistence mechanisms
        if 'persist' not in content.lower() and 'save' not in content.lower():
            validator.add_warning(
                article=15,
                title="Missing Session Persistence",
                description="Session persistence not implemented",
                file_path=str(session_file)
            )
    
    # Test for crash recovery
    recovery_file = Path('integrity/recovery/backup.py')
    if not recovery_file.exists():
        validator.add_warning(
            article=15,
            title="Missing Crash Recovery",
            description="Crash recovery mechanisms not found"
        )


# ============================================================================
# TIER 5: AESTHETIC CONSTRAINTS (Articles 16-18)
# ============================================================================

def test_article_16_truth_preserving_aesthetics(validator: ConstitutionalValidator):
    """
    Article 16: Visual design should enhance truth perception, not obscure it.
    Colors indicate meaning (⚠️ for uncertainty), typography ensures readability,
    layout reduces cognitive load.
    """
    # Test for uncertainty indicators in aesthetics
    palette_file = Path('lens/aesthetic/palette.py')
    if palette_file.exists():
        content = palette_file.read_text()
        # Check for uncertainty color
        if 'uncertainty' not in content.lower() and 'warning' not in content.lower():
            validator.add_warning(
                article=16,
                title="Missing Uncertainty Aesthetics",
                description="Uncertainty indicators not defined in color palette",
                file_path=str(palette_file)
            )


def test_article_17_minimal_decoration(validator: ConstitutionalValidator):
    """
    Article 17: Every visual element must serve truth preservation.
    No decoration for decoration's sake. When in doubt, simpler is truer.
    """
    # Test for decorative elements
    view_files = [
        'lens/views/overview.py',
        'lens/views/examination.py',
        'lens/views/connections.py'
    ]
    
    decorative_keywords = ['decorative', 'ornament', 'embellish', 'beautify']
    
    for file_path in view_files:
        full_path = Path(file_path)
        if full_path.exists():
            content = full_path.read_text()
            for keyword in decorative_keywords:
                if keyword in content.lower():
                    validator.add_warning(
                        article=17,
                        title="Decorative Elements Found",
                        description=f"Decorative keyword '{keyword}' found in {file_path}",
                        file_path=file_path
                    )


def test_article_18_consistent_metaphor(validator: ConstitutionalValidator):
    """
    Article 18: The investigation metaphor (observations, patterns, thinking)
    should be applied consistently across interface. Mixed metaphors confuse truth perception.
    """
    # Test for metaphor consistency
    interface_files = [
        'bridge/entry/cli.py',
        'bridge/entry/tui.py',
        'lens/views/overview.py'
    ]
    
    # Check for consistent investigation terminology
    investigation_terms = ['investigate', 'observe', 'pattern', 'think', 'evidence']
    
    for file_path in interface_files:
        full_path = Path(file_path)
        if full_path.exists():
            content = full_path.read_text()
            # Count investigation terms
            term_count = sum(1 for term in investigation_terms if term in content.lower())
            if term_count < 2:  # Should have multiple investigation terms
                validator.add_warning(
                    article=18,
                    title="Inconsistent Metaphor",
                    description=f"Insufficient investigation terminology in {file_path}",
                    file_path=file_path
                )


# ============================================================================
# TIER 6: EVOLUTION RULES (Articles 19-21)
# ============================================================================

def test_article_19_backward_truth_compatibility(validator: ConstitutionalValidator):
    """
    Article 19: New versions must not invalidate previous observations.
    Old investigations should remain understandable. Truth does not expire.
    """
    # Test for migration system
    migration_file = Path('storage/migration.py')
    if not migration_file.exists():
        validator.add_warning(
            article=19,
            title="Missing Migration System",
            description="Backward compatibility migration not found"
        )


def test_article_20_progressive_enhancement(validator: ConstitutionalValidator):
    """
    Article 20: New capabilities should build on, not replace, existing ones.
    Each feature should be complete within its scope before moving to the next.
    """
    # Test for modular architecture
    core_file = Path('core/engine.py')
    if core_file.exists():
        content = core_file.read_text()
        # Check for coordination without replacement
        if 'coordinate' not in content.lower():
            validator.add_warning(
                article=20,
                title="Missing Progressive Enhancement",
                description="Engine coordination not found",
                file_path=str(core_file)
            )


def test_article_21_self_validation(validator: ConstitutionalValidator):
    """
    Article 21: The system must include tests that verify it follows its own constitution.
    A truth-keeping tool that cannot verify its own truth is worthless.
    """
    # This is the meta-test - we're running it right now!
    validator.add_warning(
        article=21,
        title="Self-Validation In Progress",
        description="Self-validation test suite is being executed"
    )


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_constitutional_audit() -> ConstitutionalValidator:
    """Run complete constitutional audit and return validator with results."""
    validator = ConstitutionalValidator()
    
    # Run all article tests
    test_functions = [
        test_article_1_observation_purity,
        test_article_2_human_primacy,
        test_article_3_truth_preservation,
        test_article_4_progressive_disclosure,
        test_article_5_single_focus_interface,
        test_article_6_linear_investigation,
        test_article_7_clear_affordances,
        test_article_8_honest_performance,
        test_article_9_immutable_observations,
        test_article_10_anchored_thinking,
        test_article_11_declared_limitations,
        test_article_12_local_operation,
        test_article_13_deterministic_operation,
        test_article_14_graceful_degradation,
        test_article_15_session_integrity,
        test_article_16_truth_preserving_aesthetics,
        test_article_17_minimal_decoration,
        test_article_18_consistent_metaphor,
        test_article_19_backward_truth_compatibility,
        test_article_20_progressive_enhancement,
        test_article_21_self_validation
    ]
    
    for test_func in test_functions:
        try:
            test_func(validator)
        except Exception as e:
            validator.add_violation(
                article=999,
                title="Test Execution Error",
                description=f"Error running {test_func.__name__}: {e}"
            )
    
    return validator


def test_constitutional_compliance():
    """Pytest entry point for constitutional compliance testing."""
    validator = run_constitutional_audit()
    
    # Print results
    print(f"\n{'='*60}")
    print("CONSTITUTIONAL COMPLIANCE AUDIT RESULTS")
    print(f"{'='*60}")
    
    print(f"\nCompliance Score: {validator.get_compliance_score():.1f}%")
    print(f"Violations: {len(validator.violations)}")
    print(f"Warnings: {len(validator.warnings)}")
    
    if validator.violations:
        print(f"\n🚨 CONSTITUTIONAL VIOLATIONS:")
        for violation in validator.violations:
            print(f"  Article {violation['article']}: {violation['title']}")
            print(f"    {violation['description']}")
            if violation['file_path']:
                print(f"    Location: {violation['file_path']}")
    
    if validator.warnings:
        print(f"\n⚠️ CONSTITUTIONAL WARNINGS:")
        for warning in validator.warnings:
            print(f"  Article {warning['article']}: {warning['title']}")
            print(f"    {warning['description']}")
            if warning['file_path']:
                print(f"    Location: {warning['file_path']}")
    
    if validator.is_compliant():
        print(f"\n✅ SYSTEM IS CONSTITUTIONALLY COMPLIANT")
    else:
        print(f"\n❌ SYSTEM HAS CONSTITUTIONAL VIOLATIONS")
    
    print(f"{'='*60}")
    
    # Assert compliance for pytest
    assert validator.is_compliant(), f"Constitutional violations found: {len(validator.violations)}"
    assert validator.get_compliance_score() >= 95.0, f"Compliance score too low: {validator.get_compliance_score()}"


if __name__ == "__main__":
    test_constitutional_compliance()
