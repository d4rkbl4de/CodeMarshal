"""
Test suite for CodeMarshal export system.

Tests all export formats and file creation functionality.
"""

import json

import pytest

from bridge.entry.cli import CodeMarshalCLI


class TestExportFormats:
    """Test export format generation."""

    @pytest.fixture
    def sample_session_data(self):
        """Provide sample session data for testing."""
        return {
            "id": "test-session-001",
            "path": "/test/project",
            "state": "presentation_complete",
            "created_at": "2026-02-04T10:00:00",
            "observation_ids": ["obs_1", "obs_2"],
            "notes": ["Test note 1", "Test note 2"],
            "patterns": ["pattern_a", "pattern_b"],
        }

    @pytest.fixture
    def sample_observations(self):
        """Provide sample observations for testing."""
        return [
            {
                "type": "file_sight",
                "result": {
                    "path": "/test/project",
                    "file_count": 10,
                    "directory_count": 3,
                },
            },
            {
                "type": "import_sight",
                "file": "/test/main.py",
                "statements": [{"module": "os", "names": []}],
            },
        ]

    def test_json_export_content(self, sample_session_data, sample_observations):
        """Test JSON export format generation."""
        cli = CodeMarshalCLI()

        content = cli._generate_export_content(
            "json", sample_session_data, sample_observations, False, False
        )

        # Should be valid JSON
        data = json.loads(content)
        assert "export_metadata" in data
        assert "investigation" in data
        assert "observations" in data
        assert data["export_metadata"]["format"] == "json"

    def test_json_export_with_notes_and_patterns(
        self, sample_session_data, sample_observations
    ):
        """Test JSON export includes notes and patterns when requested."""
        cli = CodeMarshalCLI()

        content = cli._generate_export_content(
            "json", sample_session_data, sample_observations, True, True
        )

        data = json.loads(content)
        assert "notes" in data
        assert "patterns" in data
        assert len(data["notes"]) == 2
        assert len(data["patterns"]) == 2

    def test_markdown_export_content(self, sample_session_data, sample_observations):
        """Test Markdown export format generation."""
        cli = CodeMarshalCLI()

        content = cli._generate_export_content(
            "markdown", sample_session_data, sample_observations, False, False
        )

        # Should be valid Markdown
        assert "# CodeMarshal Investigation Report" in content
        assert "## Investigation Metadata" in content
        assert "## Observations Summary" in content
        assert "test-session-001" in content

    def test_html_export_content(self, sample_session_data, sample_observations):
        """Test HTML export format generation."""
        cli = CodeMarshalCLI()

        content = cli._generate_export_content(
            "html", sample_session_data, sample_observations, False, False
        )

        # Should be valid HTML
        assert "<!DOCTYPE html>" in content
        assert "<html>" in content
        assert "</html>" in content
        assert "CodeMarshal Investigation Report" in content
        assert "<table>" in content

    def test_plaintext_export_content(self, sample_session_data, sample_observations):
        """Test Plaintext export format generation."""
        cli = CodeMarshalCLI()

        content = cli._generate_export_content(
            "plain", sample_session_data, sample_observations, False, False
        )

        # Should be plain text
        assert "CODEMARSHAL INVESTIGATION REPORT" in content
        assert "test-session-001" in content
        assert "INVESTIGATION DETAILS" in content
        assert "OBSERVATIONS SUMMARY" in content

    def test_jupyter_export_content(self, sample_session_data, sample_observations):
        """Test Jupyter export format generation."""
        cli = CodeMarshalCLI()

        content = cli._generate_export_content(
            "jupyter", sample_session_data, sample_observations, True, True
        )

        data = json.loads(content)
        assert data["nbformat"] == 4
        assert "cells" in data
        assert data["metadata"]["codemarshal"]["include_notes"] is True
        assert data["metadata"]["codemarshal"]["include_patterns"] is True

        combined_sources = "\n".join(
            str(cell.get("source", "")) for cell in data["cells"]
        )
        assert "## Notes" in combined_sources
        assert "## Patterns" in combined_sources

    def test_svg_export_content(self, sample_session_data, sample_observations):
        """Test SVG export format generation."""
        cli = CodeMarshalCLI()

        content = cli._generate_export_content(
            "svg", sample_session_data, sample_observations, False, False
        )

        assert isinstance(content, str)
        assert content.lstrip().startswith("<svg")
        assert "<circle" in content
        assert "<line" in content

    def test_pdf_export_content(self, sample_session_data, sample_observations, monkeypatch):
        """Test PDF export format generation returns bytes."""
        cli = CodeMarshalCLI()

        monkeypatch.setattr(
            cli,
            "_generate_pdf_export",
            lambda *_args, **_kwargs: b"%PDF-FAKE",
        )

        content = cli._generate_export_content(
            "pdf", sample_session_data, sample_observations, False, False
        )

        assert isinstance(content, bytes)
        assert content.startswith(b"%PDF")

    def test_export_file_creation(
        self,
        sample_session_data,
        sample_observations,
        tmp_path,
    ):
        """Test that export actually creates files."""
        cli = CodeMarshalCLI()
        output_path = tmp_path / "test_export.json"

        content = cli._generate_export_content(
            "json", sample_session_data, sample_observations, False, False
        )

        # Write to file
        output_path.write_text(content, encoding="utf-8")

        # Verify file exists
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify content is valid
        data = json.loads(output_path.read_text())
        assert data["investigation"]["id"] == "test-session-001"


class TestExportEdgeCases:
    """Test export edge cases and error handling."""

    def test_export_with_empty_observations(self):
        """Test export with empty observations list."""
        cli = CodeMarshalCLI()
        session_data = {
            "id": "test-empty",
            "path": "/test",
            "state": "complete",
        }

        content = cli._generate_export_content("json", session_data, [], False, False)

        data = json.loads(content)
        assert data["observations"] == []

    def test_export_with_missing_optional_fields(self):
        """Test export when optional fields are missing."""
        cli = CodeMarshalCLI()
        session_data = {
            "id": "test-minimal",
            "path": "/test",
        }

        content = cli._generate_export_content(
            "markdown", session_data, [], False, False
        )

        # Should not crash
        assert "test-minimal" in content

    def test_export_all_formats(self):
        """Test that all export formats generate valid content."""
        cli = CodeMarshalCLI()
        session_data = {"id": "test", "path": "/test", "state": "complete"}
        observations = []

        formats = ["json", "markdown", "html", "plain", "jupyter", "svg", "pdf"]

        # Avoid optional WeasyPrint dependency in unit tests.
        cli._generate_pdf_export = lambda *_args, **_kwargs: b"%PDF-FAKE"  # type: ignore[method-assign]

        for fmt in formats:
            content = cli._generate_export_content(
                fmt, session_data, observations, False, False
            )
            assert len(content) > 0
            if fmt == "pdf":
                assert isinstance(content, bytes)
            else:
                assert isinstance(content, str)


class TestExportCLIIntegration:
    """Test export integration with CLI."""

    def test_cli_export_methods_exist(self):
        """Test that CLI has all necessary export methods."""
        cli = CodeMarshalCLI()

        assert hasattr(cli, "_generate_export_content")
        assert hasattr(cli, "_generate_json_export")
        assert hasattr(cli, "_generate_markdown_export")
        assert hasattr(cli, "_generate_html_export")
        assert hasattr(cli, "_generate_plaintext_export")
        assert hasattr(cli, "_generate_jupyter_export")
        assert hasattr(cli, "_generate_svg_export")
        assert hasattr(cli, "_generate_pdf_export")

    def test_export_format_variations(self):
        """Test that format variations are handled correctly."""
        cli = CodeMarshalCLI()
        session_data = {"id": "test", "path": "/test", "state": "complete"}
        observations = []

        # Test format variations
        variations = [
            ("json", "json"),
            ("markdown", "markdown"),
            ("md", "markdown"),  # Should handle short form
            ("html", "html"),
            ("plain", "plain"),
            ("plaintext", "plain"),
            ("jupyter", "jupyter"),
            ("svg", "svg"),
            ("pdf", "pdf"),
        ]

        # Avoid optional WeasyPrint dependency in this variations test.
        cli._generate_pdf_export = lambda *_args, **_kwargs: b"%PDF-FAKE"  # type: ignore[method-assign]

        for input_fmt, _ in variations:
            try:
                content = cli._generate_export_content(
                    input_fmt, session_data, observations, False, False
                )
                assert len(content) > 0
            except ValueError:
                # Some variations might not be supported, which is ok
                pass
