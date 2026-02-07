"""
tests/test_export/test_csv_exporter.py - Tests for CSV export format
"""

import csv
import io

import pytest

from bridge.integration.export_formats import (
    CSVExporter,
    ExportFormat,
    get_exporter,
    list_supported_formats,
)


class TestCSVExporter:
    """Test CSV exporter functionality."""

    def test_exporter_initialization(self):
        """Test CSV exporter initialization."""
        exporter = CSVExporter()
        assert exporter.format_type == ExportFormat.CSV
        assert exporter.limitations is not None

    def test_export_empty(self):
        """Test exporting with no data."""
        exporter = CSVExporter()
        csv_output = exporter.export()

        assert "CodeMarshal Investigation Export" in csv_output
        assert "Format" in csv_output
        assert "CSV" in csv_output

    def test_csv_format(self):
        """Test that output is valid CSV format."""
        exporter = CSVExporter()
        csv_output = exporter.export()

        # Try to parse as CSV
        reader = csv.reader(io.StringIO(csv_output))
        rows = list(reader)
        assert len(rows) > 0

    def test_limitations_defined(self):
        """Test that limitations are properly defined."""
        exporter = CSVExporter()
        limitations = exporter.limitations

        assert limitations.format_type == ExportFormat.CSV
        assert len(limitations.context_loss) > 0
        assert len(limitations.structure_loss) > 0
        assert len(limitations.cannot_express) > 0

    def test_get_exporter(self):
        """Test getting CSV exporter via registry."""
        exporter = get_exporter(ExportFormat.CSV)
        assert isinstance(exporter, CSVExporter)

    def test_list_formats(self):
        """Test that CSV is in supported formats."""
        formats = list_supported_formats()
        format_values = [f["format"] for f in formats]
        assert "csv" in format_values


class TestCSVStructure:
    """Test CSV structure and content."""

    def test_header_rows(self):
        """Test that header information is present."""
        exporter = CSVExporter()
        csv_output = exporter.export()

        reader = csv.reader(io.StringIO(csv_output))
        rows = list(reader)

        # Check for header
        assert any("CodeMarshal Investigation Export" in str(row) for row in rows)

    def test_sections_present(self):
        """Test that export has structured sections."""
        exporter = CSVExporter()
        csv_output = exporter.export()

        # Check for section headers
        assert "SNAPSHOT" in csv_output or "snapshot" in csv_output.lower()
        assert "Exported At" in csv_output
