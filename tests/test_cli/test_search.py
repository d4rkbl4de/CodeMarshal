"""
tests/test_cli/test_search.py - Tests for search CLI command
"""

import tempfile
from pathlib import Path

import pytest

from bridge.commands.search import SearchCommand, SearchResults


class TestSearchCommand:
    """Test search command functionality."""

    def test_simple_search(self):
        """Test basic search functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello():\n    pass\n")

            cmd = SearchCommand()
            result = cmd.execute(query="def", path=Path(tmpdir))

            assert result.success is True
            assert result.results is not None
            assert result.results.total_matches > 0

    def test_case_insensitive_search(self):
        """Test case-insensitive search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("DEF Hello():\n    pass\n")

            cmd = SearchCommand()
            result = cmd.execute(query="def", path=Path(tmpdir), case_insensitive=True)

            assert result.success is True
            assert result.results.total_matches > 0

    def test_search_with_limit(self):
        """Test search with result limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple files
            for i in range(5):
                test_file = Path(tmpdir) / f"test{i}.py"
                test_file.write_text(f"def func{i}():\n    pass\n")

            cmd = SearchCommand()
            result = cmd.execute(query="def", path=Path(tmpdir), limit=2)

            assert result.success is True
            assert result.results.total_matches <= 2

    def test_search_with_glob(self):
        """Test search with file glob."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create Python and text files
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text("def hello():\n    pass\n")
            txt_file = Path(tmpdir) / "test.txt"
            txt_file.write_text("def hello():\n    pass\n")

            cmd = SearchCommand()
            result = cmd.execute(query="def", path=Path(tmpdir), glob="*.py")

            assert result.success is True
            assert result.results.total_matches > 0

    def test_files_with_matches(self):
        """Test files-with-matches option."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello():\n    def world():\n        pass\n")

            cmd = SearchCommand()
            result = cmd.execute(
                query="def", path=Path(tmpdir), files_with_matches=True
            )

            assert result.success is True
            assert result.results.total_matches == 1  # Should be 1 file

    def test_invalid_regex(self):
        """Test search with invalid regex."""
        cmd = SearchCommand()
        result = cmd.execute(query="[invalid", path=Path("."))

        assert result.success is False
        assert result.error is not None

    def test_nonexistent_path(self):
        """Test search with nonexistent path."""
        cmd = SearchCommand()
        result = cmd.execute(query="test", path=Path("/nonexistent/path"))

        assert result.success is False

    def test_empty_query(self):
        """Test search with empty query."""
        cmd = SearchCommand()
        result = cmd.execute(query="", path=Path("."))

        assert result.success is False


class TestSearchOutputFormats:
    """Test search output formats."""

    def test_json_output(self, capsys):
        """Test JSON output format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello():\n    pass\n")

            cmd = SearchCommand()
            result = cmd.execute(query="def", path=Path(tmpdir), output_format="json")

            assert result.success is True

    def test_count_output(self, capsys):
        """Test count output format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello():\n    def world():\n        pass\n")

            cmd = SearchCommand()
            result = cmd.execute(query="def", path=Path(tmpdir), output_format="count")

            assert result.success is True


class TestSearchContext:
    """Test search context lines."""

    def test_context_lines(self):
        """Test that context lines are included."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("line1\nline2\nline3\nline4\nline5\n")

            cmd = SearchCommand(context_lines=2)
            result = cmd.execute(query="line3", path=Path(tmpdir))

            assert result.success is True
            if result.results.results:
                first_result = result.results.results[0]
                assert (
                    len(first_result.context_before) > 0
                    or len(first_result.context_after) > 0
                )
