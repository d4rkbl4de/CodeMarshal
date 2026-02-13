"""
Pattern Dashboard View

Provides a text summary of pattern scan results for CLI output.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


class PatternDashboardView:
    """Summarize pattern matches with counts and context."""

    def __init__(
        self,
        max_files: int = 5,
        max_patterns: int = 5,
        max_matches: int = 5,
        bar_width: int = 20,
    ) -> None:
        self.max_files = max_files
        self.max_patterns = max_patterns
        self.max_matches = max_matches
        self.bar_width = bar_width

    def render(self, matches: list[Any]) -> str:
        """Render a dashboard summary for pattern matches."""
        if not matches:
            return "PATTERN DASHBOARD\n" + "=" * 80 + "\nNo matches found."

        normalized = [self._normalize_match(match) for match in matches]

        severity_counts = Counter(m["severity"] for m in normalized)
        file_counts = Counter(m["file"] for m in normalized)
        pattern_counts = Counter(m["pattern_label"] for m in normalized)

        lines: list[str] = []
        lines.append("PATTERN DASHBOARD")
        lines.append("=" * 80)
        lines.append(f"Total matches: {len(normalized)}")

        lines.append("")
        lines.append("Severity distribution:")
        max_severity = max(severity_counts.values()) if severity_counts else 0
        for severity in ("critical", "warning", "info", "unknown"):
            count = severity_counts.get(severity, 0)
            if count == 0:
                continue
            bar = self._render_bar(count, max_severity)
            lines.append(f"  {severity:<8} {count:>4} {bar}")

        lines.append("")
        lines.append("Top files:")
        for file_path, count in file_counts.most_common(self.max_files):
            lines.append(f"  {count:>4} {file_path}")

        lines.append("")
        lines.append("Top patterns:")
        for pattern_label, count in pattern_counts.most_common(self.max_patterns):
            lines.append(f"  {count:>4} {pattern_label}")

        lines.append("")
        lines.append("Sample matches:")
        for match in normalized[: self.max_matches]:
            lines.extend(self._render_match(match))

        return "\n".join(lines)

    def _normalize_match(self, match: Any) -> dict[str, Any]:
        """Normalize match data from dicts or dataclasses."""
        if isinstance(match, dict):
            file_path = match.get("file") or match.get("file_path") or "unknown"
            line_number = match.get("line") or match.get("line_number")
            pattern_id = match.get("pattern_id") or "unknown"
            pattern_name = match.get("pattern_name") or pattern_id
            severity = match.get("severity") or "unknown"
            message = match.get("message") or ""
            matched = match.get("matched") or match.get("matched_text") or ""
            context_before = match.get("context_before") or []
            context_after = match.get("context_after") or []
        else:
            file_path = getattr(match, "file_path", "unknown")
            line_number = getattr(match, "line_number", None)
            pattern_id = getattr(match, "pattern_id", "unknown")
            pattern_name = getattr(match, "pattern_name", pattern_id)
            severity = getattr(match, "severity", "unknown")
            message = getattr(match, "message", "")
            matched = getattr(match, "matched_text", "")
            context_before = getattr(match, "context_before", [])
            context_after = getattr(match, "context_after", [])

        if not isinstance(file_path, str):
            file_path = str(file_path)

        return {
            "file": file_path,
            "line": line_number,
            "pattern_id": pattern_id,
            "pattern_name": pattern_name,
            "pattern_label": f"{pattern_id} ({pattern_name})",
            "severity": severity,
            "message": message,
            "matched": matched,
            "context_before": context_before,
            "context_after": context_after,
        }

    def _render_bar(self, count: int, max_count: int) -> str:
        """Render a simple proportional bar."""
        if max_count <= 0:
            return ""
        size = max(1, int((count / max_count) * self.bar_width))
        return "#" * size

    def _render_match(self, match: dict[str, Any]) -> list[str]:
        """Render a single match with context."""
        lines: list[str] = []
        severity = match["severity"].upper()
        location = (
            f"{match['file']}:{match['line']}" if match.get("line") else match["file"]
        )
        lines.append(f"- [{severity}] {location} {match['pattern_name']}")

        if match["message"]:
            lines.append(f"  {match['message']}")

        if match["context_before"]:
            for ctx in match["context_before"]:
                lines.append(f"  {ctx}")

        if match["matched"]:
            lines.append(f"  > {match['matched']}")

        if match["context_after"]:
            for ctx in match["context_after"]:
                lines.append(f"  {ctx}")

        return lines
