"""Structured results viewer widget."""

from __future__ import annotations

import json
from typing import Any

from PySide6 import QtWidgets


class ResultsViewer(QtWidgets.QWidget):
    """Read-only viewer with helpers for text and JSON output."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._tabs = QtWidgets.QTabWidget(self)
        self._summary = QtWidgets.QPlainTextEdit(self)
        self._summary.setReadOnly(True)
        self._summary.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
        self._raw = QtWidgets.QPlainTextEdit(self)
        self._raw.setReadOnly(True)
        self._raw.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)

        self._tabs.addTab(self._summary, "Summary")
        self._tabs.addTab(self._raw, "Raw")
        layout.addWidget(self._tabs)

    def clear(self) -> None:
        self._summary.clear()
        self._raw.clear()

    def set_text(self, text: str) -> None:
        self.set_sections(text, text)

    def append_text(self, text: str) -> None:
        if self._raw.toPlainText():
            self._raw.appendPlainText(text)
        else:
            self._raw.setPlainText(text)
        if self._summary.toPlainText():
            self._summary.appendPlainText(text)
        else:
            self._summary.setPlainText(text)

    def set_json(self, payload: Any) -> None:
        raw = json.dumps(payload, indent=2, default=str)
        summary = self._summarize_payload(payload)
        self.set_sections(summary, raw)

    def set_sections(self, summary: str, raw: str) -> None:
        self._summary.setPlainText(summary)
        self._raw.setPlainText(raw)

    def show_raw(self) -> None:
        self._tabs.setCurrentWidget(self._raw)

    def _summarize_payload(self, payload: Any) -> str:
        if isinstance(payload, dict):
            lines = [f"Keys: {len(payload)}"]
            for key in sorted(payload.keys())[:15]:
                value = payload[key]
                if isinstance(value, list):
                    info = f"list[{len(value)}]"
                elif isinstance(value, dict):
                    info = f"dict[{len(value)}]"
                else:
                    info = type(value).__name__
                lines.append(f"- {key}: {info}")
            return "\n".join(lines)
        if isinstance(payload, list):
            return f"List payload with {len(payload)} item(s)."
        return "Result payload received."
