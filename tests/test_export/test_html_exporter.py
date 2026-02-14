"""
tests/test_export/test_html_exporter.py - Tests for HTML export format
"""


from bridge.integration.export_formats import (
    ExportFormat,
    HTMLExporter,
    get_exporter,
    list_supported_formats,
)


class TestHTMLExporter:
    """Test HTML exporter functionality."""

    def test_exporter_initialization(self):
        """Test HTML exporter initialization."""
        exporter = HTMLExporter()
        assert exporter.format_type == ExportFormat.HTML
        assert exporter.limitations is not None

    def test_export_empty(self):
        """Test exporting with no data."""
        exporter = HTMLExporter()
        html = exporter.export()

        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "CodeMarshal Investigation Report" in html

    def test_export_structure(self):
        """Test HTML export structure."""
        exporter = HTMLExporter()
        html = exporter.export()

        # Check for required HTML elements
        assert "<head>" in html
        assert "<body>" in html
        assert "<style>" in html
        assert "</html>" in html

    def test_limitations_defined(self):
        """Test that limitations are properly defined."""
        exporter = HTMLExporter()
        limitations = exporter.limitations

        assert limitations.format_type == ExportFormat.HTML
        assert len(limitations.context_loss) > 0
        assert len(limitations.structure_loss) > 0
        assert len(limitations.cannot_express) > 0

    def test_get_exporter(self):
        """Test getting HTML exporter via registry."""
        exporter = get_exporter(ExportFormat.HTML)
        assert isinstance(exporter, HTMLExporter)

    def test_list_formats(self):
        """Test that HTML is in supported formats."""
        formats = list_supported_formats()
        format_values = [f["format"] for f in formats]
        assert "html" in format_values


class TestHTMLExporterStyling:
    """Test HTML exporter styling."""

    def test_css_styles_present(self):
        """Test that CSS styles are included."""
        exporter = HTMLExporter()
        html = exporter.export()

        # Check for common CSS properties
        assert "style" in html.lower()
        assert "font-family" in html or "font" in html
        assert "background" in html or "color" in html

    def test_responsive_meta_tag(self):
        """Test that viewport meta tag is present."""
        exporter = HTMLExporter()
        html = exporter.export()

        assert "viewport" in html.lower()
