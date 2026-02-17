"""
tests/test_cli/test_search.py - Tests for search CLI command
"""

from pathlib import Path

from bridge.commands.search import SearchCommand


class TestSearchCommand:
    """Test search command functionality."""

    def test_simple_search(self, tmp_path: Path):
        """Test basic search functionality."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    pass\n", encoding="utf-8")

        cmd = SearchCommand()
        result = cmd.execute(query="def", path=tmp_path)

        assert result.success is True
        assert result.results is not None
        assert result.results.total_matches > 0

    def test_case_insensitive_search(self, tmp_path: Path):
        """Test case-insensitive search."""
        test_file = tmp_path / "test.py"
        test_file.write_text("DEF Hello():\n    pass\n", encoding="utf-8")

        cmd = SearchCommand()
        result = cmd.execute(query="def", path=tmp_path, case_insensitive=True)

        assert result.success is True
        assert result.results.total_matches > 0

    def test_search_with_limit(self, tmp_path: Path):
        """Test search with result limit."""
        for i in range(5):
            test_file = tmp_path / f"test{i}.py"
            test_file.write_text(f"def func{i}():\n    pass\n", encoding="utf-8")

        cmd = SearchCommand()
        result = cmd.execute(query="def", path=tmp_path, limit=2)

        assert result.success is True
        assert result.results.total_matches <= 2

    def test_search_with_glob(self, tmp_path: Path):
        """Test search with file glob."""
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    pass\n", encoding="utf-8")
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("def hello():\n    pass\n", encoding="utf-8")

        cmd = SearchCommand()
        result = cmd.execute(query="def", path=tmp_path, glob="*.py")

        assert result.success is True
        assert result.results.total_matches > 0

    def test_files_with_matches(self, tmp_path: Path):
        """Test files-with-matches option."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    def world():\n        pass\n", encoding="utf-8")

        cmd = SearchCommand()
        result = cmd.execute(query="def", path=tmp_path, files_with_matches=True)

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

    def test_json_output(self, tmp_path: Path):
        """Test JSON output format."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    pass\n", encoding="utf-8")

        cmd = SearchCommand()
        result = cmd.execute(query="def", path=tmp_path, output_format="json")

        assert result.success is True

    def test_count_output(self, tmp_path: Path):
        """Test count output format."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    def world():\n        pass\n", encoding="utf-8")

        cmd = SearchCommand()
        result = cmd.execute(query="def", path=tmp_path, output_format="count")

        assert result.success is True


class TestSearchContext:
    """Test search context lines."""

    def test_context_lines(self, tmp_path: Path):
        """Test that context lines are included."""
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3\nline4\nline5\n", encoding="utf-8")

        cmd = SearchCommand(context_lines=2)
        result = cmd.execute(query="line3", path=tmp_path)

        assert result.success is True
        if result.results.results:
            first_result = result.results.results[0]
            assert (
                len(first_result.context_before) > 0
                or len(first_result.context_after) > 0
            )

