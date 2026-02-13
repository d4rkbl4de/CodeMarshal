"""
PDF exporter for investigation reports.
"""

from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from typing import Any


class PDFExporter:
    """Export investigation data as PDF bytes using WeasyPrint."""

    def export(
        self,
        session_data: dict[str, Any],
        observations: list[dict[str, Any]],
        include_notes: bool = False,
        include_patterns: bool = False,
    ) -> bytes:
        try:
            html_cls = self._load_weasyprint_html()
        except (ImportError, OSError) as exc:
            raise RuntimeError(
                "PDF export requires optional dependency WeasyPrint and native rendering libraries. "
                "Install with: pip install -e .[export_pdf]. "
                "If this still fails, install platform libraries (for example GTK/Pango/Cairo on Windows)."
            ) from exc

        html = self._build_html(
            session_data,
            observations,
            include_notes=include_notes,
            include_patterns=include_patterns,
        )
        return html_cls(string=html).write_pdf()

    @staticmethod
    def _load_weasyprint_html() -> Any:
        from weasyprint import HTML

        return HTML

    @staticmethod
    def _build_html(
        session_data: dict[str, Any],
        observations: list[dict[str, Any]],
        include_notes: bool,
        include_patterns: bool,
    ) -> str:
        counts: dict[str, int] = {}
        for observation in observations:
            observation_type = observation.get("type", "unknown")
            counts[observation_type] = counts.get(observation_type, 0) + 1

        rows = "\n".join(
            (
                "<tr>"
                f"<td>{escape(observation_type)}</td>"
                f"<td>{count}</td>"
                "</tr>"
            )
            for observation_type, count in sorted(counts.items())
        )

        notes_html = ""
        if include_notes:
            notes = session_data.get("notes", [])
            notes_html = "<h2>Notes</h2><ul>" + "".join(
                f"<li>{escape(str(note))}</li>" for note in notes
            ) + "</ul>"

        patterns_html = ""
        if include_patterns:
            patterns = session_data.get("patterns", [])
            patterns_html = "<h2>Patterns</h2><ul>" + "".join(
                f"<li>{escape(str(pattern))}</li>" for pattern in patterns
            ) + "</ul>"

        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>CodeMarshal PDF Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 26px; color: #202124; }}
    h1 {{ margin-bottom: 6px; }}
    .meta {{ color: #555; margin-bottom: 16px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 8px; text-align: left; }}
    th {{ background: #f6f8fa; }}
  </style>
</head>
<body>
  <h1>CodeMarshal Investigation Report</h1>
  <div class=\"meta\">Exported: {datetime.now(UTC).isoformat()}</div>
  <div><strong>ID:</strong> {escape(str(session_data.get("id", "unknown")))}</div>
  <div><strong>Path:</strong> {escape(str(session_data.get("path", "unknown")))}</div>
  <div><strong>State:</strong> {escape(str(session_data.get("state", "unknown")))}</div>
  <h2>Observation Summary</h2>
  <table>
    <thead><tr><th>Type</th><th>Count</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  {notes_html}
  {patterns_html}
</body>
</html>
"""
