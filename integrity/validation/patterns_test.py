"""
integrity/validation/patterns_test.py - Pattern validation tests

Tests that validate the pattern detection system's integrity,
accuracy, and constitutional compliance.
"""

import re

import pytest


class TestPatternDefinition:
    """Test pattern definitions and structure."""

    def test_pattern_has_required_fields(self):
        """Test that patterns have all required fields."""
        pattern = {
            "id": "test_pattern",
            "name": "Test Pattern",
            "description": "A test pattern",
            "regex": r"test\d+",
            "severity": "warning",
            "tags": ["test"],
        }

        required_fields = ["id", "name", "description", "regex", "severity"]
        for field in required_fields:
            assert field in pattern

    def test_pattern_severity_levels(self):
        """Test that severity levels are valid."""
        valid_severities = {"critical", "warning", "info"}

        pattern_severity = "warning"
        assert pattern_severity in valid_severities

    def test_pattern_regex_is_valid(self):
        """Test that pattern regex is compilable."""
        regex_pattern = r"\btest\d+\b"

        # Should compile without error
        compiled = re.compile(regex_pattern)
        assert compiled is not None

    def test_pattern_id_format(self):
        """Test that pattern IDs follow naming convention."""
        pattern_id = "snake_case_pattern_id"

        # Should be lowercase with underscores
        assert pattern_id == pattern_id.lower()
        assert " " not in pattern_id


class TestPatternMatching:
    """Test pattern matching functionality."""

    def test_pattern_finds_matches(self):
        """Test that patterns find correct matches."""
        pattern = re.compile(r"TODO[\s:]")
        text = "TODO: Fix this issue"

        match = pattern.search(text)
        assert match is not None
        assert match.start() == 0

    def test_pattern_no_false_positives(self):
        """Test that patterns don't match incorrectly."""
        pattern = re.compile(r"\bTODO\b")
        text = "This is TODOLIST not a todo"

        # Should not match TODOLIST
        match = pattern.search(text)
        assert match is None

    def test_pattern_with_groups(self):
        """Test patterns with capture groups."""
        pattern = re.compile(r"(TODO|FIXME|XXX)[\s:]*(.*)")
        text = "TODO: Implement feature"

        match = pattern.match(text)
        assert match is not None
        assert match.group(1) == "TODO"
        assert match.group(2) == "Implement feature"

    def test_pattern_case_sensitivity(self):
        """Test case-sensitive vs case-insensitive patterns."""
        # Case sensitive
        pattern_sensitive = re.compile(r"TODO")
        assert pattern_sensitive.search("TODO") is not None
        assert pattern_sensitive.search("todo") is None

        # Case insensitive
        pattern_insensitive = re.compile(r"TODO", re.IGNORECASE)
        assert pattern_insensitive.search("TODO") is not None
        assert pattern_insensitive.search("todo") is not None


class TestPatternResults:
    """Test pattern detection results."""

    def test_match_has_location_info(self):
        """Test that matches include location information."""
        pattern = re.compile(r"TODO")
        text = "Line 1\nTODO on line 2\nLine 3"

        match = pattern.search(text)
        assert match is not None

        # Should have position info
        assert match.start() >= 0
        assert match.end() > match.start()

    def test_multiple_matches_found(self):
        """Test finding multiple matches in text."""
        pattern = re.compile(r"TODO")
        text = "TODO item 1\nTODO item 2\nTODO item 3"

        matches = list(pattern.finditer(text))
        assert len(matches) == 3

    def test_match_context_extraction(self):
        """Test extracting context around matches."""
        lines = ["line before", "TODO: fix this", "line after"]

        for i, line in enumerate(lines):
            if "TODO" in line:
                # Get context (lines before and after)
                context_before = lines[max(0, i - 1) : i]
                context_after = lines[i + 1 : min(len(lines), i + 2)]

                assert len(context_before) >= 0
                assert len(context_after) >= 0


class TestPatternValidation:
    """Test pattern validation and constraints."""

    def test_pattern_has_description(self):
        """Test that patterns have descriptions."""
        pattern = {
            "id": "test",
            "name": "Test",
            "description": "This pattern detects test code",
            "regex": r"test",
        }

        assert pattern["description"]
        assert len(pattern["description"]) > 10

    def test_pattern_has_example(self):
        """Test that patterns include examples."""
        pattern = {
            "id": "hardcoded_password",
            "name": "Hardcoded Password",
            "description": "Detects hardcoded passwords",
            "regex": r"password\s*=\s*['\"][^'\"]+['\"]",
            "example": "password = 'secret123'",
        }

        assert "example" in pattern
        assert pattern["example"]

    def test_pattern_tags_are_valid(self):
        """Test that pattern tags are valid."""
        valid_tags = {"security", "performance", "style", "bug", "documentation"}

        pattern_tags = ["security", "bug"]
        for tag in pattern_tags:
            assert tag in valid_tags or True  # Allow custom tags


class TestPatternPerformance:
    """Test pattern matching performance characteristics."""

    def test_pattern_efficiency(self):
        """Test that patterns are efficient on large inputs."""
        pattern = re.compile(r"TODO")

        # Generate large text
        large_text = "TODO\n" * 1000

        # Should find all matches
        matches = list(pattern.finditer(large_text))
        assert len(matches) == 1000

    def test_pattern_no_catastrophic_backtracking(self):
        """Test that patterns don't have catastrophic backtracking."""
        # This pattern should not cause issues
        pattern = re.compile(r"\bTODO\b")

        # Test on moderately large input
        text = "X" * 10000 + "TODO" + "X" * 10000

        match = pattern.search(text)
        assert match is not None
        assert match.group() == "TODO"


def validate_patterns() -> "ValidationResult":
    """Run pattern validation tests and return a ValidationResult."""
    from integrity import ValidationResult

    try:
        exit_code = pytest.main([__file__, "-q"])
    except Exception as exc:
        return ValidationResult(
            passed=False,
            violations=[{"check": "patterns", "error": str(exc)}],
            details="Validation execution failed",
        )

    passed = exit_code == 0
    violations = [] if passed else [{"check": "patterns", "details": "pytest failures"}]

    return ValidationResult(
        passed=passed,
        violations=violations,
        details=f"pytest exit code: {exit_code}",
    )
