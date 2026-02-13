"""Tests for bridge.integration.pdf_exporter."""

import pytest

from bridge.integration.pdf_exporter import PDFExporter


class _FakeHTML:
    """Simple fake WeasyPrint HTML object for tests."""

    def __init__(self, string: str):
        self.string = string

    def write_pdf(self) -> bytes:
        return b"%PDF-FAKE"


def _raise_import_error():
    raise ImportError("weasyprint missing")


def test_pdf_export_requires_optional_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        PDFExporter,
        "_load_weasyprint_html",
        staticmethod(_raise_import_error),
    )

    exporter = PDFExporter()

    with pytest.raises(RuntimeError, match=r"pip install -e \.\[export_pdf\]"):
        exporter.export({"id": "session-1"}, [])


def test_pdf_export_returns_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        PDFExporter,
        "_load_weasyprint_html",
        staticmethod(lambda: _FakeHTML),
    )

    exporter = PDFExporter()
    result = exporter.export(
        {"id": "session-2", "path": "/repo", "state": "complete"},
        [{"type": "import_sight"}],
        include_notes=False,
        include_patterns=False,
    )

    assert isinstance(result, bytes)
    assert result.startswith(b"%PDF")


def test_pdf_build_html_includes_sections_and_escapes() -> None:
    html = PDFExporter._build_html(
        {
            "id": "session-3",
            "path": "/repo",
            "state": "complete",
            "notes": ["<note>"],
            "patterns": ["pattern<&>"],
        },
        [{"type": "import_sight"}, {"type": "import_sight"}],
        include_notes=True,
        include_patterns=True,
    )

    assert "CodeMarshal Investigation Report" in html
    assert "<h2>Notes</h2>" in html
    assert "<h2>Patterns</h2>" in html
    assert "&lt;note&gt;" in html
    assert "pattern&lt;&amp;&gt;" in html
    assert "import_sight" in html


def _raise_os_error():
    raise OSError("missing gobject")


def test_pdf_export_reports_missing_native_libraries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        PDFExporter,
        "_load_weasyprint_html",
        staticmethod(_raise_os_error),
    )

    exporter = PDFExporter()

    with pytest.raises(RuntimeError, match=r"native rendering libraries"):
        exporter.export({"id": "session-4"}, [])
