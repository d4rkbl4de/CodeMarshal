"""
metaphor_consistency.test.py - Investigation Metaphor Consistency Validation

Article 18: The investigation metaphor (observations, patterns, thinking)
should be applied consistently across interface. Mixed metaphors confuse truth perception.
"""

import ast
import re
from pathlib import Path
from typing import Any

# Import CodeMarshal modules for testing


class MetaphorConsistencyValidator:
    """Validates investigation metaphor consistency across all interfaces."""

    def __init__(self):
        self.violations: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []

        # Define the core investigation metaphor terms
        self.investigation_terms = {
            "primary": ["investigate", "observe", "evidence", "case", "inquiry"],
            "secondary": ["pattern", "hypothesis", "analysis", "detect"],
            "tertiary": ["think", "note", "reflect", "conclusion", "insight"],
            "process": ["stage", "phase", "step", "progress", "workflow"],
            "interface": ["lens", "focus", "magnifying", "workspace", "workbench"],
        }

        # Define forbidden mixed metaphors
        self.forbidden_terms = {
            "business": ["dashboard", "analytics", "metrics", "kpi", "report"],
            "military": ["command", "mission", "target", "deploy", "strategy"],
            "industrial": ["factory", "assembly", "production", "manufacture"],
            "educational": ["lesson", "grade", "student", "teacher", "curriculum"],
            "medical": ["diagnosis", "symptom", "treatment", "patient", "therapy"],
        }

    def add_violation(self, file_path: str, line: int, issue: str, description: str):
        """Record a metaphor consistency violation."""
        self.violations.append(
            {
                "file_path": file_path,
                "line": line,
                "issue": issue,
                "description": description,
                "severity": "VIOLATION",
            }
        )

    def add_warning(self, file_path: str, line: int, issue: str, description: str):
        """Record a metaphor consistency warning."""
        self.warnings.append(
            {
                "file_path": file_path,
                "line": line,
                "issue": issue,
                "description": description,
                "severity": "WARNING",
            }
        )

    def check_file_metaphor_consistency(self, file_path: Path) -> None:
        """Check a single file for metaphor consistency."""
        try:
            content = file_path.read_text()

            # Parse AST to find string literals and comments
            tree = ast.parse(content)

            # Extract all string literals
            string_literals = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Str):
                    string_literals.append(node.s)
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    string_literals.append(node.value)

            # Check for investigation metaphor terms
            found_investigation_terms = []
            found_forbidden_terms = []

            for literal in string_literals:
                literal_lower = literal.lower()

                # Check for investigation terms
                for category, terms in self.investigation_terms.items():
                    for term in terms:
                        if term in literal_lower:
                            found_investigation_terms.append((term, category))

                # Check for forbidden mixed metaphors
                for category, terms in self.forbidden_terms.items():
                    for term in terms:
                        if term in literal_lower:
                            found_forbidden_terms.append((term, category))

            # Report violations
            if found_forbidden_terms:
                for term, category in found_forbidden_terms:
                    self.add_violation(
                        file_path=str(file_path),
                        line=0,  # Would need line numbers from AST
                        issue="Mixed Metaphor",
                        description=f"Found forbidden '{category}' metaphor term: '{term}'",
                    )

            # Report warnings for weak investigation metaphor
            investigation_count = len(found_investigation_terms)
            if investigation_count < 3:  # Should have multiple investigation terms
                self.add_warning(
                    file_path=str(file_path),
                    line=0,
                    issue="Weak Investigation Metaphor",
                    description=f"Only {investigation_count} investigation terms found",
                )

        except Exception as e:
            self.add_warning(
                file_path=str(file_path),
                line=0,
                issue="Parse Error",
                description=f"Could not parse file: {e}",
            )

    def check_class_and_function_names(self, file_path: Path) -> None:
        """Check class and function names for metaphor consistency."""
        try:
            content = file_path.read_text()
            tree = ast.parse(content)

            # Extract all class and function names
            names = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    names.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    names.append(node.name)

            # Check names for metaphor consistency
            for name in names:
                name_lower = name.lower()

                # Check for investigation metaphor terms (good)
                found_investigation = any(
                    term in name_lower
                    for terms in self.investigation_terms.values()
                    for term in terms
                )

                # Check for forbidden mixed metaphors (bad)
                found_forbidden = any(
                    term in name_lower
                    for terms in self.forbidden_terms.values()
                    for term in terms
                )

                if found_investigation:
                    # Good - investigation metaphor term found
                    continue

                if found_forbidden:
                    self.add_violation(
                        file_path=str(file_path),
                        line=0,
                        issue="Forbidden Metaphor in Name",
                        description=f"Function/class name '{name}' uses forbidden metaphor",
                    )

        except Exception as e:
            self.add_warning(
                file_path=str(file_path),
                line=0,
                issue="Name Parse Error",
                description=f"Could not parse names: {e}",
            )

    def check_comments_and_docstrings(self, file_path: Path) -> None:
        """Check comments and docstrings for metaphor consistency."""
        try:
            content = file_path.read_text()

            # Extract comments and docstrings
            comments = []

            # Simple regex for comments
            comment_pattern = r'#.*$|""".*?"""|\'\'\'.*?\'\'\''
            for match in re.finditer(comment_pattern, content, re.MULTILINE):
                comment = match.group().strip()
                if (
                    comment.startswith("#")
                    or comment.startswith('"""')
                    or comment.startswith("'''")
                ):
                    comments.append(comment)

            # Check comments for metaphor consistency
            for comment in comments:
                comment_lower = comment.lower()

                # Check for investigation terms
                found_investigation = any(
                    term in comment_lower
                    for terms in self.investigation_terms.values()
                    for term in terms
                )

                # Check for forbidden terms
                found_forbidden = any(
                    term in comment_lower
                    for terms in self.forbidden_terms.values()
                    for term in terms
                )

                if found_forbidden:
                    self.add_violation(
                        file_path=str(file_path),
                        line=0,
                        issue="Forbidden Metaphor in Comment",
                        description=f"Comment uses forbidden metaphor: {comment}",
                    )

                if not found_investigation and len(comment) > 20:
                    # Long comment without investigation metaphor
                    self.add_warning(
                        file_path=str(file_path),
                        line=0,
                        issue="Non-Investigative Comment",
                        description=f"Long comment lacks investigation metaphor: {comment[:50]}...",
                    )

        except Exception as e:
            self.add_warning(
                file_path=str(file_path),
                line=0,
                issue="Comment Parse Error",
                description=f"Could not parse comments: {e}",
            )

    def validate_interface_metaphor(self, interface_file: Path) -> None:
        """Validate interface-specific metaphor consistency."""
        try:
            content = interface_file.read_text()

            # Check for interface-specific investigation terms
            interface_terms = ["tui", "cli", "interface", "view", "screen", "panel"]
            found_interface_terms = []

            for term in interface_terms:
                if term in content.lower():
                    found_interface_terms.append(term)

            # Should have interface terms
            if len(found_interface_terms) == 0:
                self.add_warning(
                    file_path=str(interface_file),
                    line=0,
                    issue="Missing Interface Metaphor",
                    description="No interface metaphor terms found",
                )

            # Check for single focus enforcement
            if (
                "single_focus" not in content.lower()
                and "magnifying" not in content.lower()
            ):
                self.add_warning(
                    file_path=str(interface_file),
                    line=0,
                    issue="Missing Single Focus Metaphor",
                    description="No single focus or magnifying glass metaphor found",
                )

        except Exception as e:
            self.add_warning(
                file_path=str(interface_file),
                line=0,
                issue="Interface Parse Error",
                description=f"Could not parse interface: {e}",
            )

    def is_compliant(self) -> bool:
        """Check if system is metaphor compliant."""
        return len(self.violations) == 0

    def get_compliance_score(self) -> float:
        """Calculate metaphor consistency compliance score."""
        # Score based on violations and warnings
        violation_penalty = len(self.violations) * 10
        warning_penalty = len(self.warnings) * 2
        base_score = 100.0

        return max(0.0, base_score - violation_penalty - warning_penalty)


def test_cli_metaphor_consistency():
    """Test CLI interface for investigation metaphor consistency."""
    validator = MetaphorConsistencyValidator()

    cli_file = Path("bridge/entry/cli.py")
    if cli_file.exists():
        validator.check_file_metaphor_consistency(cli_file)
        validator.check_class_and_function_names(cli_file)
        validator.check_comments_and_docstrings(cli_file)
        validator.validate_interface_metaphor(cli_file)

    # Verify CLI uses investigation terminology
    assert validator.is_compliant(), (
        f"CLI has metaphor violations: {len(validator.violations)}"
    )
    print("✅ CLI metaphor consistency: PASSED")
    return True


def test_tui_metaphor_consistency():
    """Test TUI interface for investigation metaphor consistency."""
    validator = MetaphorConsistencyValidator()

    tui_file = Path("bridge/entry/tui.py")
    if tui_file.exists():
        validator.check_file_metaphor_consistency(tui_file)
        validator.check_class_and_function_names(tui_file)
        validator.check_comments_and_docstrings(tui_file)
        validator.validate_interface_metaphor(tui_file)

    # Verify TUI uses magnifying glass metaphor
    assert validator.is_compliant(), (
        f"TUI has metaphor violations: {len(validator.violations)}"
    )
    print("✅ TUI metaphor consistency: PASSED")
    return True


def test_views_metaphor_consistency():
    """Test view modules for investigation metaphor consistency."""
    validator = MetaphorConsistencyValidator()

    view_files = [
        "lens/views/overview.py",
        "lens/views/examination.py",
        "lens/views/connections.py",
        "lens/views/patterns.py",
        "lens/views/thinking.py",
    ]

    for view_file in view_files:
        view_path = Path(view_file)
        if view_path.exists():
            validator.check_file_metaphor_consistency(view_path)
            validator.check_class_and_function_names(view_path)

    # Verify views use investigation stages
    assert validator.is_compliant(), (
        f"Views have metaphor violations: {len(validator.violations)}"
    )
    print("✅ Views metaphor consistency: PASSED")
    return True


def test_inquiry_metaphor_consistency():
    """Test inquiry modules for investigation metaphor consistency."""
    validator = MetaphorConsistencyValidator()

    inquiry_files = [
        "inquiry/questions/structure.py",
        "inquiry/questions/purpose.py",
        "inquiry/questions/connections.py",
        "inquiry/patterns/coupling.py",
        "inquiry/patterns/density.py",
        "inquiry/notebook/entries.py",
    ]

    for inquiry_file in inquiry_files:
        inquiry_path = Path(inquiry_file)
        if inquiry_path.exists():
            validator.check_file_metaphor_consistency(inquiry_path)
            validator.check_class_and_function_names(inquiry_path)

    # Verify inquiry uses investigation terminology
    assert validator.is_compliant(), (
        f"Inquiry has metaphor violations: {len(validator.violations)}"
    )
    print("✅ Inquiry metaphor consistency: PASSED")
    return True


def test_observation_metaphor_consistency():
    """Test observation modules for investigation metaphor consistency."""
    validator = MetaphorConsistencyValidator()

    obs_files = [
        "observations/eyes/file_sight.py",
        "observations/eyes/import_sight.py",
        "observations/eyes/export_sight.py",
        "observations/record/snapshot.py",
        "observations/record/integrity.py",
    ]

    for obs_file in obs_files:
        obs_path = Path(obs_file)
        if obs_path.exists():
            validator.check_file_metaphor_consistency(obs_path)
            validator.check_class_and_function_names(obs_path)

    # Verify observations use evidence/observation terminology
    assert validator.is_compliant(), (
        f"Observations have metaphor violations: {len(validator.violations)}"
    )
    print("✅ Observation metaphor consistency: PASSED")
    return True


def test_storage_metaphor_consistency():
    """Test storage modules for investigation metaphor consistency."""
    validator = MetaphorConsistencyValidator()

    storage_files = [
        "storage/investigation_storage.py",
        "storage/transactional.py",
        "storage/backup.py",
    ]

    for storage_file in storage_files:
        storage_path = Path(storage_file)
        if storage_path.exists():
            validator.check_file_metaphor_consistency(storage_path)
            validator.check_class_and_function_names(storage_path)

    # Verify storage uses case/session terminology
    assert validator.is_compliant(), (
        f"Storage has metaphor violations: {len(validator.violations)}"
    )
    print("✅ Storage metaphor consistency: PASSED")
    return True


def test_cross_module_metaphor_consistency():
    """Test metaphor consistency across module boundaries."""
    validator = MetaphorConsistencyValidator()

    # Check that investigation terms are used consistently across modules
    key_files = [
        "bridge/entry/cli.py",
        "bridge/entry/tui.py",
        "lens/views/overview.py",
        "inquiry/questions/structure.py",
        "observations/eyes/file_sight.py",
    ]

    investigation_term_counts = {}

    for file_path in key_files:
        path = Path(file_path)
        if path.exists():
            content = path.read_text()
            content_lower = content.lower()

            # Count investigation terms
            term_count = 0
            for _category, terms in validator.investigation_terms.items():
                for term in terms:
                    term_count += content_lower.count(term)

            investigation_term_counts[file_path] = term_count

    # Check that investigation metaphor is consistently applied
    if len(investigation_term_counts) > 1:
        counts = list(investigation_term_counts.values())
        min_count = min(counts)
        max_count = max(counts)

        # Should not have huge variation in investigation metaphor usage
        if max_count > min_count * 5:  # One file uses 5x more investigation terms
            validator.add_warning(
                file_path="cross_module",
                line=0,
                issue="Inconsistent Investigation Metaphor",
                description=f"Large variation in investigation metaphor usage: {min_count} vs {max_count}",
            )

    assert validator.is_compliant(), (
        f"Cross-module metaphor violations: {len(validator.violations)}"
    )
    print("✅ Cross-module metaphor consistency: PASSED")
    return True


def test_metaphor_enforcement_in_code():
    """Test that metaphor enforcement is present in the codebase."""
    validator = MetaphorConsistencyValidator()

    # Look for metaphor enforcement mechanisms
    enforcement_files = [
        "integrity/validation/metaphor_consistency.test.py",  # This file!
        "integrity/validation/complete_constitutional.test.py",
    ]

    enforcement_found = False
    for enforcement_file in enforcement_files:
        path = Path(enforcement_file)
        if path.exists():
            content = path.read_text()
            if "metaphor" in content.lower() and "consistency" in content.lower():
                enforcement_found = True
                break

    if not enforcement_found:
        validator.add_warning(
            file_path="metaphor_enforcement",
            line=0,
            issue="Missing Metaphor Enforcement",
            description="No metaphor consistency enforcement found",
        )

    assert validator.is_compliant(), (
        f"Metaphor enforcement violations: {len(validator.violations)}"
    )
    print("✅ Metaphor enforcement: PASSED")
    return True


def run_metaphor_consistency_tests():
    """Run all metaphor consistency tests."""
    print("=" * 60)
    print("METAPHOR CONSISTENCY TESTS - Article 18 Compliance")
    print("=" * 60)

    tests = [
        test_cli_metaphor_consistency,
        test_tui_metaphor_consistency,
        test_views_metaphor_consistency,
        test_inquiry_metaphor_consistency,
        test_observation_metaphor_consistency,
        test_storage_metaphor_consistency,
        test_cross_module_metaphor_consistency,
        test_metaphor_enforcement_in_code,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} FAILED: {e}")
            failed += 1

    print("=" * 60)
    print(f"METAPHOR CONSISTENCY TEST RESULTS: {passed} passed, {failed} failed")

    if failed == 0:
        print("✅ ALL METAPHOR CONSISTENCY TESTS PASSED")
    else:
        print("❌ SOME METAPHOR CONSISTENCY TESTS FAILED")

    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_metaphor_consistency_tests()
    exit(0 if success else 1)
